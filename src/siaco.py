from scipy.spatial.distance import euclidean
import numpy as np
import networkx as nx
import statistics
import agents
import generators
import traci
def percieve_pheromone(incoming, k, pos, leader_pos):
    dist = euclidean(pos, leader_pos)
    return incoming*np.exp(-k*dist)


class Sonic_ant(agents.Vehicle_agent):

    def __init__(self, model, origin, destination, pheromone=0, type="Sonic_ant", id = None, observables = {}):
        super().__init__(model, origin, destination,  type, id, observables)
        self.pheromone = pheromone
        self.percieve_strategy = {
            Sonic_ant:lambda leader: leader.pheromone,
            Sonic_junction: lambda node: node.get_pheromone(self.road)
        }
        self.vision_strategy = {
            Sonic_ant:lambda leader: self.info.get_position(leader),
            Sonic_junction: lambda node: node.pos
        }
        self.speeds = []
    
    def step_behaviour(self):
        # try:
            leader = self.road.get_leader(self)
            leader_pos = leader.get_pos()
            # try:
            #     leader_pos = self.info.get_position(leader)
            # except AttributeError: # Leader is a junction
            #     leader_pos = leader.pos 
            pos = self.info.get_position(self)
            next_node_pos = self.road.dst_node.pos
            dist_left = euclidean(pos, next_node_pos)
            speed = self.info.get_speed(self)
            self.speeds.append(speed)
            
            added_pheromone = self.get_delay(dist_left, statistics.mean(self.speeds), self.road.max_speed, self.road.impulse)
            self.pheromone = percieve_pheromone(leader.get_pheromone(self.road), 
                                                self.road.k, 
                                                pos, 
                                                leader_pos) 
            self.pheromone +=added_pheromone

            try:
                if dist_left/speed < self.model.deltaT:
                    self.reroute()
            except ZeroDivisionError: # if speed=0 -> agent not moving
                pass
        # except Exception as e:
        #     print(e)
    
    def get_delay(self, dist_left, speed, max_speed, impulse):
        cost = dist_left/(speed+0.01) - dist_left/max_speed
        cost*=impulse
        return cost
    
    def reroute(self):
        graph=self.road.dst_node.get_graph()
        nodes = nx.dijkstra_path(graph, self.road.dst_node, self.destination.src_node, weight='time')
        nodes = [self.road.src_node.id] + nodes
        road_ids = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        self.info.set_route(road_ids)
    
    def move(self, id):
        super().move(id)
        try:
            self.speeds = [self.speeds[-1]]
        except IndexError: # just created
            self.speeds = []
    
    def get_pheromone(self, road):
        return self.pheromone
    
    def get_pos(self):
        return self.info.get_position(self)


class Sonic_junction(agents.Junction_agent):

    def __init__(self, model, id, properties, **kwargs):
        # in_pheromones = {edge:0 for edge in in_edges}
        # out_pheromones = {edge:0 for edge in out_edges}
        super().__init__(model, id, properties, **kwargs)
        # self.travel_matrix = np.array([[0 for _ in len(out_edges)] for _ in len(in_edges)])
        
        self.graph = self.model.graph.copy()
        self.pos = (self.x, self.y)
        self.in_pheromones = {}
        self.out_pheromones = {}

    def step_behaviour(self):
        for edge in self.out_pheromones:
            agent = edge.get_pos(-1)
            try:
                self.out_pheromones[edge] = percieve_pheromone(agent.get_pheromone(edge),  
                                                                edge.k, 
                                                                self.pos, 
                                                                agent.get_pos())
            except traci.exceptions.TraCIException as ex:
                 # Rare case, only 1 agent on edge and ended journey in this iter. 
                 # Only agents are allowed to delete themselves, yet node realized it first.
                 if ex.getCommand() == 164: 
                     agent = edge.dst_node
                     self.out_pheromones[edge] = percieve_pheromone(agent.get_pheromone(edge),  
                                                                edge.k, 
                                                                self.pos, 
                                                                agent.get_pos())
        try:
            mean_pheromone = statistics.mean(list(self.out_pheromones.values()))
        except statistics.StatisticsError:
            mean_pheromone = 0
        for edge in self.in_pheromones:
            self.in_pheromones[edge] = mean_pheromone
            #TODO probar con media ponderada por viajes.
    
    def get_graph(self):
        out_edges_pheromone = {edge.id : {"time":self.out_pheromones[edge]+edge.time} for edge in self.out_pheromones}
        nx.set_edge_attributes(self.graph, out_edges_pheromone)
        return self.graph
    
    def get_pheromone(self, edge):
        return self.in_pheromones[edge]
    
    def get_pos(self):
        return self.pos
    
class Sonic_edge_generator(generators.Edge_generator): 
    epsilon = 0.01   
    def create_edges(self, model):
            for edge in model.graph.edges(data=True):
                road = self.edge_class(model, 
                                    model.junctions[edge[0]], 
                                    model.junctions[edge[1]], 
                                    observables = self.observables, 
                                    properties=["length"])
                model.junctions[edge[1]].in_pheromones[road]=0
                model.junctions[edge[0]].out_pheromones[road]=0
                k = 1
                impulse = self.epsilon*np.exp(k*road.max_speed*2)
                road.set_property("k",k)
                road.set_property("impulse", impulse)
                yield road


            

    


        



