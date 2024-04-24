import traci
import mesa
import ootraci
import error_codes as err

class Junction_agent(mesa.Agent):
    def __init__(self, model, id, properties:list, **kwargs):
        super().__init__(id, model)
        self.id = id

        for property in properties:
            try:
                self.__dict__[property] = self.model.graph.nodes[id][property]
            except KeyError: # Property not found in network node
                self.set_property(property, None)
        
        for kwarg in kwargs:
            # self.__dict__[kwarg] = kwargs[kwarg]
            # self.model.graph.nodes[id][property] = kwargs[kwarg] 
            self.set_property(kwarg, kwargs[kwarg])
    
    def step(self):
        self.step_behaviour()
    
    def step_behaviour(self):
        pass
    
    def set_property(self,property, value):
        self.__dict__[property] = value
        self.model.graph.nodes[self.id][property] = value # Create it in graph
    
    def on_destroy(self):
        pass

class Road_agent(mesa.Agent):
    def __init__(self, model, src_node:Junction_agent, dst_node: Junction_agent, observables:dict, properties: list, **kwargs):
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
        try:
            kwargs["time"] = self.length/kwargs["max_speed"]
        except AttributeError:
            kwargs["length"] = self.info.get_length(self)
            kwargs["time"] = kwargs["length"]/kwargs["max_speed"]
        
        for kwarg in kwargs:
            self.set_property(kwarg, kwargs[kwarg])
    
    def set_property(self,property, value):
        self.__dict__[property] = value
        self.model.graph.edges[self.id][property] = value # Create it in graph
    
    def get_leader(self, agent):
        agents = self.model.grid.get_cell_list_contents([self.id])
        leader = agents.index(agent)-1
        if leader < 0:
            return self.dst_node
        return agents[leader]
    
    def get_follower(self, agent):
        agents = self.model.grid.get_cell_list_contents([self.id])
        follower = agents.index(agent)+1
        if follower >= len(agents):
            return self.src_node
        return agents[follower]

    def get_pos(self, pos, default_first=True):
        agents = self.model.grid.get_cell_list_contents([self.id])
        if len(agents) > 0:
            return agents[pos]
        elif default_first:
            return self.dst_node
        else:
            return self.src_node
    
    def get_first(self):
        self.get_pos(0)
    
    def get_last(self):
        self.get_pos(-1, default_first=False)
    
    def step(self):
        self.step_behaviour()
        for obs in self.observables:
            try:
                self.model.road_statistics[obs][self.id].append(self.observables[obs](self))
            except KeyError: # First time logging 
                self.model.road_statistics[obs][self.id] = [self.observables[obs](self)]
    
    def step_behaviour(self):
        pass

    def on_destroy(self):
        pass

    def __str__(self) -> str:
        return "Edge({},{})".format(self.id[0], self.id[1])
    


class Vehicle_agent(mesa.Agent):
    next_id = 0

    def __init__(self, model, origin, destination,  type="Car", id = None, observables = {}):
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

        #self.model.add_agent(self)

    @classmethod
    def _get_new_id(cls, type):
        id = str(type)+str(Vehicle_agent.next_id)
        Vehicle_agent.next_id+=1
        return id
    
    def move(self, road_id):
        self.model.grid.move_agent(self, road_id)
        self.road = self.model.roads[road_id]
    
    def check_road_change(self, sumo_road_id):
        if self.road != self.model.sumo_to_nx[sumo_road_id]:
            self.move(self.model.sumo_to_nx[sumo_road_id])
            # print("Me movi a")
            # print(self.road)
        
    
    def step(self):
        # print("Soy el agente {}".format(self.id))
        # print(" Puedo ir a ")
        # print(self.model.grid.get_neighborhood(self.node))

        try:
            # print(self.get_road(), self.model.sumo_to_nx[self.get_road()])
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
        pass
    
    def on_destroy(self):
        pass
