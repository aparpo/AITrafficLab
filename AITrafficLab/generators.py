from AITrafficLab.agents import *
from abc import ABC, abstractmethod
import random
import numpy as np

class Node_generator():
    """
    Abstract factory in charge of creating node agents for each junction in the urban network. 
    This a base node generator ment to be adapted to the users needs. However, for basic purposes
    this factory can create any kind of agent whose __init__ method is compatible with AITrafficLab.agents.Junction_agent.
    If agents different from AITrafficLab.agents.Junction_agent were to be created by this factory, its class must be 
    specified in the node_class argument.

    :ivar connection: Connection with the traffic simulator.
    :vartype connection: AITrafficLab.connection.Simulator_connection
    :ivar node_class: Node object class to be instatiated. 
    :vartype node_class: class.
    """
    def __init__(self, connection, node_class = Junction_agent):
        """
        Creates a Node_generator instance.

        :param connection: Connection with the traffic simulator.
        :type connection: AITrafficLab.connection.Simulator_connection
        :param node_class: Node object class to be instatiated. 
        :type node_class: class.
        """
        self.connection = connection
        self.node_class = node_class

    def get_classes(self):
        """
        Gets all the node classes that this node generator instantiates

        :return: List of node classes
        :rtype: list
        """
        return [self.node_class]
    
    def create_nodes(self, model):
        """
        Creates node objects of the node_class based on the information provided by the traffic model.

        :param model: Traffic model used to get information.
        :type model: AITrafficLab.traffic_model.Traffic_model
        :yields: New nodes
        """
        try:
            for node in model.graph.nodes(data=True):
                yield self.node_class(model, node[0], properties=["x","y"])
        except TypeError:
            raise(TypeError("node_class constructor not compatible with agents.Junction_agent constructor, consider adapting your node_class or creating your own custom Node_generator and overriding this method"))

class Edge_generator():
    """
    Abstract factory in charge of creating edge agents for each road in the urban network. 
    This a base edge generator ment to be adapted to the users needs. However, for basic purposes
    this factory can create any kind of agent whose __init__ method is compatible with AITrafficLab.agents.Road_agent.
    If agents different from AITrafficLab.agents.Road_agent were to be created by this factory, its class must be 
    specified in the edge_class argument.

    :ivar connection: Connection with the traffic simulator.
    :vartype connection: AITrafficLab.connection.Simulator_connection
    :ivar edge_class: Edge object class to be instatiated. 
    :vartype edge_class: class.
    :ivar edge_observables: Metrics to be tracked by each edge agent. 
    :vartype edge_observables: dict[str, function].
    """
    def __init__(self, connection,  edge_class = Road_agent, edge_observables = {}, **kwargs):
        """
        Creates an Edge_generator instance.

        :param connection: Connection with the traffic simulator.
        :type connection: AITrafficLab.connection.Simulator_connection
        :param edge_class: Edge object class to be instatiated. 
        :type edge_class: class.
        :param edge_observables: Metrics to be tracked by each edge agent. 
        :type edge_observables: dict[str, function].
        :param kwargs: Any additional keyword arguments used to create edge agents
        :type kwargs: dict
        """
        self.connection = connection
        self.edge_class = edge_class
        self.observables = edge_observables
        self.edge_kwargs = kwargs
    
    def get_classes(self):
        """
        Gets all the edge classes that this edge generator instantiates

        :return: List of edge classes
        :rtype: list
        """
        return [self.edge_class]
    
    def create_edges(self, model):
        """
        Creates edge objects of the edge_class based on the information provided by the traffic model.

        :param model: Traffic model used to get information.
        :type model: AITrafficLab.traffic_model.Traffic_model
        :yields: New edges
        """
        try:
            for edge in model.graph.edges(data=True):
                yield self.edge_class(model, 
                                    model.junctions[edge[0]], 
                                    model.junctions[edge[1]], 
                                    observables = self.observables, 
                                    properties=["length"],
                                    **self.edge_kwargs
                )
        except TypeError as te:
            print(te)
            raise(TypeError("edge_class constructor not compatible with agents.Road_agent constructor, consider adapting your edge_class or creating your own custom Edge_generator and overriding this method"))

class Vehicle_generator(ABC):
    """
    Abstract factory in charge of creating vehicle agents. 
    This a base vehicle generator ment to be adapted to the users needs. User should extend this class and
    define the vehicle creation strategy. User should also specify the vehicle class to be created. However, for basic purposes
    this factory can create any kind of agent whose __init__ method is compatible with AITrafficLab.agents.Vehicle_agent.
    If agents different from AITrafficLab.agents.Vehicle_agent were to be created by this factory, its class must be 
    specified in the vehicle_class argument.

    :ivar connection: Connection with the traffic simulator.
    :vartype connection: AITrafficLab.connection.Simulator_connection
    :ivar vehicle_class: Vehicle object class to be instatiated. 
    :vartype vehicle_class: class.
    :ivar observables: Metrics to be tracked by each vehicle agent. 
    :vartype observables: dict[str, function].
    """
    def __init__(self, connection,  vehicle_class=Vehicle_agent, observables = {}, **kwargs):
        """
        Allows the creation of instances from clases that extend this one. As an abstract class, trying to create an instance of 
        Vehicle_generator is unavailable.

        :param connection: Connection with the traffic simulator.
        :type connection: AITrafficLab.connection.Simulator_connection
        :param vehicle_class: Vehicle object class to be instatiated. 
        :type vehicle_class: class.
        :param observables: Metrics to be tracked by each vehicle agent. 
        :type observables: dict[str, function].
        :param kwargs: Any additional keyword arguments used to create vehicle agents
        :type kwargs: dict
        """
        self.connection = connection
        self.observables = observables
        self.vehicle_class = vehicle_class
        self.vehicle_kwargs = kwargs
    
    @abstractmethod
    def generate_vehicle(self, model)-> Vehicle_agent:
        """
        Creates a single vehicle.

        :param model: Traffic model to add the vehicle
        :type model: AITrafficLab.traffic_model.Traffic_model
        :return: New vehicle
        :rtype: AITrafficLab.agents.Vehicle_agent
        """
        pass

    @abstractmethod
    def generate_vehicles(self, model) -> list[Vehicle_agent]:
        """
        Creates vehicles for each iteration.

        :param model: Traffic model to add the vehicles
        :type model: AITrafficLab.traffic_model.Traffic_model
        :return: New vehicles
        :rtype: list[AITrafficLab.agents.Vehicle_agent]
        """
        pass

    @abstractmethod
    def initial_generation(self, model) -> list[Vehicle_agent]:
        """
        Creates a starting set of vehicles at the begining of the simulation.

        :param model: Traffic model to add the vehicles
        :type model: AITrafficLab.traffic_model.Traffic_model
        :return: New vehicles
        :rtype: list[AITrafficLab.agents.Vehicle_agent]
        """
        pass

    def get_classes(self):
        """
        Gets all the vehicle classes that this vehicle generator instantiates

        :return: List of vehicle classes
        :rtype: list
        """
        return [self.vehicle_class]

# class Dumb_vehicle_generator(Vehicle_generator):
#     def generate_vehicle(self,model):
#         try:
#             if random.random() < 0.9:
#                 return self.vehicle_class(model, model.roads[4, 1], model.roads[0, 5], observables=self.observables, **self.vehicle_kwargs) 
#             else:
#                 return self.vehicle_class(model, model.roads[6, 2], model.roads[0, 5], observables=self.observables, **self.vehicle_kwargs) 
#         except TypeError as te:
#             print(te)
#             raise(TypeError("vehicle_class constructor not compatible with agents.Vehicle_agent constructor, consider adapting your vehicle_class or creating your own custom Vehicle_generator and overriding this method"))

#     def generate_vehicles(self, model, *args):

#         return [self.generate_vehicle(model) for _ in range(2)]

    
#     def get_vehicle_number(self, max):
#         return 5
    
#     def initial_generation(self, model):
#         return self.generate_vehicles(model)

class Random_vehicle_generator(Vehicle_generator):
    """
    Implementation of Vehicle_generator. Creates a random number of vehicles based on Poisson distribution.
    Each vehicle is also created with random origin and destination within the edges of the network.
    """
    def __init__(self, connection, prob, max_init_car, max_iter_car, observables={}, vehicle_class=Vehicle_agent, **kwargs):
        super().__init__(connection, observables, vehicle_class, **kwargs)
        self.prob = prob
        self.max_init_car = max_init_car
        self.max_iter_car = max_iter_car

    def generate_vehicle(self, model):
        valid_route = False
        while not valid_route:
            origin = model.roads[random.choice(list(model.roads.keys()))]
            destination = model.roads[random.choice(list(model.roads.keys()))]
            valid_route = self.connection.is_valid_route(origin, destination)
        try:
            return self.vehicle_class(model, origin, destination, observables=self.observables, **self.vehicle_kwargs)
        except TypeError as te:
            print(te)
            raise(TypeError("vehicle_class constructor not compatible with agents.Vehicle_agent constructor, consider adapting your vehicle_class or creating your own custom Vehicle_generator and overriding this method"))

    
    def generate_vehicles(self, model, max = None):
        vehicles = []
        for _ in range(self.get_vehicle_number()):
            vehicles.append(self.generate_vehicle(model))
        return vehicles
    
    def get_vehicle_number(self):
        return np.random.poisson(lam=self.max_iter_car)
    
    def initial_generation(self, model):
        vehicles = []
        for _ in range(self.max_init_car):
            vehicles.append(self.generate_vehicle(model))
        return vehicles 