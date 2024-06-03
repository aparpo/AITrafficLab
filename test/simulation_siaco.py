# 283
from AITrafficLab.algorithms import siaco
from AITrafficLab.traffic_model import Traffic_model
from AITrafficLab import generators
from AITrafficLab import agents
from statistics import mean
from AITrafficLab.connection import Sumo_connection
import random

import networkx as nx

INTELLIGENT = True

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

if __name__ == "__main__":

    path = "./test/networks"
    simm_conn = Sumo_connection()
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission}
    
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
    


    if not INTELLIGENT:
        generator = Custom_vehicle_generator(simm_conn,  agents.Dijkstra_vehicle, observables)
        edge_generator = None
        node_generator = None
    else:
        generator = Custom_vehicle_generator(simm_conn,  siaco.Sonic_ant, observables) 
        edge_generator = siaco.Sonic_edge_generator(simm_conn, 
                                                    k = 0.2,
                                                    speed_coef=-0.604840,
                                                    lane_coef=-0.529011,  
                                                    len_coef=0.113197, 
                                                    src_central_coef=-0.360841,
                                                    dst_central_coef=-0.994093,
                                                    epsilon=0.2,
                                                    max_length=85)
        node_generator = siaco.Sonic_junction_generator(simm_conn, node_class=siaco.Sonic_junction)
    
    model = Traffic_model(
                                 filepath,
                                 simm_conn, 
                                 node_generator = node_generator, 
                                 edge_generator = edge_generator, 
                                 vehicle_generator = generator, 
                                 iters = 1000,
                                 gui=True,
                                 graph=G
    )
    model.start()
    co2_grams = 0
    time = 0
    for car in model.vehicle_statistics["time"]:
        time += sum(model.vehicle_statistics["time"][car])
    print("Tiempo medio en s:", time/len(model.vehicle_statistics["time"]))