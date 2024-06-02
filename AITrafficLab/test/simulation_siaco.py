# 283
import siaco
import AITrafficLab.traffic_model as traffic_model
import ootraci
import generators
import agents
from statistics import mean
from connection import Sumo_connection
import random

import networkx as nx

class Dijkstra_vehicle(agents.Vehicle_agent):
    def __init__(self, model, origin, destination,  type="Car", id = None, observables = {}):
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

class Custom_vehicle_generator(generators.Vehicle_generator):
    def generate_vehicle(self,model):
        if random.random() < 0.5:
            return self.vehicle_class(model, model.roads[-3, 10], model.roads[14, -4], observables=self.observables) 
        else:
            return self.vehicle_class(model, model.roads[-1, 0], model.roads[24, -2], observables=self.observables) 
    
    def generate_vehicles(self, model, *args):
        return [self.generate_vehicle(model) for _ in range(self.get_vehicle_number())]
    
    def get_vehicle_number(self):
        if random.random() < 0.5:
            return 1
        return 0
    
    def initial_generation(self, model):
        return self.generate_vehicles(model)

class Random_vehicle_generator(generators.Vehicle_generator):
    def generate_vehicle(self, model):
        valid_route = False
        while not valid_route:
            origin = model.roads[random.choice(list(model.roads.keys()))]
            destination = model.roads[random.choice(list(model.roads.keys()))]
            valid_route = self.connection.is_valid_route(origin, destination)
        return self.vehicle_class(model, origin, destination, observables=self.observables, **self.vehicle_kwargs)
    
    def generate_vehicles(self, model, amount=None,*args):
        if amount:
            return [self.generate_vehicle(model) for _ in range(amount)]
        return [self.generate_vehicle(model) for _ in range(self.get_vehicle_number())]
    
    def get_vehicle_number(self):
        return 0
    
    def initial_generation(self, model):
        return self.generate_vehicles(model,50)

if __name__ == "__main__":
    intelligent = True
    real = False

    path = "./test"
    simm_conn = Sumo_connection()
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission}
    
    if real:
        place = "Segovia"
        filepath = simm_conn.import_data_from(place, path)
        generator = generators.Random_vehicle_generator(simm_conn, 0.01, 5,5, observables=observables, vehicle_class = siaco.Sonic_ant) 
        edge_generator = siaco.Sonic_edge_generator(simm_conn, 
                                                    k= 0.2,
                                                    speed_coef=-0.366202,
                                                    lane_coef=-0.678529, 
                                                    len_coef=-0.645993,
                                                    src_central_coef=-0.909025,
                                                    dst_central_coef=0.108010,
                                                    epsilon=0.2,
                                                    max_length=2221.841)
        node_generator = siaco.Sonic_junction_generator(simm_conn, node_class=siaco.Sonic_junction)
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

        place= "/Cuadricula"
        filepath = path+place
    


    if not intelligent:
        generator = Custom_vehicle_generator(simm_conn, observables, Dijkstra_vehicle)
        if real:
            generator = generators.Random_vehicle_generator(simm_conn, 0.01, 5,5, observables=observables, vehicle_class = Dijkstra_vehicle)
        edge_generator = None
        node_generator = None
    elif not real:
        generator = Custom_vehicle_generator(simm_conn, observables, siaco.Sonic_ant) 
        edge_generator = siaco.Sonic_edge_generator(simm_conn, 
                                                    k = 0.2,
                                                    speed_coef=-0.604840,#-0.677082,
                                                    lane_coef=-0.529011, #0.519594, 
                                                    len_coef=0.113197, #0.449026,
                                                    src_central_coef=-0.360841, #-0.540998,
                                                    dst_central_coef=-0.994093, #-0.335713,
                                                    epsilon=0.2, #0.585110,
                                                    max_length=85) #max_length=165)#max_length=2221.841)

        # edge_generator = siaco.Sonic_edge_generator(simm_conn, 
        #                                             0.1,
        #                                             0.1, 
        #                                             0.1,
        #                                             0.1,
        #                                             0.1,
        #                                             max_length=85) #max_length=165)#max_length=2221.841)
        node_generator = siaco.Sonic_junction_generator(simm_conn, node_class=siaco.Sonic_junction)
    
    eco = traffic_model.Traffic_model(
                                 filepath,
                                 simm_conn, 
                                 node_generator = node_generator, 
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
        #print(car, sum(eco.vehicle_statistics["co2"][car])/1000)
    #print("Consumo medio en gramos:", co2_grams/len(eco.vehicle_statistics["co2"]))
    print("Tiempo medio en s:", time/len(eco.vehicle_statistics["time"]))