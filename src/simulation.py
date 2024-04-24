import siaco
import ecosystem
import ootraci
import generators
import agents
from statistics import mean
from connection import Sumo_connection
if __name__ == "__main__":
    place= "Torrejon de Ardoz"
    path = "./test"
    simm_conn = Sumo_connection()
    filepath = simm_conn.import_data_from(place, path)
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission,
                    "speed" :simm_conn.vehicle_info.get_speed}
    generator = generators.Random_vehicle_generator(simm_conn, 0.01, 100, observables=observables, vehicle_class = siaco.Sonic_ant)
    # generator = generators.Random_vehicle_generator(0.01, 10, observables=observables, vehicle_class = agents.Vehicle_agent)
    edge_generator = siaco.Sonic_edge_generator(simm_conn)
    node_generator = generators.Node_generator(simm_conn, node_class=siaco.Sonic_junction)
    eco = ecosystem.Ecosystem(filepath,
                                 simm_conn, 
                                 node_generator = node_generator, 
                                 edge_generator = edge_generator, 
                                 vehicle_generator=generator, 
                                 iters = 300)
    eco.start()
    print(eco.vehicle_statistics)
    co2_grams = 0
    distance = 0
    for car in eco.vehicle_statistics["co2"]:
        co2_grams += sum(eco.vehicle_statistics["co2"][car])/1000
        distance += sum(eco.vehicle_statistics["speed"][car])/1000
        print(car, sum(eco.vehicle_statistics["co2"][car])/1000)
    print("Consumo medio en gramos:", co2_grams/len(eco.vehicle_statistics["co2"]))
    print("Distancia medio en km:", distance/len(eco.vehicle_statistics["speed"]))