from ecosystem import Ecosystem
from warnings import warn
from tqdm import tqdm

class Batch_proccessing():
    def __init__(self, model, vehicle_agg={}, veh_collection_agg={}, road_agg={}, road_collection_agg={}):
        self.model = model

        if not set(vehicle_agg).issubset(model.vehicle_statistics):
            warn("Some individual vehicle metric aggregation methods are unclear. Following metrics will be ignored:")
            warn([metric for metric in vehicle_agg if metric not in model.vehicle_statistics])
        if not set(veh_collection_agg).issubset(model.vehicle_statistics):
            warn("Some metric aggregation methods across vehicles are unclear. Following metrics will be ignored:")
            warn([metric for metric in veh_collection_agg if metric not in model.vehicle_statistics])
        
        self.vehicle_info = {
            "agent_func": {},
            "collection_func": {},
            "run_data": model.vehicle_statistics,
            "run_stats" : {},
            "global_stats": []
        }
        
        if not set(road_agg).issubset(model.road_statistics):
            warn("Some individual road metric aggregation methods are unclear. Following metrics will be ignored:")
            warn([metric for metric in road_agg if metric not in model.road_statistics])
        if not set(road_collection_agg).issubset(model.road_statistics):
            warn("Some metric aggregation methods across roads are unclear. Following metrics will be ignored:")
            warn([metric for metric in veh_collection_agg if metric not in model.road_statistics])
        
        self.road_info = {
            "agent_func": {},
            "collection_func": {},
            "run_stats" : {},
            "global_stats": []
        }
    
    def simulate(self, simulations):
        for _ in tqdm(range(simulations), desc = "Running simulations"):
            self.model.start()
            veh_progress = tqdm(self.vehicle_statistics, desc="Calculating vehicle stats", leave = False)
            for metric in veh_progress:
                try:
                    for agent in self.model.vehicle_statistics[metric]:
                        agent_agg_metric = self.vehicle_agg[metric](agent)
                        self.vehicle_statistics[metric].append(agent_agg_metric)

                except TypeError: # Several aggregation functions defined for this metric
                    for func in self.vehicle_agg[metric]:
                        for agent in self.model.vehicle_statistics[metric]:
                            agent_agg_metric = self.vehicle_agg[metric][func](agent)
                            try:
                                self.vehicle_statistics["{}_{}".format(func, metric)].append(agent_agg_metric)
                            except KeyError:
                                self.vehicle_statistics["{}_{}".format(func, metric)] = [agent_agg_metric]
    
    def format_single_funcs(self, metrics, info, type):
        if callable(metrics):
            info["agent_func"] = {metric: {metrics.__name__:metrics} for metric in info["run_data"]}
        else:
            for metric in metrics:
                if callable(metrics[metric]):
                    info["agent_func"][metric] = {metrics[metric].__name__: metrics[metric]}
                if isinstance(metrics[metric], dict):
                    info["agent_func"][metric] = {
                        metrics[metric][func].__name__: metrics[metric][func] for func in metrics[metric]
                    }
    
    def format_collection_funcs(self, metrics, info):
        for metric in metrics:
            if callable(metrics[metric]):
                info["collection_func"][metric] = {metrics[metric].__name__: metrics[metric]}
            if isinstance(metrics[metric], dict):
                for func in metrics[metric]:
                    info["collection_func"] = {
                        "{}_{}".format(metric,metrics[metric][func].__name__): metrics[metric][func]
                    }


    def _aggregate_agent_single(self, agent, metric_name, func, info): 
        info["run_stats"][metric_name].append(func(agent))
    
    def _aggregate_agent_multi(self, agent, metric_name, info):
        for func in info["agent_func"][metric_name]:
            try:
                self._aggregate_agent_single(agent, metric_name, func, info)
            except KeyError: # Compound metric not yet initialized
                info["run_stats"]["{}_{}".format(func, metric_name)] = []
                self._aggregate_agent_single(agent, metric_name, func, info)
    
    def aggregate_collection(self, metric_name, info):
        try:
            for agent in self.model.vehicle_statistics[metric_name]:
                self._aggregate_agent_single(agent, metric_name, info)
        except TypeError: # Several aggregation functions defined for this metric
            for agent in self.model.vehicle_statistics[metric_name]:
                self._aggregate_agent_multi(agent, metric_name, info)
    

            
                
            


