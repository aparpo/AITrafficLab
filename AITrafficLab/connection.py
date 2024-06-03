import traci
from abc import ABC, abstractmethod
import networkx as nx
import sumolib
from AITrafficLab import error_codes as err
import subprocess
import osmnx as ox
import os

from AITrafficLab import ootraci

class Simulator_connection(ABC):
    """
    Traffic simulator abstraction. Allows user to extend this class and adapt it to the needs of its own traffic simulator
    without the need of changing the logic defined in AITrafficLab.traffic_model.Traffic_model.

    :ivar vehicle_info: Comunication API with models and methods used to obtain information from vehicles directly from the traffic simulator.
    :ivar road_info: Comunication API with models and methods used to obtain information from roads directly from the traffic simulator.
    :ivar junction_info: Comunication API with models and methods used to obtain information from junctions directly from the traffic simulator.
    """ 
    def __init__(self, vehicle_info, road_info, junction_info):
        """
        Allows the creation of instances from clases that extend this one. As an abstract class, trying to create an instance of 
        Simulator_connection is unavailable.

        :param vehicle_info: Comunication API with models and methods used to obtain information from vehicles directly from the traffic simulator.
        :param road_info: Comunication API with models and methods used to obtain information from roads directly from the traffic simulator.
        :param junction_info: Comunication API with models and methods used to obtain information from junctions directly from the traffic simulator.
        """ 
        self.vehicle_info = vehicle_info
        self.road_info = road_info
        self.junction_info = junction_info

    @abstractmethod
    def start(self, filepath:str, gui:bool, **kwargs) -> None:
        """
        Starts a connection with the traffic simulator.

        :param filepath: Any kind of file required to start the simulator such as a config file or a networkfile
        :type filepath: str
        :param gui: Decides whether to launch the Graphic User Interface if the traffic simulator allows it.
        :type gui: bool
        :param kwargs: Any other additional keyword argument needed to start the connection
        :type kwargs: dict
        """
        pass

    @abstractmethod
    def load_information(self, filepath:str, graph:nx.DiGraph)-> tuple[nx.Graph, dict, dict]:
        """
        Reads the information stored in filepath and ensures that the network used by the simulator and the model match.

        :param filepath: Any kind of file required to start the simulator such as a config file or a networkfile
        :type filepath: str
        :param graph: Graph representation of the network if the model has already created one.
        :type graph: networkx.DiGraph
        :return: Returns the final graph with updates if needed and two dictionaries with the tranlation (in both directions)
                 of the names of the nodes and edges used by the model and the simulator. 
        :rtype: tuple[networkx.DiGraph, dict, dict]
        """
        pass

    @abstractmethod
    def simulation_step(self)-> None:
        """
        Executes a simulation step in the traffic simulator.
        """
        pass

    @abstractmethod
    def close(self)-> None:
        """
        Closes the connection with the traffic simulator
        """
        pass

    @abstractmethod
    def is_valid_route(self, origin, destination)-> bool:
        """
        Checks if a given pair of nodes are connected.

        :param origin: Starting node of the path to find.
        :type origin: AITrafficLab.agents.Junction_agent
        :param destination: Ending node of the path to find.
        :type destination: AITrafficLab.agents.Junction_agent
        :return: Indicates if both nodes are connected.
        :rtype: bool
        """
        pass

    @abstractmethod
    def get_step_time(self) -> float:
        """
        Gets the time value asociated with one time step in the simulation.

        :return: Value of the time step
        :rtype: float
        """
        pass

    @abstractmethod
    def add_vehicle(self, vehicle)-> bool:
        """
        Adds a new vehicle to the simulation.

        :param vehicle: Vehicle object with the information needed to add it to the simulation.
        :type vehicle: AITrafficLab.agents.Vehicle_agent
        :return: Success of the operation
        :rtype: bool
        """
        pass

    def is_simulation_running(self) -> bool:
        """
        Checks if the simulation is stil running.

        :return: Boolean indicating if the simulation is stil running
        :rtype: bool
        """
        return True

    def manage_exception(self, ex:Exception, context):
        """
        Manages the exceptions produced by the simulator and converts them into 
        an appropiate format to be understood by the traffic model.

        :param ex: Exception thrown
        :type ex: Exception
        :param context: Object who encountered the exception
        :type context: Object
        """
        raise ex

class Sumo_connection(Simulator_connection):
    """
    Implements the methods needed to manage a connection with the traffic simulator SUMO. Additionally to the 
    methods defined in AITrafficLab.connection.Simulator_connection, it implements the method import_data_from, 
    which allows the user to obtain urban networks, ready to be used by SUMO, from all over the world using OpenStreetMap data.
    """

    def __init__(self):
        vehicle_info = ootraci.Vehicle_info()
        road_info = ootraci.Road_info()
        junction_info = ootraci.Junction_info()
        super().__init__(vehicle_info, road_info, junction_info)
        self.exception_strategy = {
            "fatal" : err.ABORTED,
            164: err.NON_EXISTING,
            #196: err.INVALID_ROUTE,
        }
    def start(self, filepath:str, gui:bool, **kwargs) -> None:
        if gui:
            sumoCmd = ["sumo-gui", "-n", filepath+".net.xml", "--error-log", "error.log", "--message-log", "msg.log", "--device.rerouting.probability", "0"]
        else:
          sumoCmd = ["sumo", "-n", filepath+".net.xml", "--error-log", "error.log", "--message-log", "msg.log", "--device.rerouting.probability", "0"]  
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
    
    def add_vehicle(self, vehicle):
        traci.route.add("trip"+vehicle.id, [vehicle.model.nx_to_sumo[vehicle.origin.id], vehicle.model.nx_to_sumo[vehicle.destination.id]])
        traci.vehicle.add(vehicle.id, "trip"+vehicle.id)

    def is_valid_route(self, origin, destination) -> bool:
        return len(traci.simulation.findRoute(origin.sumo_id, destination.sumo_id).edges) > 0
    
    def import_data_from(self, place:str, output_path:str):
        """
        Allows the user to obtain urban networks, ready to be used by SUMO, from all over the world using OpenStreetMap data.
        It creates a new folder with the name of the place and stores all the files needed for a simulation.

        :param place: Name of the city or network to search.
        :type place: str
        :param outuput_path: Path where to store the information obtained
        :type output_path: str
        """
        filepath = "{}/{}".format(output_path, place.replace(" ", "_"))
        osm_filepath = filepath+".osm.xml"
        sumo_filepath = filepath+".net.xml"
        if not (os.path.exists(osm_filepath) and os.path.exists(sumo_filepath)):
            graph = ox.graph_from_place(place, network_type="drive")
            ox.save_graph_xml(graph, filepath= osm_filepath)
            subprocess.run(["netconvert", "--osm-files", osm_filepath, "--output-file", sumo_filepath, "--remove-edges.isolated"])
        return filepath
        