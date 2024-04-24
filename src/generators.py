from agents import *
from abc import ABC, abstractmethod
import random
import traci

class Node_generator():
    def __init__(self, connection, node_class = Junction_agent):
        self.connection = connection
        self.node_class = node_class
    
    def get_classes(self):
        return [self.node_class]
    
    def create_nodes(self, model):
        try:
            for node in model.graph.nodes(data=True):
                yield self.node_class(model, node[0], properties=["x","y"])
        except TypeError:
            raise(TypeError("node_class constructor not compatible with agents.Junction_agent constructor, consider adapting your node_class or creating your own custom Node_generator and overriding this method"))

class Edge_generator():
    def __init__(self, connection, edge_observables = {}, edge_class = Road_agent):
        self.connection = connection
        self.edge_class = edge_class
        self.observables = edge_observables
    
    def get_classes(self):
        return [self.edge_class]
    
    def create_edges(self, model):
        try:
            for edge in model.graph.edges(data=True):
                yield self.edge_class(model, 
                                    model.junctions[edge[0]], 
                                    model.junctions[edge[1]], 
                                    observables = self.observables, 
                                    properties=["length"]
                )
        except TypeError as te:
            print(te)
            raise(TypeError("edge_class constructor not compatible with agents.Road_agent constructor, consider adapting your edge_class or creating your own custom Edge_generator and overriding this method"))

class Vehicle_generator(ABC):
    def __init__(self, connection, observables = {}, vehicle_class=Vehicle_agent):
        self.connection = connection
        self.observables = observables
        self.vehicle_class = vehicle_class
    
    @abstractmethod
    def generate_vehicle(self, model):
        pass

    @abstractmethod
    def generate_vehicles(self, model):
        pass

    def get_classes(self):
        return [self.vehicle_class]

class Dumb_vehicle_generator(Vehicle_generator):
    def generate_vehicle(self,model):
        try:
            return self.vehicle_class(model, model.roads[1,6], model.roads[0,1], observables=self.observables) 
        except TypeError as te:
            print(te)
            raise(TypeError("vehicle_class constructor not compatible with agents.Vehicle_agent constructor, consider adapting your vehicle_class or creating your own custom Vehicle_generator and overriding this method"))

    def generate_vehicles(self, model, *args):
        return [self.generate_vehicle(model) for _ in range(1)]
    
    def get_vehicle_number(self, max):
        return 5

class Random_vehicle_generator(Vehicle_generator):
    def __init__(self, connection, prob, max_car, observables={}, vehicle_class=Vehicle_agent):
        super().__init__(connection, observables, vehicle_class)
        self.prob = prob
        self.max_car = max_car

    def generate_vehicle(self, model):
        valid_route = False
        while not valid_route:
            origin = model.roads[random.choice(list(model.roads.keys()))]
            destination = model.roads[random.choice(list(model.roads.keys()))]
            valid_route = self.connection.is_valid_route(origin, destination)
        try:
            return self.vehicle_class(model, origin, destination, observables=self.observables)
        except TypeError as te:
            print(te)
            raise(TypeError("vehicle_class constructor not compatible with agents.Vehicle_agent constructor, consider adapting your vehicle_class or creating your own custom Vehicle_generator and overriding this method"))

    
    def generate_vehicles(self, model, max = None):
        vehicles = []
        for _ in range(self.get_vehicle_number(max)):
            vehicles.append(self.generate_vehicle(model))
        return vehicles
    
    def get_vehicle_number(self, max):
        number = 0
        for _ in range(self.max_car):
            if self.prob > random.random(): 
                number+=1
        return number