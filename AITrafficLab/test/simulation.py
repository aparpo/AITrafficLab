import siaco
import AITrafficLab.traffic_model as traffic_model
import ootraci
import generators
import agents
from statistics import mean
from connection import Sumo_connection

import networkx as nx

if __name__ == "__main__":
    G = nx.DiGraph()

    for i in range(7):
        G.add_node(i)
    G.add_edges_from([(4, 1), (1, 0), (0, 5), (2, 1), (2, 3), (3,0), (6,2)])

    place= "/Experimento"
    # place = "Las Rozas de Madrid"
    path = "./test"
    simm_conn = Sumo_connection()
    # filepath = simm_conn.import_data_from(place, path)
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission,
                    "speed" :simm_conn.vehicle_info.get_speed}
    generator = generators.Dumb_vehicle_generator(simm_conn, observables)#, siaco.Sonic_ant)
    # generator = generators.Random_vehicle_generator(simm_conn, 0.01, 5,5, observables=observables, vehicle_class = siaco.Sonic_ant)
    # generator = generators.Random_vehicle_generator(0.01, 10, observables=observables, vehicle_class = agents.Vehicle_agent)
    # edge_generator = siaco.Sonic_edge_generator(simm_conn, 0.01, 0.01, 0.01,0.01,0.01,max_length=2221.841) #max_length=165)#max_length=2221.841)
    # node_generator = siaco.Sonic_junction_generator(simm_conn, node_class=siaco.Sonic_junction)
    
    eco = traffic_model.Traffic_model(
                                 path+place,
                                #  filepath,
                                 simm_conn, 
                                #  node_generator = node_generator, 
                                #  edge_generator = edge_generator, 
                                 vehicle_generator = generator, 
                                 iters = 600,
                                 gui=True,
                                 graph=G
    )
    eco.start()
    print(eco.vehicle_statistics)
    co2_grams = 0
    time = 0
    for car in eco.vehicle_statistics["co2"]:
        co2_grams += sum(eco.vehicle_statistics["co2"][car])/1000
        time += len(eco.vehicle_statistics["speed"][car])
        print(car, sum(eco.vehicle_statistics["co2"][car])/1000)
    print("Consumo medio en gramos:", co2_grams/len(eco.vehicle_statistics["co2"]))
    print("Tiempo medio en km:", time/len(eco.vehicle_statistics["speed"]))