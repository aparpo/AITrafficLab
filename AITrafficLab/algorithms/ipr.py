from AITrafficLab import agents
from scipy.spatial.distance import euclidean
import networkx as nx
import traci
from itertools import islice
import random

CONGESTION_THRESHOLD = 0.7
K = 50
EPSILON = 0.0001
ALPHA = 0.5
BETA = 0.5
VEHICLE_LENGTH = 5
VEHICLE_GAP = 2.5

class Inverted_ant(agents.Vehicle_agent):
    def __init__(self, model, origin, destination, deposit_rate, observables = {}):
        super().__init__(model, origin, destination, observables = observables, pheromone=0, deposit_rate=deposit_rate)
        self.route = []
        self.reroute()
    
    def step_behaviour(self):
        pos = self.info.get_position(self)
        next_node_pos = self.road.dst_node.pos
        dist_left = euclidean(pos, next_node_pos)

        speed = self.info.get_speed(self)

        self.pheromone = self.road.length/(speed+0.01)

        if dist_left/(speed+EPSILON) < 2: #less than 1 step to get to a node
            self.reroute()

        self.road.pheromone += self.pheromone*self.deposit_rate
    
    def reroute(self):
        try:
            if len(self.route)<=2 or self.model.roads[self.route[0], self.route[1]].get_congestion()>CONGESTION_THRESHOLD:
                allowed_routes = list(
                    islice(nx.shortest_simple_paths(self.model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight="time"), K)
                )
                try:
                    allowed_edges = list(set([self.model.roads[(nodes[0], nodes[1])] for nodes in allowed_routes]))
                except IndexError: #less than 2 nodes to choose from (can't form an edge)
                    allowed_edges = []
                if len(allowed_edges) > 1:
                    likelyhoods = [1/(edge.pheromone+EPSILON)**ALPHA *1/edge.length**BETA for edge in allowed_edges]
                    total = sum(likelyhoods)
                    probabilities = [likelyhood/total for likelyhood in likelyhoods]
                    selected_edge = random.choices(allowed_edges, weights=probabilities, k=1)[0]

                    for route in allowed_routes:
                        if (route[0], route[1]) == selected_edge.id:
                            final_route = route
                            break            

                    if len(final_route) > 1:
                        self.route = final_route
                        final_route = [self.road.src_node.id] + final_route
                        final_route = [(final_route[i], final_route[i+1]) for i in range(len(final_route)-1)]
                        self.info.set_route(self,final_route)
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
    
    def get_congestion(self):
        return len(self.get_vehicles())*(VEHICLE_LENGTH+VEHICLE_GAP)/(self.length*self.lanes)

        

