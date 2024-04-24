from ecosystem import Ecosystem
from warnings import warn
from tqdm import tqdm

class Batch_proccessing():
    def __init__(self, model, veh_agg, veh_collection_agg):
        self.model = model
        self.veh_agg = veh_agg
        self.veh_collection_agg = veh_collection_agg

        self.veh_global_stats = self.model.vehicle_statistics.copy()
        self.veh_global_stats = self.model.vehicle_statistics.copy()
    
    def simulate(self, simulations):
        for _ in tqdm(range(simulations), desc = "Running simulations"):
            self.model.start()
            stats = self.model.vehicle_statistics.copy()
            for metric in stats:
                for car in stats[metric]:
                    stats[metric][car] = self.veh_agg(stats[metric][car])
                try:
                    self.veh_global_stats[metric].append(self.veh_collection_agg(stats[metric].values()))
                except AttributeError:
                    self.veh_global_stats[metric] = [self.veh_collection_agg(stats[metric].values())]
            self.model.reset()
            
            
        

    
        