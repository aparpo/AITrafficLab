import traci
import time

class Vehicle_info():

    def __init__(self):
        self.return_agent = {True: self._return_agent, False: self._return_id}

    def get_road(self, agent):
        return traci.vehicle.getRoadID(agent.id)

    def get_acceleration(self, agent):
        try:
            return traci.vehicle.getAcceleration(agent.id)
        except AttributeError:
            return traci.vehicle.getAcceleration(agent)
    
    def get_co2_emission(self, agent, deltaT = 1):
        try:
            return traci.vehicle.getCO2Emission(agent.id)*agent.model.deltaT
        except AttributeError:
            return traci.vehicle.getCO2Emission(agent)*deltaT
    
    def get_co_emission(self, agent, deltaT = 1):
        try:
            return traci.vehicle.getCOEmission(agent.id)*agent.model.deltaT
        except AttributeError:
            return traci.vehicle.getCOEmission(agent)*deltaT
    
    def get_accumulated_distance(self, agent, x = None, y = None):
        try:
            return traci.vehicle.getDrivingDistance2D(agent.id, agent.origin.src_node.x, agent.origin.src_node.y)
        except AttributeError:
            return traci.vehicle.getDrivingDistance2D(agent, x, y)
    
    def get_follower(self, agent, dist=0, as_agent=False, _class=None)-> tuple[str, float]:
        try:
            return self.return_agent[as_agent](agent,traci.vehicle.getFollower(agent.id, dist=dist), _class)
        except AttributeError:
            return self.return_agent[as_agent](agent,traci.vehicle.getFollower(agent, dist=dist), _class)

    def get_leader(self, agent, dist=0, as_agent=False, _class=None)-> tuple[str, float]:
        try:
            return self.return_agent[as_agent](agent,traci.vehicle.getLeader(agent.id, dist=dist), _class)
        except AttributeError:
            return self.return_agent[as_agent](agent,traci.vehicle.getLeader(agent, dist=dist), _class)
    
    def get_fuel_consumption(self, agent, deltaT = 1):
        try:
            return traci.vehicle.getFuelConsumption(agent.id)*agent.model.deltaT
        except AttributeError:
            return traci.vehicle.getFuelConsumption(agent)*deltaT
    
    def get_position(self, agent)-> tuple[float, float]:
        try:
            return traci.vehicle.getPosition(agent.id)
        except AttributeError:
            return traci.vehicle.getPosition(agent)
    
    def get_speed(self, agent)-> float:
        try:
            return traci.vehicle.getSpeed(agent.id)
        except AttributeError:
            return traci.vehicle.getSpeed(agent)
        
    def set_route(self, agent, road_list):            
        try:
            edgeList = [agent.model.nx_to_sumo[road.id] for road in road_list]
            traci.vehicle.setRoute(agent.id, edgeList)
        except AttributeError:
            edgeList = [agent.model.nx_to_sumo[road] for road in road_list]
            traci.vehicle.setRoute(agent, edgeList)
    
    def is_stopped(self, agent):
        try:
            return traci.vehicle.isStopped(agent.id)
        except AttributeError:
            return traci.vehicle.isStopped(agent.id)
    
    def _return_agent(self, agent, id):
        return agent.model.agents[id]
    
    def _return_id(self, agent, id):
        return id
    
class Road_info():

    # def __init__(self):
    #     self.return_agent = {True: self._return_agent, False: self._return_id}

    def get_co2_emission(self, road):
        return traci.edge.getCO2Emission(road.sumo_id)*road.model.deltaT
    
    def get_co_emission(self, road):
        return traci.edge.getCOEmission(road.sumo_id)*road.model.deltaT
    
    def get_co_electricity_consumption(self, road):
        return traci.edge.getElectricityConsumption(road.sumo_id)*road.model.deltaT
    
    def get_fuel_consumption(self, road):
        return traci.edge.getFuelConsumption(road.sumo_id)*road.model.deltaT
    
    def get_hce_emission(self, road):
        return traci.edge.getHCEmission(road.sumo_id)*road.model.deltaT
    
    def get_nox_emission(self, road):
        return traci.edge.getNOxEmission(road.sumo_id)*road.model.deltaT
    
    def get_noise_emission(self, road):
        return traci.edge.getNoiseEmission(road.sumo_id)*road.model.deltaT

    def get_max_speed(self,road):
        return traci.lane.getMaxSpeed(road.sumo_id+"_0")
    
    def get_length(self, road):
        return traci.lane.getLength(road.sumo_id+"_0")