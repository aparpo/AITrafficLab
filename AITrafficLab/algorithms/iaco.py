from AITrafficLab import agents
from scipy.spatial.distance import euclidean
import networkx as nx
import traci


class Inverted_ant(agents.Vehicle_agent):
    def __init__(self, model, origin, destination, deposit_rate, observables = {}):
        super().__init__(model, origin, destination, observables = observables, pheromone=0, deposit_rate=deposit_rate)
    
    def step_behaviour(self):
        pos = self.info.get_position(self)
        next_node_pos = self.road.dst_node.pos
        dist_left = euclidean(pos, next_node_pos)

        speed = self.info.get_speed(self)

        self.pheromone = dist_left/(speed+0.01)

        if dist_left/(speed+0.01) < 2: #less than 1 step to get to a node
            self.reroute()

        self.road.pheromone += self.pheromone*self.deposit_rate
    
    def reroute(self):
        try:
            nodes = nx.dijkstra_path(self.model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight='time')
            if len(nodes) > 1:
                nodes = [self.road.src_node.id] + nodes
                road_ids = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
                self.info.set_route(self,road_ids)
        except nx.exception.NetworkXNoPath: 
            pass #let the agent use its previous route
        except traci.exceptions.TraCIException as e: 
            if e.getCommand() == 196:
                pass #let the agent use its previous route
    
    def on_destroy(self):
            return super().on_destroy()

class Inverted_road(agents.Road_agent):
    def __init__(self, model, src_node, dst_node, properties, observables={}, pheromone=0, evaporation_rate=0):
        super().__init__(model, src_node=src_node, dst_node=dst_node, observables=observables, properties=properties, pheromone=pheromone, evaporation_rate=evaporation_rate)
    
    def step_behaviour(self):
        self.pheromone *= self.evaporation_rate
        pheromone_update = {self.id : {"time":self.pheromone+self.time}}
        nx.set_edge_attributes(self.model.graph, pheromone_update)

        

