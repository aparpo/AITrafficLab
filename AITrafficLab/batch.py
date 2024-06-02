from warnings import warn
from tqdm import tqdm

class Batch_proccessing():
    """
    Executes multiple simulations and collects statistics from each one.

    :ivar model: Model with the initial conditions used to run the simulations. 
    :vartype model: AITrafficLab.traffic_model.Traffic_model
    :ivar veh_agg: Callback function used to aggregate all the logs from every vehicle. 
    :vartype veh_agg: function
    :ivar veh_collection_agg: Callback function used to aggregate metrics across all the aggregated logs from the vehicles. 
    :vartype veh_collection_agg: function
    :ivar road_agg: Callback function used to aggregate all the logs from every road. 
    :vartype road_agg: function
    :ivar road_collection_agg: Callback function used to aggregate metrics across all the aggregated logs from the roads. 
    :vartype road_collection_agg: function
    """
    def __init__(self, model, veh_agg= lambda x: None, veh_collection_agg= lambda x: None, road_agg= lambda x: None, road_collection_agg= lambda x: None):
        """
        Creates a Batch_proccesing instance.

        :param model: Model with the initial conditions used to run the simulations. 
        :type model: AITrafficLab.traffic_model.Traffic_model
        :param veh_agg: Callback function used to aggregate all the logs from every vehicle. 
        :type veh_agg: function
        :param veh_collection_agg: Callback function used to aggregate metrics across all the aggregated logs from the vehicles. 
        :type veh_collection_agg: function
        :param road_agg: Callback function used to aggregate all the logs from every road. 
        :type road_agg: function
        :param road_collection_agg: Callback function used to aggregate metrics across all the aggregated logs from the roads. 
        :type road_collection_agg: function
    """
        self.model = model

        self.veh_agg = veh_agg
        self.veh_collection_agg = veh_collection_agg
        self.veh_global_stats = self.model.vehicle_statistics.copy()

        self.road_agg = road_agg
        self.road_collection_agg = road_collection_agg
        self.road_global_stats = self.model.road_statistics.copy()
    
    def simulate(self, simulations):
        """
        Procceses a batch of simulations, calculates statistics for every simulation and stores its values.

        :param simulations: number of simulations to run
        :type simulations: int        
        """
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
            
            stats = self.model.road_statistics.copy()
            for metric in stats:
                for road in stats[metric]:
                    stats[metric][road] = self.road_agg(stats[metric][road])
                try:
                    self.road_global_stats[metric].append(self.road_collection_agg(stats[metric].values()))
                except AttributeError:
                    self.road_global_stats[metric] = [self.road_collection_agg(stats[metric].values())]
            self.model.reset()
            
            
        

    
        