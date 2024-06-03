from AITrafficLab.traffic_model import Traffic_model
from AITrafficLab import generators
from statistics import mean
from AITrafficLab.connection import Sumo_connection

import networkx as nx

if __name__ == "__main__":

    place = "Las Rozas de Madrid"
    path = "./test/networks"
    simm_conn = Sumo_connection()
    filepath = simm_conn.import_data_from(place, path)
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission}
    generator = generators.Random_vehicle_generator(simm_conn, 0.01, 5,5, observables=observables)
    model = Traffic_model(
                                 filepath,
                                 simm_conn, 
                                 vehicle_generator = generator, 
                                 iters = 600,
                                 gui=True
    )
    model.start()
    co2_grams = 0
    time = 0
    for car in model.vehicle_statistics["co2"]:
        co2_grams += sum(model.vehicle_statistics["co2"][car])/1000
    print("Contaminación media en gramos:", co2_grams/len(model.vehicle_statistics["co2"]))