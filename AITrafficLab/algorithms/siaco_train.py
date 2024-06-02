import optuna
import generators
import siaco
import agents
import AITrafficLab.traffic_model as traffic_model
import mlflow
from batch import Batch_proccessing
from statistics import mean
import warnings
import networkx as nx
import random
warnings.filterwarnings("ignore")

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
# Suprimir todas las advertencias
warnings.filterwarnings("ignore")

def callback(study, trial):
    """Función que se ejecutará en la función "objetive" para guardar el mejor modelo
    entrenado hasta el momento.
    """
    if study.best_trial.number == trial.number:
        study.set_user_attr(key="best_model", value=trial.user_attrs["best_model"])


def objective(trial, simm_conn, filepath, graph, observables, iters, sims):
    """Función que entrena y evalua "un intento" de un modelo de red neuronal"""       
    # Construimos el modelo
    generator = Custom_vehicle_generator(simm_conn, observables, siaco.Sonic_ant) 
    # generator = generators.Random_vehicle_generator(0.01, 10, observables=observables, vehicle_class = agents.Vehicle_agent)
    # speed_coef, lane_coef, len_coef, src_central_coef, dst_central_coef
    # params = {
    #     "speed":trial.suggest_float("speed", -0.2,1),
    #     "lanes":trial.suggest_float("lanes", -0.2,1),
    #     "length":trial.suggest_float("length", -0.2,1),
    #     "src_centrality":trial.suggest_float("src_centrality", -0.2,1),
    #     "dst_centrality":trial.suggest_float("dst_centrality", -0.2,1),
    #     "epsilon":trial.suggest_float("epsilon",0,1)
    # }
    params = {"k":trial.suggest_float("k",0,1),
              "epsilon":trial.suggest_float("epsilon",0,1)}
    
    edge_generator = siaco.Sonic_edge_generator(simm_conn,
                                                params["k"],
                                                0,# params["speed"],
                                                0,# params["lanes"],
                                                0,# params["length"],
                                                0,# params["src_centrality"],
                                                0,# params["dst_centrality"],
                                                max_length=150,
                                                epsilon=params["epsilon"])
    node_generator = siaco.Sonic_junction_generator(simm_conn, node_class=siaco.Sonic_junction)
    eco = traffic_model.Traffic_model(filepath,
                                 simm_conn, 
                                 node_generator = node_generator, 
                                 edge_generator = edge_generator, 
                                 vehicle_generator=generator, 
                                 iters = iters,
                                 graph = graph)
    
    batch = Batch_proccessing(eco, sum, mean)
    batch.simulate(sims);  
    
    # Guardamos el modelo creado
    trial.set_user_attr(key="best_model", value=params)
    
    # Evaluamos
    media = mean(batch.veh_global_stats["time"])
    with mlflow.start_run(): 
        mlflow.log_params(params)
        mlflow.log_metric("mean", media)
    return media

from connection import Sumo_connection
mlflow.set_tracking_uri(uri="http://localhost:8080/")
mlflow.set_experiment("SIACO4_cuadricula")

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
path = "./test"
simm_conn = Sumo_connection()
filepath = path+place
observables = {}
trial = []
study = optuna.create_study(direction="minimize", study_name="SIACO")
# study = optuna.load_study(study_name="MLP Tensorflow")
func = lambda trial: objective(trial=trial, graph = G, simm_conn=simm_conn, filepath=filepath, observables=observables, iters=1000, sims=5)

study.optimize(func, n_trials=1000, callbacks=[callback])

