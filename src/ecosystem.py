import mesa
import networkx as nx
import osmnx as ox
import random
import traci
import sumolib
import time
import matplotlib.pyplot as plt
import subprocess

from agents import *
from generators import *
from schedule import GraphOrderedActivation
import error_codes as err

# def import_data_from(place:str, output_path:str):
#     graph = ox.graph_from_place(place, network_type="drive")
#     filepath = "{}/{}".format(output_path, place.replace(" ", "_"))
#     osm_filepath = filepath+".osm.xml"
#     sumo_filepath = filepath+".net.xml"
#     ox.save_graph_xml(graph, filepath= osm_filepath)
#     subprocess.run(["netconvert", "--osm-files", osm_filepath, "--output-file", sumo_filepath, "--remove-edges.isolated"])
#     return filepath



class Ecosystem(mesa.Model):
    def __init__(self,graph_file, connection, node_generator=None, edge_generator=None, vehicle_generator=None, iters=None, gui = False):
        super().__init__()
        self.connection = connection
        self.iters = iters
        if iters<=0 or iters is None:
            self.start = self._start_eternal
        else:
            self.start = self._start_iters
        # sumoCmd = ["sumo-gui", "-n", graph_file+".net.xml", "--error-log", "error.log", "--message-log", "msg.log"]
        # traci.start(sumoCmd)
        self.connection.start(graph_file, gui)
        # self.deltaT = traci.simulation.getDeltaT()
        self.deltaT = self.connection.get_step_time()
        print("DeltaT: {}".format(self.deltaT))

        graph = nx.DiGraph(ox.graph_from_xml(graph_file+'.osm.xml'))
        # pos = nx.spring_layout(self.graph)
        # nx.draw_networkx_nodes(self.graph, pos)
        # nx.draw_networkx_edges(self.graph, pos, arrows=True)
        # plt.show()

        # print(self.graph.edges(data=True))
        # print(self.graph.nodes(data=True))
        
        # self.sumonet = sumolib.net.readNet(graph_file+'.net.xml')
        # self.sumo_to_nx = {edge._id: (int(edge._from._id), int(edge._to._id)) for edge in self.sumonet.getEdges()}
        # self.nx_to_sumo = {(int(edge._from._id), int(edge._to._id)): edge._id for edge in self.sumonet.getEdges()}
        # self.graph.remove_edges_from(list(set(self.graph.edges)-set(self.nx_to_sumo.keys()))) # Asegurar que ambas topologías coinciden
        self.graph, self.sumo_to_nx, self.nx_to_sumo = self.connection.load_information(graph_file, graph)
        self.line_graph = nx.line_graph(self.graph)

        
        if not node_generator:
            node_generator = Node_generator(self.connection)
        if not edge_generator:
            edge_generator = Edge_generator(self.connection)
        if not vehicle_generator:
            vehicle_generator = Dumb_vehicle_generator(self.connection)

        self.grid = mesa.space.NetworkGrid(self.line_graph)
        self.schedule = GraphOrderedActivation(self, node_generator.get_classes(), edge_generator.get_classes())

        self.junctions = dict()
        for node in node_generator.create_nodes(self):
            self.junctions[node.id]=node
            self.add_agent(node, place=False)

        self.roads = dict()
        for edge in edge_generator.create_edges(self):
            self.roads[edge.id]=edge
            self.add_agent(edge, place=False)
        self.road_statistics = {stat:dict() for stat in edge_generator.observables}

        print("nx-to-sumo", self.nx_to_sumo)
        print("roads", self.roads)

        self.vehicle_generator = vehicle_generator
        self.vehicle_statistics = {stat:dict() for stat in self.vehicle_generator.observables}
        # print(self.statistics)

        vehicle = vehicle_generator.generate_vehicle(self)
        self.add_agent(vehicle, vehicle.road.id)
        for vehicle in self.vehicle_generator.generate_vehicles(self, 10):
            self.add_agent(vehicle, vehicle.road.id)

        self.to_destroy = []
    
    def step(self):
        print("Siguiente iteración")
        # Generadores de vehiculos
        for vehicle in self.vehicle_generator.generate_vehicles(self, 10):
            self.add_agent(vehicle, vehicle.road.id)
        self.schedule.step()
        # traci.simulationStep()
        self.connection.simulation_step()
        self._purge()
    
    def _start_eternal(self):
        # while traci.simulation.getMinExpectedNumber() > 0:
        while self.connection.is_simulation_running():
            self.step()
        self._destroy()
        self.connection.close()
    
    def _start_iters(self):
        try:
            for _ in range(self.iters):
                self.step()
        except Exception as e:
            self.connection.manage_exception(e, self)
        self._destroy()
        self.connection.close()
    
    def _purge(self):
        for deleted_agent in self.to_destroy:
            try:
                deleted_agent.on_destroy()
                self.grid.remove_agent(deleted_agent)
                self.schedule.remove(deleted_agent)
                self.to_destroy.remove(deleted_agent)
            except KeyError:
                pass
    
    def _destroy(self):
        for agent in self.schedule.agents:
            self.to_destroy.append(agent)
        self._purge()
    
    def add_agent(self, agent, place=None):
        # print([self.model.nx_to_sumo[self.origin.id], self.model.nx_to_sumo[self.destination.id]])
        # traci.route.add("trip"+self.id, [self.model.nx_to_sumo[self.origin.id], self.model.nx_to_sumo[self.destination.id]])
        # traci.vehicle.add(self.id, "trip"+self.id)
        if isinstance(agent, Vehicle_agent):
            self.connection.add_vehicle(agent.id, self.nx_to_sumo[agent.origin.id], self.nx_to_sumo[agent.destination.id])
        self.schedule.add(agent)
        if place:
            self.grid.place_agent(agent,place)
        
