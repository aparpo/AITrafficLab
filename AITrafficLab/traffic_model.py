import mesa
import networkx as nx
import osmnx as ox
from tqdm import tqdm

from AITrafficLab.agents import *
from AITrafficLab.generators import *
from AITrafficLab.schedule import GraphOrderedScheduler

class Traffic_model(mesa.Model):
    """
    Multiagent model for traffic simulations in urban networks.

    :ivar connection: Traffic simulator abstraction.
    :vartype connection: AITrafficLab.connection.Simulator_connection
    :ivar graph: Graph associated to the urban network. Contains basic info such as travelling time, road length or road max speed.
    :vartype graph: Networkx.DiGraph
    :ivar line_graph: Line graph obtained from graph. It models the actual space where agents interact.
    :vartype line_graph: Networkx.DiGraph
    :ivar junctions: Collection of all junction agents present in the model.
    :vartype junctions: dict[id, AITrafficLab.agents.Junction_agent]
    :ivar roads: Collection of all road agents present in the model.
    :vartype roads: dict[id, AITrafficLab.agents.Road_agent]
    :ivar schedule: Activation order for the different agents. Also stores all the agent instances.
    :vartype schedule: AITrafficLab.schedule.GraphOrderedActivation
    :ivar to_destroy: Collection of all agents to be removed from the simulation in the next iteration.
    :vartype to_destroy: list[AITrafficLab.agents.Vehicle_agent]
    :ivar road_statistics: Information logged by the road agents. If set to, every road agent logs a value each iteration.
                           Information is stored first by the metric name (e.g. "time", "co2"), and then by the agents itself.
                           Each agent can store any kind of object each iteration on its own list.
                           After the end of the simulation, this attribute can be casted into a Pandas DataFrame.
    :vartype road_statistics: dict[str, dict[AITrafficLab.agents.Road_agent,list[Object]]]
    :ivar vehicle_statistics: Information logged by the vehicle agents. If set to, every vehicle agent logs a value each iteration.
                           Information is stored first by the metric name (e.g. "time", "co2"), and then by the agents itself.
                           Each agent can store any kind of object each iteration on its own list.
                           After the end of the simulation, this attribute can be casted into a Pandas DataFrame.
    :vartype vehicle_statistics: dict[str, dict[AITrafficLab.agents.Vehicle_agent,list[Object]]]
    """ 
    def __init__(self,graph_file, connection, node_generator=None, edge_generator=None, vehicle_generator=None, iters=None, gui = False, graph=None):
        """
        Creates a Traffic_model instance.

        :param graph_file: File where the simulation's graph info is stored.
        :type graph_file: str
        :param connection: Traffic simulator abstraction.
        :type connection: AITrafficLab.connection.Simulator_connection
        :param node_generator: Factory object in charge of creating node instances out of network junctions. 
                            If no node_generator is provided a basic AITrafficLab.generators.Node_generator is created.
        :type node_generator: AITrafficLab.generators.Node_generator
        :param edge_generator: Factory object in charge of creating edge instances out of network roads.
                            If no edge_generator is provided a basic AITrafficLab.generators.Edge_generator is created.
        :type edge_generator: AITrafficLab.generators.Edge_generator
        :param vehicle_generator: Factory object in charge of creating vehicle instances. 
                                If no vehicle_generator is provided a basic AITrafficLab.generators.Dumb_vehicle_generator is created.
        :type vehicle_generator: AITrafficLab.generators.Vehicle_generator
        :param iters: Number of iterations to run the simulation before closing the connection.
                    If no value is provided the simulation will keep on running forever or until there are no more vehicles left.
        :type iters: int
        :param gui: Indicates wether to launch or not the simulators Graffic User Interface.
        :type gui: bool
        :param graph: Custom graph to be used. If no graph is provided, the network topology is infered from the network in graph_file.
        :type graph: Networkx.DiGraph
        """ 
        super().__init__()
        self.graph_file = graph_file
        self.connection = connection
        self.gui = gui
        self.iters = iters
        if  iters is None or iters<=0:
            self.start_strategy = self._start_eternal
        else:
            self.start_strategy = self._start_iters
        if graph:
            self.graph = graph
        else:
            self.graph = nx.DiGraph(ox.graph_from_xml(graph_file+'.osm.xml'))

        
        if not node_generator:
            node_generator = Node_generator(self.connection)
        self.node_generator = node_generator
        if not edge_generator:
            edge_generator = Edge_generator(self.connection)
        self.edge_generator = edge_generator
        if not vehicle_generator:
            vehicle_generator = Dumb_vehicle_generator(self.connection)
        self.vehicle_generator = vehicle_generator

        self.junctions = dict()
        self.roads = dict()
        
        self.reset()

        self.to_destroy = []

        self._initialize()
        
    
    def _initialize(self):
        """
        Sets up the conditions needed for the simulation to run: 
            -Starts the simulator's connection
            -Reads the information from the graph_file.
            -Creates all the node and edge agents
            -Closes the connection to avoid resource waste until simulation is started.
        """ 
        self.connection.start(self.graph_file, False)
        
        self.deltaT = self.connection.get_step_time()            
        self.graph, self.sumo_to_nx, self.nx_to_sumo = self.connection.load_information(self.graph_file, self.graph)
        self.line_graph = nx.line_graph(self.graph)

        self.grid = mesa.space.NetworkGrid(self.line_graph)
        self.schedule = GraphOrderedScheduler(self, self.node_generator.get_classes(), self.edge_generator.get_classes())

        for node in self.node_generator.create_nodes(self):
            self.junctions[node.id]=node
            self.add_agent(node, place=False)
        
        for edge in self.edge_generator.create_edges(self):
            self.roads[edge.id]=edge
            self.add_agent(edge, place=False)
        
        self.connection.close()

    def start(self):
        """
        Starts the traffic simulation. Adds at least one vehicle agent, then creates an initial vehicle batch.
        The simulation will either run forever or for a set number of iterations depending on the value of the attribute iters.
        """ 
        self.connection.start(self.graph_file, self.gui)
        vehicle = self.vehicle_generator.generate_vehicle(self)
        self.add_agent(vehicle, vehicle.road.id)
        for vehicle in self.vehicle_generator.initial_generation(self):
            self.add_agent(vehicle, vehicle.road.id)
        self.start_strategy()
    
    def reset(self):
        """
        Clears the information logged by the agents. May be used to run several simulation by restarting the model every time.
        """ 
        self.road_statistics = {stat:dict() for stat in self.edge_generator.observables}
        self.vehicle_statistics = {stat:dict() for stat in self.vehicle_generator.observables}
        self.vehicle_statistics["time"] = dict()

    def step(self):  
        """
        Executes one iteration by running the logic of the model:
            - Creates new agents each iteration
            - Awakes the agents acording to the schedule's logic
            - Runs one step simulation on the traffic simulator
        """       
        for vehicle in self.vehicle_generator.generate_vehicles(self, 10):
            self.add_agent(vehicle, vehicle.road.id)
        self.schedule.step()
        self.connection.simulation_step()
        
        self._purge()
    
    def _start_eternal(self):
        """
        Runs the simulation until it finishes.
        """ 
        while self.connection.is_simulation_running():
            self.step()
        self._destroy()
        self.connection.close()
    
    def _start_iters(self):
        """
        Runs the simulation for a set amount of iterations. Tracks the progress of the simulation.
        """ 
        try:
            for _ in tqdm(range(self.iters), desc = "Current simulation progress"):
                self.step()
        except Exception as e:
            self.connection.manage_exception(e, self)
        self._destroy()
        self.connection.close()
    
    def _purge(self):
        """
        Calls the on_destroy method for each agent stored in to_destroy and then removes it completely from the simulation.
        """ 
        for deleted_agent in self.to_destroy:
            try:
                deleted_agent.on_destroy()
                self.grid.remove_agent(deleted_agent)
                self.schedule.remove(deleted_agent)
                
            except KeyError:
                pass
            self.to_destroy.remove(deleted_agent)
    
    def _destroy(self):
        """
        Deletes the remaining agents.
        """ 
        vehicles = [
            vehicle for vehicle in self.schedule.agents if
                any(isinstance(vehicle, _class) for _class in self.vehicle_generator.get_classes())
        ]
        for agent in vehicles:
            self.to_destroy.append(agent)
        self._purge()
    
    def add_agent(self, agent, place=None):
        """
        Adds an agent to the model. If the agent is a vehicle it's added to the traffic simulator too.

        :param agent: Agent to be added
        :type agent: Mesa.Agent
        :param place: Road's id where to place the agent if it's a vehicle.
        :type place: tuple[int,int]
        """ 
        if isinstance(agent, Vehicle_agent):
            self.connection.add_vehicle(agent)
        self.schedule.add(agent)
        if place:
            self.grid.place_agent(agent,place)
        
