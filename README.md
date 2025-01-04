# AITrafficLab

**AITrafficLab** is an easy-to-use tool for coding and testing multi-agent based solutions to traffic problems. It extends Mesa's functionalities by adapting them to the field of urban mobility. With AITrafficLab, users can create networks, manage swarms of vehicles by defining their logic once, and gather performance data. Not only vehicles can exhibit intelligent behavior; roads and junctions can also act as intelligent agents. View full documentation at [Read the Docs](https://aitrafficlab.readthedocs.io/en/latest/)

> **Note**  
> AITrafficLab currently supports only one traffic simulator: **Simulation of Urban Mobility (SUMO)**. To work with other traffic simulators, users may need to create their own connection class extending from the `Connection` class.

---

## Installation Guide

To use AITrafficLab, you first need to install a traffic simulator. For beginners, we highly recommend using **SUMO**. After understanding AITrafficLab's basic functions, you may try other simulators by creating a custom connection.

Follow the instructions in the SUMO installation guide to install SUMO.

After installing a traffic simulator, select your virtual environment and install AITrafficLab by running the following commands:

```bash
# Upgrade pip
pip install --upgrade pip

# Install AITrafficLab
pip install AITrafficLab
```

## Basic simulation example   

To test the first connection, you need to import **AITrafficLab** and create a connection and a traffic model. The following example will also use the road graph associated with the city of Las Rozas (storing it in "./test"), build a simulation with 1000 iterations that will be displayed using SUMO's Graphical User Interface, and finally run the simulation.  

```python
from AITrafficLab.connection import Sumo_connection
from AITrafficLab.traffic_model import Traffic_model

if __name__ == "__main__":
    simm_conn = Sumo_connection()
    path = "./test"
    place = "Las Rozas de Madrid"
    filepath = simm_conn.import_data_from(place, path)
    model = traffic_model.Traffic_model(
        filepath,
        simm_conn,
        iters=1000,
        gui=True
    )
    model.start()

```

## Design your own algorithm

Simply watching random vehicles travel along the network is not that interesting. To make the simulation more engaging, we can create a traffic-solving model by adding intelligent behavior to the vehicles. This can be achieved by extending the `Vehicle_agent` class (which can be found in the `Agents` module). Here is an example of how to design a custom intelligent vehicle class for the following experiment:

### Experiment

Using the `Yen_vehicle` class, we aim to test the following hypothesis:

> *“If, instead of the fastest route, every car takes the second fastest route, the traffic density is decreased.”*

To implement this hypothesis, the `Yen_vehicle` uses Yen’s K shortest paths algorithm to determine the second fastest route to its destination.

### Implementation

```python
class Yen_vehicle(Vehicle_agent):
    def __init__(self, model, origin, destination, k, observables = {}):
        super().__init__(model, origin, destination, type="Yen_car", observables=observables)
        nodes = list(
            islice(nx.shortest_simple_paths(model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight="time"), 3)
        )[1]
        nodes = [self.road.src_node.id] + nodes
        self.route = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
        self.started = False

    def step_behaviour(self):
        try:
            if not self.started:
                self.info.set_route(self, self.route)
                self.started = True
        except: # Agent hasn't been created on the simulator yet
            pass
```

### Explanation

- **`__init__` Method:**
  - Upon creation, calculates the second fastest route to the vehicle's destination using Yen’s K shortest paths algorithm.
  - The calculated route is stored in the `self.route` attribute.

- **`step_behaviour` Method:**
  - Updates the vehicle's route in the simulation on its first iteration.








