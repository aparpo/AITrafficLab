from scipy.spatial.distance import euclidean
import numpy as np
import networkx as nx
import statistics
from AITrafficLab import agents, generators
# import generators
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
            
            # added_pheromone = self.get_delay(dist_left, statistics.mean(self.speeds), self.road.max_speed, self.road.impulse)
            added_pheromone = self.get_delay(dist_left, speed, self.road.max_speed, self.road.impulse)
            self.pheromone = percieve_pheromone(leader.get_pheromone(self.road), 
                                                self.road.k, 
                                                pos, 
                                                leader_pos) 
            self.pheromone +=added_pheromone

            # try:
            #     if dist_left/(speed+0.01) <= self.model.deltaT:
            #         self.reroute()
            # except ZeroDivisionError: # if speed=0 -> agent not moving
            #     pass
        # except Exception as e:
        #     print(e)
    
    def get_delay(self, dist_left, speed, max_speed, impulse):
        cost = dist_left/(speed+0.01) - dist_left/max_speed
        cost*=impulse
        return cost
    
    def reroute(self):
        try:
            graph=self.road.dst_node.get_graph()
            nodes = nx.dijkstra_path(graph, self.road.dst_node.id, self.destination.dst_node.id, weight='time')
            if len(nodes) > 2:
                # nodes = [self.road.src_node.id] + nodes
                road_ids = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
                self.info.set_route(self,road_ids)
        except nx.exception.NetworkXNoPath: 
            pass #let the agent use its previous route
        except traci.exceptions.TraCIException as e: 
            if e.getCommand() == 196:
                try:
                    nodes = [self.road.src_node.id] + nodes
                    road_ids = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
                    self.info.set_route(self,road_ids)
                except traci.exceptions.TraCIException as e: 
                    if e.getCommand() == 196:
                        pass
        except Exception as e:
            pass
        
    
    def move(self, id):
        previous = self.road
        super().move(id)
        try:
            self.speeds = [self.speeds[-1]]
        except IndexError: # just created
            self.speeds = []
        self.road.src_node.log_change(previous, self.road)

    
    def get_pheromone(self, road):
        return self.pheromone
    
    def get_pos(self):
        return self.info.get_position(self)
    
    def on_destroy(self):
        super().on_destroy()


class Sonic_junction(agents.Junction_agent):

    def __init__(self, model, id, properties, **kwargs):
        # in_pheromones = {edge:0 for edge in in_edges}
        # out_pheromones = {edge:0 for edge in out_edges}
        super().__init__(model, id, properties, **kwargs)
        # self.travel_matrix = np.array([[0 for _ in len(out_edges)] for _ in len(in_edges)])
        
        self.graph = self.model.graph.copy()
        self.total_travels = 0
        self.travels = {}
        self.incoming_edges_pheromone = {}
        self.outcoming_edges_pheromone = {}

    def step_behaviour(self):
        if self.id == 2:
            pass
        for edge in self.outcoming_edges_pheromone:
            agent = edge.get_agent_by_pos(-1)
            # agent = edge.get_last()
            try:
                self.outcoming_edges_pheromone[edge] = percieve_pheromone(agent.get_pheromone(edge),  
                                                                edge.k, 
                                                                self.pos, 
                                                                agent.get_pos())
            except traci.exceptions.TraCIException as ex:
                 # Rare case, only 1 agent on edge and ended journey in this iter. 
                 # Only agents are allowed to delete themselves, yet node realized it first.
                 if ex.getCommand() == 164: 
                     agent = edge.dst_node
                     self.outcoming_edges_pheromone[edge] = percieve_pheromone(agent.get_pheromone(edge),  
                                                                edge.k, 
                                                                self.pos, 
                                                                agent.get_pos())
            except KeyError:
                self.outcoming_edges_pheromone[edge] = 0
        
        # try:
        #     mean_pheromone = statistics.mean(list(self.outcoming_edges_pheromone.values()))
        # except statistics.StatisticsError:
        #     mean_pheromone = 0

        for edge in self.incoming_edges_pheromone:
            self.incoming_edges_pheromone[edge] = self.compute_edge_propagation(edge)
        # pass
        for edge in self.incoming_edges_pheromone:
            agent = edge.get_first()
            try:
                agent.reroute()
            except AttributeError: #Agent was a junction who has no reroute method
                pass
    
    def get_graph(self):
        graph = self.model.graph.copy()
        out_edges_pheromone = {edge.id : {"time":self.outcoming_edges_pheromone[edge]+edge.time} for edge in self.outcoming_edges_pheromone}
        nx.set_edge_attributes(graph, out_edges_pheromone)
        return graph
    
    def get_pheromone(self, edge):
        try:
            return self.incoming_edges_pheromone[edge]
        except KeyError:
            return 0
    
    def get_pos(self):
        return self.pos
    
    def compute_edge_propagation(self, incoming):
        pheromone = 0
        for edge in self.outcoming_edges_pheromone:
            pheromone+= self.outcoming_edges_pheromone[edge]*self.travels[incoming][edge]
        try:
            pheromone /= self.total_travels
            if np.isnan(pheromone): # 0/0
                pheromone = 0 
        except ZeroDivisionError:
            pheromone = 0
        return pheromone

    def log_incoming_edge(self, incoming):
        self.incoming_edges_pheromone[incoming] = 0
        for edge in self.outcoming_edges_pheromone:
            try:
                self.travels[incoming][edge] = 0
            except KeyError:
                self.travels[incoming]= {edge: 0}

    def log_outcoming_edge(self, outcoming):
        self.outcoming_edges_pheromone[outcoming] = 0
        for edge in self.incoming_edges_pheromone:
            try:
                self.travels[edge][outcoming] = 0
            except KeyError:
                self.travels[edge] = {outcoming:0}

    def log_change(self, edge_from , edge_to):
        self.travels[edge_from][edge_to]+=1
        self.total_travels+=1

class Sonic_junction_generator(generators.Node_generator):    
    def create_nodes(self, model):
        betweenness = nx.betweenness_centrality(model.graph, normalized=True)
        for node in model.graph.nodes(data=True):
            yield self.node_class(model, node[0], properties=["x","y"], betweenness = betweenness[node[0]])
        
    
class Sonic_edge_generator(generators.Edge_generator): 

    def __init__(self, connection, k, speed_coef=0, lane_coef=0, len_coef=0, src_central_coef=0, dst_central_coef=0, edge_observables = {}, edge_class = agents.Road_agent, max_speed = 33.33, max_lanes = 4, max_length = 3000, epsilon = 0.2):
        super().__init__(connection, edge_observables, edge_class)
        self.speed_coef = speed_coef
        self.lane_coef = lane_coef
        self.len_coef = len_coef
        self.src_central_coef = src_central_coef
        self.dst_central_coef = dst_central_coef
        self.max_speed = max_speed
        self.max_lanes = max_lanes
        self.max_length = max_length
        self.epsilon = epsilon
        self.k = k

    def create_edges(self, model):
            for edge in model.graph.edges(data=True):
                src = model.junctions[edge[0]]
                dst = model.junctions[edge[1]]
                road = self.edge_class(model, 
                                    src, 
                                    dst, 
                                    observables = self.observables, 
                                    properties=["length"])
                src.log_outcoming_edge(road)
                # src.x, src.y = traci.junction.getPosition(traci.edge.getFromJunction(road.sumo_id))
                dst.log_incoming_edge(road)
                # dst.x, dst.y = traci.junction.getPosition(traci.edge.getToJunction(road.sumo_id))
                k = self.speed_coef*road.max_speed/self.max_speed+\
                    self.lane_coef*road.lanes/self.max_lanes+\
                    self.len_coef*road.length/self.max_length+\
                    self.src_central_coef*src.betweenness+\
                    self.dst_central_coef*dst.betweenness
                k/=5
                if k<0:
                    k=0
                k=0.05
                impulse = self.epsilon*np.exp(k*road.max_speed*2)
                road.set_property("k",k)
                road.set_property("impulse", impulse)
                yield road


            

    


        



