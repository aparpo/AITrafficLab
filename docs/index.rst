Welcome to AITrafficLab's documentation!
========================================
.. _Mesa: https://mesa.readthedocs.io/en/stable/
.. _OpenStreetMap: https://www.openstreetmap.org/
.. _Networkx: https://networkx.org/
.. _SUMO installation guide: https://sumo.dlr.de/docs/Installing/index.html
.. _SUMO: https://sumo.dlr.de/docs/index.html

.. toctree::
   :maxdepth: 1
   :hidden:
   
   self
 
Introduction
------------

AITrafficLab is a powerful and easy-to-use tool to code and deploy multiagent based solutions for traffic problems that extends `Mesa`_'s functionalities
by adapting them to the field of urban mobility. 
It allows the user to create networks, manage swarms of vehicles by defining its logic once and gather information about their performance.
Not only vehicles can have an intelligent behaviour, roads and junctions may work as intelligent agents too. 

.. note::
   Currently AITrafficLab only supports the use of one traffic simulator: Simulation of Urban Mobility (`SUMO`_).
   To work with other traffic simulators user may need to create its own connection class extending from :doc:`source/connection`.

.. .. warning::
..   This is a warning. It highlights potential issues or pitfalls.

.. .. attention::
..   This is an attention note. It draws attention to important points.

.. .. tip::
..   This is a tip. It offers helpful suggestions or recommendations.

Installation guide
-------------------

In order to use AITrafficLab you must first install a traffic simulator to work with. If it's your first time working with AITrafficLab, we highly recommend using
SUMO as your traffic simulator. Once you have understood the basic functioning of AITrafficLab, you may as well try using other simulators by creating a custom :doc:`source/connection`.

To install SUMO please follow the steps on the `SUMO installation guide`_.

After installing a traffic simulator, choose your desired virtual environment and install AITrafficLab by running the following commands:

.. code-block:: bash
	
	# Upgrade your pip version
	pip install --upgrade pip
	
	# Install AITrafficLab
	pip install AITrafficLab
	
.. note::
	Note: you may need to restart the kernel to use updated packages.

Usage
------

In the following section you will understand how to create your first urban mobility simulation and test its results.

To begin with, we first need to import AITrafficLab and create a connection and a traffic model:

.. code-block:: python

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
			iters = 1000,
			gui=True
		)
		model.start()

.. tip::
	In this example we used "Las Rozas de Madrid" as our urban network, but you can change it for any other
	city or town that suits your study as long as it can be recognized by `OpenStreetMap`_. 

.. tip::
	Another interesting feature is to design your own network with `Networkx`_ and pasing it to the model 
	via the attribute `graph`. Or create it yourself using tools like Netedit from the SUMO package.

This chunk of code will start a simulation using SUMO as the traffic simulator. It will run for 1000 iterations and it will display its Graphic User Interface, as `gui=True`
indicates the model that the user wants to see the simulation running.

.. attention::
   Launching a simulation using its GUI reduces the simulation speed. It is unadvised to be used when running multiple simulations.
   
However, simply watching random vehicles travel along the network is not that interesting. We could then try to create a traffic solving model 
by adding an intelligent behaviour to the vehicles. This can be easily done by extending the Vehicle_agent (which can be found in :doc:`source/agents`):

.. code-block:: python

	class Yen_vehicle(Vehicle_agent):
		def __init__(self, model, origin, destination, k, observables = {}):
			super().__init__(model, origin, destination,  type="Yen_car", observables = observables)
			nodes = list(
				islice(nx.shortest_simple_paths(model.graph, self.road.dst_node.id, self.destination.dst_node.id, weight="time"), 3)
			)[1]
			nodes = [self.road.src_node.id] + nodes
			self.route = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
			self.started = False
		
		def step_behaviour(self):
			try:
				if not self.started:
					self.info.set_route(self,self.route)
					self.started = True
			except: # agent hasn't been created on the simulator yet
				pass

The previous class is an example of how to design your own custom intelligent vehicle. 
With this experiment we want to test the following hipothesis: "If, instead of the fastest route, every car takes the second fastest route, the traffic density is decreased".
Therefore, this type of vehicle uses Yen's K shortest paths algorithm to obtain the second fastest route to its destination.
It reimplements 2 methods: 
 * __init__(): to calculate the second fastest route upon creation

 * step_behaviour(): to update its route on its first iteration


.. attention::
   Updating values in the simulator upon an agents creation is unadvised as the simulator may decide not to create the vehicle immediately if there is no roon
   for it on its starting road. It is important to note that an instance of the vehicle can exist in the traffic model but not yet in the traffic simulator.
   
Now we could also specify the way and amount of vehicles added to the simulation. For that we could make a custom vehicle generator:

.. code-block:: python

	class Custom_vehicle_generator(generators.Vehicle_generator):
		def generate_vehicle(self,model):
			if random.random() < 0.5:
				return Yen_vehicle(model, model.roads[1, 2], model.roads[14, 15], observables=self.observables) 
			else:
				return Vehicle_agent(model, model.roads[1, 3], model.roads[24, 25], observables=self.observables) 
		
		def generate_vehicles(self, model, *args):
			return [self.generate_vehicle(model) for _ in range(self.get_vehicle_number())]
		
		def get_vehicle_number(self):
			return 5
		
		def initial_generation(self, model):
			return self.generate_vehicles(model)

With this Custom_vehicle_generator we create batches of 5 vehicles, 50% of which will be created with the Yen's algorithm behaviour and the remaining with the default one.
We also specified the starting and ending road for each type of vehicles. Yen vehicles will travel from the edge conecting the nodes 1 and 2, to the one conecting the nodes 14 and 15.
The same will be applied to the default vehicles, but from the edge (1,3) to the (24,25). This will allow us to visually compare both behaviours.

.. tip::
	To implement more complex algorithms, roads and junctions can also act as intelligent agents. To see examples of fully implemented algorithms please refer to :doc:`source/algorithms`.


.. toctree::
   :maxdepth: 2
   :caption: Modules:
   
   source/model
   source/agents
   source/generators
   source/batch
   source/schedule
   source/connection
   source/ootraci
   source/algorithms
