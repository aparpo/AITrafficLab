import mesa
import networkx as nx
import osmnx as ox
import random
import traci
import sumolib
import time
import matplotlib.pyplot as plt
import subprocess
from tqdm import tqdm


from agents import *
from generators import *
from schedule import GraphOrderedScheduler
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
    def __init__(self,graph_file, connection, node_generator=None, edge_generator=None, vehicle_generator=None, iters=None, gui = False, graph=None):
        super().__init__()
        self.graph_file = graph_file
        self.connection = connection
        self.gui = gui
        self.iters = iters
        if  iters is None or iters<=0:
            self.start_strategy = self._start_eternal
        else:
            self.start_strategy = self._start_iters
        # self.connection.start(graph_file, gui)
        # self.deltaT = self.connection.get_step_time()
        if graph:
            self.graph = graph
        else:
            self.graph = nx.DiGraph(ox.graph_from_xml(graph_file+'.osm.xml'))
        
        # self.graph, self.sumo_to_nx, self.nx_to_sumo = self.connection.load_information(graph_file, self.graph)
        # self.line_graph = nx.line_graph(self.graph)

        
        if not node_generator:
            node_generator = Node_generator(self.connection)
        self.node_generator = node_generator
        if not edge_generator:
            edge_generator = Edge_generator(self.connection)
        self.edge_generator = edge_generator
        if not vehicle_generator:
            vehicle_generator = Dumb_vehicle_generator(self.connection)
        self.vehicle_generator = vehicle_generator

        # self.grid = mesa.space.NetworkGrid(self.line_graph)
        # self.schedule = GraphOrderedActivation(self, node_generator.get_classes(), edge_generator.get_classes())

        self.junctions = dict()
        self.roads = dict()
        
        self.reset()

        self.to_destroy = []

        self._initialize()
        
    
    def _initialize(self):
        self.connection.start(self.graph_file, False)
        
        self.deltaT = self.connection.get_step_time()            
        self.graph, self.sumo_to_nx, self.nx_to_sumo = self.connection.load_information(self.graph_file, self.graph)
        self.line_graph = nx.line_graph(self.graph)

        self.grid = mesa.space.NetworkGrid(self.line_graph)
        self.schedule = GraphOrderedScheduler(self, self.node_generator.get_classes(), self.edge_generator.get_classes())

        for node in self.node_generator.create_nodes(self):
            self.junctions[node.id]=node
            self.add_agent(node, place=False)
        
        for edge in self.edge_generator.create_edges(self):
            self.roads[edge.id]=edge
            self.add_agent(edge, place=False)
        
        self.connection.close()

    def start(self):
        self.connection.start(self.graph_file, self.gui)
        vehicle = self.vehicle_generator.generate_vehicle(self)
        self.add_agent(vehicle, vehicle.road.id)
        for vehicle in self.vehicle_generator.initial_generation(self):
            self.add_agent(vehicle, vehicle.road.id)
        self.start_strategy()
    
    def reset(self):
        self.road_statistics = {stat:dict() for stat in self.edge_generator.observables}
        self.vehicle_statistics = {stat:dict() for stat in self.vehicle_generator.observables}

    def step(self):
        # print("Siguiente iteración")
        # Generadores de vehiculos
        for vehicle in self.vehicle_generator.generate_vehicles(self, 10):
            self.add_agent(vehicle, vehicle.road.id)
        self.schedule.step()
        # traci.simulationStep()
        self.connection.simulation_step()
        self._purge()
    
    def _start_eternal(self):
        while self.connection.is_simulation_running():
            self.step()
        self._destroy()
        self.connection.close()
    
    def _start_iters(self):
        try:
            for _ in tqdm(range(self.iters), desc = "Current simulation progress"):
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
        vehicles = [
            vehicle for vehicle in self.schedule.agents if
                any(isinstance(vehicle, _class) for _class in self.vehicle_generator.get_classes())
        ]
        for agent in [vehicle for vehicle in vehicles]:
            self.to_destroy.append(agent)
        self._purge()
    
    def add_agent(self, agent, place=None):
        if isinstance(agent, Vehicle_agent):
            self.connection.add_vehicle(agent.id, self.nx_to_sumo[agent.origin.id], self.nx_to_sumo[agent.destination.id])
        self.schedule.add(agent)
        if place:
            self.grid.place_agent(agent,place)
        
