#255.0809498111171
import iaco
import ipr
import AITrafficLab.traffic_model as traffic_model
import ootraci
import generators
import agents
from statistics import mean
from connection import Sumo_connection
import random
from itertools import islice

import networkx as nx

class Dijkstra_vehicle(agents.Vehicle_agent):
    def __init__(self, model, origin, destination,  type="Car", id = None, observables = {}, **kwargs):
        super().__init__(model, origin, destination,  type=type, id = id, observables = observables)
        nodes = nx.dijkstra_path(model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight='time')
        nodes = [self.road.src_node.id] + nodes
        self.route = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        self.started = False
    def step_behaviour(self):
        try:
            if not self.started:
                self.info.set_route(self,self.route)
                self.started = True
        except:
            pass
    
    def on_destroy(self):
        super().on_destroy()

class Yen_vehicle(agents.Vehicle_agent):
    def __init__(self, model, origin, destination,  type="Car", id = None, observables = {}):
        super().__init__(model, origin, destination,  type=type, id = id, observables = observables)
        rand = random.randint(0,50)
        nodes = list(
            islice(nx.shortest_simple_paths(model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight="time"), 51)
        )[rand]
        nodes = [self.road.src_node.id] + nodes
        self.route = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        self.started = False
    def step_behaviour(self):
        try:
            if not self.started:
                self.info.set_route(self,self.route)
                self.started = True
        except:
            pass
    
    def on_destroy(self):
        super().on_destroy()

class Custom_vehicle_generator(generators.Vehicle_generator):
    def generate_vehicle(self,model):
        # valid_route = False
        # while not valid_route:
        #     origin = model.roads[random.choice(list(model.roads.keys()))]
        #     destination = model.roads[random.choice(list(model.roads.keys()))]
        #     valid_route = self.connection.is_valid_route(origin, destination)
        # return self.vehicle_class(model, origin, destination, observables=self.observables, **self.vehicle_kwargs)
        if random.random() < 0.5:
            return self.vehicle_class(model, model.roads[-3, 10], model.roads[14, -4], observables=self.observables, **self.vehicle_kwargs) 
        else:
            return self.vehicle_class(model, model.roads[-1, 0], model.roads[24, -2], observables=self.observables, **self.vehicle_kwargs) 
    
    def generate_vehicles(self, model, *args):
        return [self.generate_vehicle(model) for _ in range(self.get_vehicle_number())]
    
    def get_vehicle_number(self):
        if random.random() < 0.5:
            return 1
        return 0
    
    def initial_generation(self, model):
        return self.generate_vehicles(model)

if __name__ == "__main__":

    intelligent = True
    real = False
    
    simm_conn = Sumo_connection()
    path = "./test"
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission}#,
                    # "speed" :simm_conn.vehicle_info.get_speed}

    if real:
        place = "Las Rozas de Madrid"
        filepath = simm_conn.import_data_from(place, path)
        generator = generators.Random_vehicle_generator(simm_conn, 0.01, 5,5, observables=observables, vehicle_class = ipr.Inverted_ant, deposit_rate = 0.5) 
        edge_generator = generators.Edge_generator(simm_conn, edge_class = ipr.Inverted_road, evaporation_rate=0.5)
        G = None
    else:
        # Crear un grafo de cuadrícula de tamaño 5x5
        rows, cols = 5, 5
        G = nx.grid_2d_graph(rows, cols)

        # Renombrar los nodos para que no sean tuplas
        mapping = { (i, j): i * cols + j for i, j in G.nodes() }
        G = nx.relabel_nodes(G, mapping)
        G.add_nodes_from([-1,-2,-3,-4])
        G.add_edges_from([(-1,0),(24,-2), (-3,10),(10,-3),(14,-4),(-4,14)])
        G = nx.DiGraph(G)

        filepath = path+"/Cuadricula"
    
    if not intelligent:
        generator = Custom_vehicle_generator(simm_conn, observables, Yen_vehicle)
        edge_generator = None
        node_generator = None
    elif not real:
        generator = Custom_vehicle_generator(simm_conn, observables, ipr.Inverted_ant, deposit_rate = 0.5) 
        edge_generator = generators.Edge_generator(simm_conn, edge_class = ipr.Inverted_road, evaporation_rate=0.5)
        node_generator = None
    
    eco = traffic_model.Traffic_model(
                                 filepath,
                                 simm_conn, 
                                 node_generator = None, 
                                 edge_generator = edge_generator, 
                                 vehicle_generator = generator, 
                                 iters = 1000,
                                 gui=True,
                                 graph=G
    )
    eco.start()
    # print(eco.vehicle_statistics)
    co2_grams = 0
    time = 0
    for car in eco.vehicle_statistics["time"]:
        #co2_grams += sum(eco.vehicle_statistics["co2"][car])/1000
        time += sum(eco.vehicle_statistics["time"][car])
        # print(car, sum(eco.vehicle_statistics["co2"][car])/1000)
    #print("Consumo medio en gramos:", co2_grams/len(eco.vehicle_statistics["co2"]))
    print("Tiempo medio en s:", time/len(eco.vehicle_statistics["time"]))