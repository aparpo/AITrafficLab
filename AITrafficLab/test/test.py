from AITrafficLab.traffic_model import *
from generators import *
from connection import Sumo_connection
from statistics import mean
from batch import Batch_proccessing
import matplotlib.pyplot as plt

if __name__ == "__main__":
    place= "Las Rozas de Madrid"
    path = "./test"
    simm_conn = Sumo_connection()
    filepath = simm_conn.import_data_from(place, path)
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission,
                    "distance" :simm_conn.vehicle_info.get_accumulated_distance}
    generator = Random_vehicle_generator(simm_conn,0.01, 5,5, observables=observables)
    eco = Traffic_model(filepath, simm_conn, vehicle_generator=generator, iters = 30, gui=True)
    eco.start()

    batch = Batch_proccessing(eco, mean, mean)
    batch.simulate(30)

    plt.hist(batch.veh_global_stats["co2"])
    plt.show()
    


    # eco.start()
    # print(eco.vehicle_statistics)
    # co2_grams = 0
    # dist = 0
    # for car in eco.vehicle_statistics["co2"]:
    #     co2_grams += sum(eco.vehicle_statistics["co2"][car])/1000
    #     dist += eco.vehicle_statistics["distance"][car][-1]
    #     print(car, sum(eco.vehicle_statistics["co2"][car])/1000)
    # print("Consumo medio en gramos:", co2_grams/len(eco.vehicle_statistics["co2"]))
    # print("Distancia media:", dist/len(eco.vehicle_statistics["distance"]))


def add(x,y):
    return x+y

    