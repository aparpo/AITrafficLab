from AITrafficLab.traffic_model import Traffic_model
from AITrafficLab.generators import Random_vehicle_generator
from AITrafficLab.connection import Sumo_connection
from statistics import mean
from AITrafficLab.batch import Batch_proccessing
import matplotlib.pyplot as plt

if __name__ == "__main__":
    place= "Las Rozas de Madrid"
    path = "./test/networks"
    simm_conn = Sumo_connection()
    filepath = simm_conn.import_data_from(place, path)
    observables = { "co2":simm_conn.vehicle_info.get_co2_emission}
    generator = Random_vehicle_generator(simm_conn,0.01, 5,5, observables=observables)
    model = Traffic_model(filepath, simm_conn, vehicle_generator=generator, iters = 30, gui=False)
    model.start()

    batch = Batch_proccessing(model, mean, mean)
    batch.simulate(30)

    plt.hist(batch.veh_global_stats["co2"])
    plt.show()


    