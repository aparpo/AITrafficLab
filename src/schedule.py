import mesa
import agents

class GraphOrderedActivation(mesa.time.BaseScheduler):
    def __init__(self, model, node_classes, edge_classes):
        super().__init__(model)
        self.node_classes = node_classes
        self.edge_classes = edge_classes
        self.agent_types = dict()
    

    def add(self, agent):
        super().add(agent)
        try:
            self.agent_types[type(agent)].append(agent)
        except KeyError:
            self.agent_types[type(agent)] = [agent]
    
    def remove(self, agent):
        super().remove(agent)
        self.agent_types[type(agent)].remove(agent)

    def get_agent_count(self, type=None):
        try:
            return len(self.agent_types[type]) 
        except KeyError:
            if type==None: # Return the total of agents
                return sum(len(agent_list for agent_list in self.agent_types.values))
    
    def step(self):
        for node_type in self.node_classes:
            for node in self.agent_types[node_type]:
                node.step()
        
        for edge_type in self.edge_classes:
            for edge in self.agent_types[edge_type]:
                edge.step()
                for agent in self.model.grid.iter_cell_list_contents([edge.id]):
                    try:
                        if agent in self.agent_types[type(agent)]: # Agent is scheduled
                            agent.step()
                    except KeyError: # Agent type unknown 
                        pass
    
    def sort_agents(self, type, order, reverse = False):
        if type(order)==function:
            self.agent_types[type].sort(key=order, reverse = reverse)
        elif type(order)==dict:
            key = lambda x, order=order: order[x]
            self.agent_types[type].sort(key = key, reverse = reverse) 