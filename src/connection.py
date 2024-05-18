import traci
from abc import ABC, abstractmethod
import networkx as nx
import sumolib
import error_codes as err
import subprocess
import osmnx as ox
import os

import ootraci

class Simulator_connection(ABC):
    def __init__(self, vehicle_info, road_info, junction_info):
        self.vehicle_info = vehicle_info
        self.road_info = road_info
        self.junction_info = junction_info

    @abstractmethod
    def start(self, filepath:str, gui:bool, **kwargs) -> None:
        pass

    @abstractmethod
    def load_information(self, filepath:str, graph:nx.Graph)-> tuple[nx.Graph, dict, dict]:
        pass

    @abstractmethod
    def simulation_step(self)-> None:
        pass

    @abstractmethod
    def close(self)-> None:
        pass

    @abstractmethod
    def is_valid_route(self, origin, destination)-> bool:
        pass

    @abstractmethod
    def get_step_time(self) -> float:
        pass

    @abstractmethod
    def add_vehicle(self, origin, destination, **kwargs)-> bool:
        pass

    def is_simulation_running(self) -> bool:
        return True

    def manage_exception(self, ex:Exception, context):
        raise ex

class Sumo_connection(Simulator_connection):

    def __init__(self):
        vehicle_info = ootraci.Vehicle_info()
        road_info = ootraci.Road_info()
        junction_info = ootraci.Junction_info()
        super().__init__(vehicle_info, road_info, junction_info)
        self.exception_strategy = {
            "fatal" : err.ABORTED,
            164: err.NON_EXISTING,
        }
    def start(self, filepath:str, gui:bool, **kwargs) -> None:
        if gui:
            sumoCmd = ["sumo-gui", "-n", filepath+".net.xml", "--error-log", "error.log", "--message-log", "msg.log"]
        else:
          sumoCmd = ["sumo", "-n", filepath+".net.xml", "--error-log", "error.log", "--message-log", "msg.log"]  
        traci.start(sumoCmd)
    
    def get_step_time(self) -> float:
        return traci.simulation.getDeltaT()
    
    def load_information(self, filepath:str, graph:nx.Graph):
        sumonet = sumolib.net.readNet(filepath+'.net.xml')
        sumo_to_nx = {edge._id: (int(edge._from._id), int(edge._to._id)) for edge in sumonet.getEdges()}
        nx_to_sumo = {(int(edge._from._id), int(edge._to._id)): edge._id for edge in sumonet.getEdges()}
        graph.remove_edges_from(list(set(graph.edges)-set(nx_to_sumo.keys()))) # Asegurar que ambas topologías coinciden
        return graph, sumo_to_nx, nx_to_sumo
    
    def simulation_step(self)-> None:
        traci.simulationStep()

    def is_simulation_running(self) -> bool:
        return traci.simulation.getMinExpectedNumber() > 0
    
    def close(self)-> None:
        traci.close()

    def manage_exception(self, ex:Exception, context) -> tuple[int, Exception]:
        try:
            raise ex
        except traci.exceptions.FatalTraCIError:
            return self.exception_strategy["fatal"], ex
        except traci.exceptions.TraCIException:
            return self.exception_strategy[ex.getCommand()], ex  
    
    def add_vehicle(self, id, origin, destination, **kwargs) -> bool:
        # print([self.model.nx_to_sumo[self.origin.id], self.model.nx_to_sumo[self.destination.id]])
        traci.route.add("trip"+id, [origin, destination])
        traci.vehicle.add(id, "trip"+id)

    def is_valid_route(self, origin, destination) -> bool:
        return len(traci.simulation.findRoute(origin.sumo_id, destination.sumo_id).edges) > 0
    
    def import_data_from(self, place:str, output_path:str):
        filepath = "{}/{}".format(output_path, place.replace(" ", "_"))
        osm_filepath = filepath+".osm.xml"
        sumo_filepath = filepath+".net.xml"
        if not (os.path.exists(osm_filepath) and os.path.exists(sumo_filepath)):
            graph = ox.graph_from_place(place, network_type="drive")
            ox.save_graph_xml(graph, filepath= osm_filepath)
            subprocess.run(["netconvert", "--osm-files", osm_filepath, "--output-file", sumo_filepath, "--remove-edges.isolated"])
        return filepath
        