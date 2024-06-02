import mesa

class GraphOrderedScheduler(mesa.time.BaseScheduler):
    """
    A scheduler specially designed for graphs. Activates agents in the following order:
        1. Node agents
        2. Edge agents
            3. Vehicle agents in each edge
    
    :ivar node_classes: List of node classes present in the model.
    :vartype node_clases: list[class]
    :ivar edge_classes: List of edge classes present in the model.
    :vartype edge_clases: list[class]
    :ivar agent_types: Dictionary containing diferent collection of agents.
    :vartype agent_types: dict[class,list[Mesa.agent]]
    """
    def __init__(self, model, node_classes, edge_classes):
        """
        Creates a GraphOrderedScheduler instance.

        :param node_classes: List of node classes present in the model.
        :type node_clases: list[class]
        :param edge_classes: List of edge classes present in the model.
        :type edge_clases: list[class]
        :param agent_types: Dictionary containing diferent collection of agents.
        :type agent_types: dict[class,list[Mesa.agent]]
        """
        super().__init__(model)
        self.node_classes = node_classes
        self.edge_classes = edge_classes
        self.agent_types = dict()

    def add(self, agent):
        """
        Adds a new agent to be activated each iteration.

        :param agent: Agent to be added.
        :type agent: Mesa.Agent
        """
        super().add(agent)
        try:
            self.agent_types[type(agent)].append(agent)
        except KeyError:
            self.agent_types[type(agent)] = [agent]
    
    def remove(self, agent):
        """
        Removes an agent from the schedule so that it is never activated again.

        :param agent: agent to be removed
        :type agent: Mesa.Agent
        """
        super().remove(agent)
        self.agent_types[type(agent)].remove(agent)

    def get_agent_count(self, type=None):
        """
        Gets de number of agents o a certain type. If no type is specified, returns the total number of agents.

        :param type: class of agents to be counted
        :type type: class
        :return: Number of agents of a certain class
        :rtype: int
        """
        try:
            return len(self.agent_types[type]) 
        except KeyError:
            if type==None: # Return the total of agents
                return sum(len(agent_list for agent_list in self.agent_types.values))
    
    def step(self):
        """
        Activates the agents behaviour by calling their step method each iteration in the following order:
            1. Node agents
            2. Edge agents
                3. Agents in each edge
        """
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
        self.time+=1
    
    def sort_agents(self, type, order, reverse = False):
        """
        Reorders the activation of agents of the same class.

        :param type: Class of agents to be sorted
        :type type: class
        :param order: Defines the new order for the agents
        :type order: dict or function
        :param reverse: reverts the order specified by the parameter order
        :type reverse: bool
        """
        if type(order)==function:
            self.agent_types[type].sort(key=order, reverse = reverse)
        elif type(order)==dict:
            key = lambda x, order=order: order[x]
            self.agent_types[type].sort(key = key, reverse = reverse) 