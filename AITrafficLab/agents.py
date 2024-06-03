import mesa
from AITrafficLab  import error_codes as err
import networkx as nx
import random
from itertools import islice

class Junction_agent(mesa.Agent):
    """
    Default agent to model junctions or nodes in the network. 
    User may add any attribute to the constructor so that other agents can retrieve its value without the need of extending this class.
    A step_behaviour method is available to override in order to add an intelligent behaviour to the junction agent.

    :ivar model: Instance of the traffic model it belongs to.
    :vartype model: AITrafficLab.traffic_model.Traffic_model
    :ivar id: Junction ID used by the traffic model.
    :vartype id: int
    :ivar info: Allows user to retrieve information regarding the junction directly from the traffic simulator.
    :vartype info: AITrafficLab.ootraci.Junction_info
    :ivar pos: Position of the node in the network.
    :vartype pos: tuple[float,float]
    """
    def __init__(self, model, id, properties:list, **kwargs):
        """
        Creates a Junction_agent instance.

        :param model: Instance of the traffic model it belongs to.
        :type model: AITrafficLab.traffic_model.Traffic_model
        :param id: Junction ID used by the traffic model.
        :type id: int
        :param properties: List of the names of the attributes present on the network graph to be added to the object.
                           Every entry on the list will create a new attribute with its name.
                           If the network doesn't have a value for the specified property and node ID, the value will be filled with None
        :type properties: list[str]
        :param kwargs: Aditional attributes with their values to be added to the object
        :type kwargs: dict
        """ 
        super().__init__(id, model)
        self.id = id
        self.info = self.model.connection.junction_info

        for property in properties:
            try:
                self.__dict__[property] = self.model.graph.nodes[id][property]
            except KeyError: # Property not found in network node
                self.set_property(property, None)
        
        if not self.x or not self.y:
            self.x, self.y = self.info.get_pos(self)
        
        self.pos = (self.x, self.y)
        
        for kwarg in kwargs:
            self.set_property(kwarg, kwargs[kwarg])

    def set_property(self,property, value):
        """
        Creates or updates the value of an attribute on the object and on the model's network.

        :param property: Name of the property.
        :type property: str
        :param value: Value of the property.
        :type value: Object
        """ 
        self.__dict__[property] = value
        self.model.graph.nodes[self.id][property] = value # Create it in graph
        
    def step(self):
        """
        Execute the logic of the junction agent. 
        """ 
        self.step_behaviour()
    
    def step_behaviour(self):
        """
        Method prepared to be overriden with the junction's logic for every iteration. 
        """ 
        pass
    
    def on_destroy(self):
        """
        Method prepared to be overriden with the junction's logic before being deleted. 
        """
        pass

class Road_agent(mesa.Agent):
    """
    Default agent to model roads or edgess in the network. 
    User may add any attribute to the constructor so that other agents can retrieve its value without the need of extending this class.
    A step_behaviour method is available to override in order to add an intelligent behaviour to the road agent.

    :ivar model: Instance of the traffic model it belongs to.
    :vartype model: AITrafficLab.traffic_model.Traffic_model
    :ivar id: Road ID used by the traffic model. It's made up of the source and destiny nodes ID.
    :vartype id: tuple[int,int]
    :ivar info: Allows user to retrieve information regarding the road directly from the traffic simulator.
    :vartype info: AITrafficLab.ootraci.Road_info
    :ivar src_node: Source node of the road or edge.
    :vartype src_node: AITrafficLab.agents.Junction_agent
    :ivar dst_node: Destination node of the road or edge.
    :vartype dst_node: AITrafficLab.agents.Junction_agent
    :ivar observables: List of callback functions for the metrics to be collect in each iterations.
                       Each function must recieve exactly one argument: the agent itself
    :vartype observables: list[function]
    :ivar length: Length of the road in m.
    :vartype length: float
    :ivar max_speed: Max speed allowed in the road in m/s.
    :vartype max_speed: float
    :ivar time: Minimun time required to travel along the road in s.
    :vartype length: float
    :ivar lanes: Nomber of lanes in the road.
    :vartype length: int
    """
    def __init__(self, model, src_node:Junction_agent, dst_node: Junction_agent, observables:dict, properties: list, **kwargs):
        """
        Creates a Road_agent instance.

        :param model: Instance of the traffic model it belongs to.
        :type model: AITrafficLab.traffic_model.Traffic_model
        :param id: Road ID used by the traffic model. It's made up of the source and destiny nodes ID.
        :type id: tuple[id,id]
        :param properties: List of the names of the attributes present on the network graph to be added to the object.
                           Every entry on the list will create a new attribute with its name.
                           If the network doesn't have a value for the specified property and node ID, the value will be filled with None
        :type properties: list[str]
        :param kwargs: Aditional attributes with their values to be added to the object
        :type kwargs: dict
        """ 
        self.src_node = src_node
        self.dst_node = dst_node
        self.id = (src_node.id, dst_node.id)
        super().__init__(self.id, model)
        self.sumo_id = self.model.nx_to_sumo[self.id]
        self.observables = observables
        self.info = self.model.connection.road_info

        for property in properties:
            try:
                self.__dict__[property] = self.model.graph.edges[self.id][property]
            except KeyError: # Property not found in network edge
                self.set_property(property, None) # Set default value to None

        if "max_speed" not in kwargs:
            kwargs["max_speed"] = self.info.get_max_speed(self)

        if "lanes" not in kwargs:
            kwargs["lanes"] = self.info.get_lane_number(self)
            
        try:
            kwargs["time"] = self.length/kwargs["max_speed"]
        except (AttributeError, TypeError):
            kwargs["length"] = self.info.get_length(self)
            kwargs["time"] = kwargs["length"]/kwargs["max_speed"]
        
        for kwarg in kwargs:
            self.set_property(kwarg, kwargs[kwarg]) 

    def set_property(self,property, value):
        """
        Creates or updates the value of an attribute on the object and on the model's network.

        :param property: Name of the property.
        :type property: str
        :param value: Value of the property.
        :type value: Object
        """ 
        self.__dict__[property] = value
        self.model.graph.edges[self.id][property] = value # Create it in graph  

    def get_vehicles(self):
        """"
        Gets all the vehicles on the road

        :return: List of vehicles present in the road
        :rtype: list[AITrafficLab.agents.Vehicle_agent]
        """ 
        return  self.model.grid.get_cell_list_contents([self.id])
    
    def get_leader(self, agent):
        """"
        Gets the agent in front of the given agent. If there is no vehicle in front of the given agent in this road
        it returns the destination node of the road.

        :param agent: Agent from which to obtain the agent that is in front of it.
        :type agent: AITrafficLab.agents.Vehicle_agent

        :return: Agent in front
        :rtype: AITrafficLab.agents.Vehicle_agent or AITrafficLab.agents.Junction_agent
        """ 
        agents = self.model.grid.get_cell_list_contents([self.id])
        leader = agents.index(agent)-1
        if leader < 0:
            return self.dst_node
        return agents[leader]
    
    def get_follower(self, agent):
        """"
        Gets the agent behind of the given agent. If there is no vehicle behind of the given agent in this road
        it returns the source node of the road.

        :param agent: Agent from which to obtain the agent that is behind it.
        :type agent: AITrafficLab.agents.Vehicle_agent

        :return: Agent behind
        :rtype: AITrafficLab.agents.Vehicle_agent or AITrafficLab.agents.Junction_agent
        """ 
        agents = self.model.grid.get_cell_list_contents([self.id])
        follower = agents.index(agent)+1
        if follower >= len(agents):
            return self.src_node
        return agents[follower]
    
    def get_agent_by_pos(self, pos, default_destination=True):
        """"
        Gets the agent on the specified position. 
        If there are no vehicle agents on the road ir returns a Junction_agent between
        the source and the destination depending on the value of default_first.

        :param pos: Index of the agent to be retrieved
        :type pos: int
        :param default_destination: Decides which node is returned:
                                        -True: the destination node is returned
                                        -False: the origgin node is returned
        :type default_destination: bool

        :return: Agent in the specified position
        :rtype: AITrafficLab.agents.Vehicle_agent or AITrafficLab.agents.Junction_agent
        """ 
        agents = self.model.grid.get_cell_list_contents([self.id])
        if len(agents) > 0:
            return agents[pos]
        elif default_destination:
            return self.dst_node
        else:
            return self.src_node
    
    
    def get_first(self):
        """"
        Convenieve method, returns the first agent on the road.

        :return: Agent in first position
        :rtype: AITrafficLab.agents.Vehicle_agent or AITrafficLab.agents.Junction_agent
        """ 
        return self.get_agent_by_pos(0) 

    def get_last(self):
        """"
        Convenieve method, returns the last agent on the road.

        :return: Agent in last position
        :rtype: AITrafficLab.agents.Vehicle_agent or AITrafficLab.agents.Junction_agent
        """ 
        return self.get_agent_by_pos(-1, default_destination=False) 
        
    def step(self):
        """
        Executes the logic of the road agent and logs the metrics defined in the attribute observables.
        """ 
        self.step_behaviour()
        for obs in self.observables:
            try:
                self.model.road_statistics[obs][self.id].append(self.observables[obs](self))
            except KeyError: # First time logging 
                self.model.road_statistics[obs][self.id] = [self.observables[obs](self)] 
    def step_behaviour(self):
        """
        Method prepared to be overriden with the junction's logic for every iteration. 
        """ 
        pass

    def on_destroy(self):
        """
        Method prepared to be overriden with the junction's logic before being deleted. 
        """ 
        pass

    def __str__(self) -> str:
        return "Edge({},{})".format(self.id[0], self.id[1])
    


class Vehicle_agent(mesa.Agent):
    """
    Default agent to model vehicles in the network. 
    User may add any attribute to the constructor so that other agents can retrieve its value without the need of extending this class.
    A step_behaviour method is available to override in order to add an intelligent behaviour to the vehicle agent.

    :ivar model: Instance of the traffic model it belongs to.
    :vartype model: AITrafficLab.traffic_model.Traffic_model
    :ivar origin: Road agent where the vehicle starts its route.
    :vartype origin: AITrafficLab.agents.Road_agent
    :ivar destination: Road agent where the vehicle ends its route.
    :vartype destination: AITrafficLab.agents.Road_agent
    :ivar road: Current road of the agent
    :vartype road: AITrafficLab.agents.Road_agent
    :ivar observables: List of callback functions for the metrics to be collect in each iterations.
                       Each function must recieve exactly one argument: the agent itself
    :vartype observables: list[function]
    :ivar info: Allows user to retrieve information regarding the vehicle directly from the traffic simulator.
    :vartype info: AITrafficLab.ootraci.Vehicle_info
    :ivar departed: Iteration in which the agent was created.
    :vartype info: int
    """
    next_id = 0

    def __init__(self, model, origin:Road_agent, destination:Road_agent,  type="Car", id = None, observables = {}, **kwargs):
        """
        Creates a Vehicle_agent instance.

        :param model: Instance of the traffic model it belongs to.
        :type model: AITrafficLab.traffic_model.Traffic_model
        :param origin: Road agent where the vehicle starts its route.
        :type origin: AITrafficLab.agents.Road_agent
        :param destination: Road agent where the vehicle ends its route.
        :type destination: AITrafficLab.agents.Road_agent
        :param type: Used to differentiate collections of vehicles from the same class.
        :type type: str
        :param id: Vehicle ID used by the traffic simulator. ID must be unique. If no ID is provided a new unique ID is created.
        :type id: str
        :param observables: List of callback functions for the metrics to be collect in each iterations.
                            Each function must recieve exactly one argument: the agent itself
        :type observables: list[function]
        :param kwargs: Aditional attributes with their values to be added to the object
        :type kwargs: dict
        """ 
        if id:

            new_id = id
        else:
            new_id = Vehicle_agent._get_new_id(type)
        self.id = new_id
        
        super().__init__(new_id, model)
        self.origin = origin
        self.destination = destination
        self.road = self.origin
        self.type = type
        self.observables = observables
        self.info = self.model.connection.vehicle_info
        self.departed = self.model.schedule.time
        self.__dict__.update(kwargs)

    @classmethod
    def _get_new_id(cls, type):
        """
        Creates a new unique ID

        :return: new ID
        :rtype: str
        """
        id = str(type)+str(cls.next_id)
        cls.next_id+=1
        return id 
     
    def move(self, road_id):
        """
        Moves the agent from one road to another. Updates the current road.

        :param road_id: Road ID to move the agent
        :type road_id: tuple[int,int]
        """
        self.model.grid.move_agent(self, road_id)
        self.road = self.model.roads[road_id]

    def check_road_change(self, sumo_road_id):
        """
        Checks if the agent has changed road in the traffic simulator.
        If it has, it moves the agent in the model.

        :param sumo_road_id: Road ID used by the traffic simulator
        :type sumo_road_id: str
        :return: Road ID used by the model if the vehicle changed road
        :rtype: tuple[int, int] or None
        """
        road_id = self.model.sumo_to_nx[sumo_road_id]
        if self.road.id != road_id:
            self.move(road_id)
            return road_id 
              
    def step(self):
        """
        Executes the logic of the vehicle agent and logs the metrics defined in the attribute observables.
        If the reached the end of its route it is sent to the model's to_destroy queue.
        """ 
        try:
            self.check_road_change(self.info.get_road(self))
            self.step_behaviour()

            for obs in self.observables:
                try:
                    self.model.vehicle_statistics[obs][self.id].append(self.observables[obs](self))
                except KeyError: # First time logging 
                    self.model.vehicle_statistics[obs][self.id] = [self.observables[obs](self)]
        except KeyError as ke: # Agent currently in the middle of a junction or hasn't departed yet
            pass 
        except Exception as ex: 
            if self.model.connection.manage_exception(ex, self)[0] == err.NON_EXISTING: # Non-existint agent
                try:
                    self.road.agents.remove(self)
                except:
                    pass
                self.model.to_destroy.append(self) # Agent arrived to its destination or no longer existing
            else: # Different traci exception
                raise(ex)
        
    def step_behaviour(self):
        """
        Method prepared to be overriden with the vehicle's logic for every iteration. 
        """ 
        pass
    
    def on_destroy(self):
        """
        Executes the vehicle's logic before being deleted. The basic logic is to log the 
        total time since the creation of the vehicle. 
        """ 
        self.model.vehicle_statistics["time"][self.id] = [self.model.schedule.time - self.departed]

    def __str__(self) -> str:
        return self.id

class Dijkstra_vehicle(Vehicle_agent):
    """
    Extension of the Vehicle_agent class. It calculates the fastest route upon departure using Dijkstra algorithm
    and follows it until the end.

    :ivar route: list of edges that form the fastest route from origin to destination
    :vartype route: list[AITrafficLab.agents.Road_agent]
    
    """
    def __init__(self, model, origin, destination,  type="Car", id = None, observables = {}):
        super().__init__(model, origin, destination,  type=type, id = id, observables = observables)
        nodes = nx.dijkstra_path(model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight='time')
        nodes = [self.road.src_node.id] + nodes
        self.route = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        self.started = False
    
    def step_behaviour(self):
        try:
            if not self.started:
                self.info.set_route(self,self.route)
                self.started = True
        except:
            pass

class Yen_vehicle(Vehicle_agent):
    """
    Extension of the Vehicle_agent class. It calculates the k fastest routes upon departure using Yen algorithm,
    then selects a random route and follows it until the end.

    :ivar route: list of edges that form the fastest route from origin to destination
    :vartype route: list[AITrafficLab.agents.Road_agent]
    
    """
    def __init__(self, model, origin, destination, k,  type="Car", id = None, observables = {}):
        super().__init__(model, origin, destination,  type=type, id = id, observables = observables)
        rand = random.randint(0, k)
        nodes = list(
            islice(nx.shortest_simple_paths(model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight="time"), 51)
        )[rand]
        nodes = [self.road.src_node.id] + nodes
        self.route = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        self.started = False
    def step_behaviour(self):
        try:
            if not self.started:
                self.info.set_route(self,self.route)
                self.started = True
        except:
            pass
