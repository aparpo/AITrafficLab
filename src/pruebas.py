import osmnx as ox
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
from tqdm import tqdm
import time

# graph_file = "../data/Torrejon"
# graph = nx.DiGraph(ox.io.load_graphml(graph_file+'.osm'))

# pos = nx.spring_layout(graph)
# fig, ax = plt.subplots()
# nx.draw_networkx_nodes(graph, pos)
# nx.draw_networkx_labels(graph, pos)
# curved_edges = [edge for edge in graph.edges() if reversed(edge) in graph.edges()]
# print(curved_edges)
# straight_edges = list(set(graph.edges()) - set(curved_edges))
# nx.draw_networkx_edges(graph, pos, ax=ax, edgelist=straight_edges)
# arc_rad = 0.25
# nx.draw_networkx_edges(graph, pos, ax=ax, edgelist=curved_edges, connectionstyle=f'arc3, rad = {arc_rad}')

# plt.show()

# Definir el rango del bucle externo
num_iteraciones_externo = 5

# Barra de progreso externa (para el bucle padre)
for i in tqdm(range(num_iteraciones_externo), desc='Bucle externo'):
    # Definir el rango del primer bucle interno
    num_iteraciones_interno_1 = 10

    # Barra de progreso interna para el primer bucle hijo
    barra_interna_1 = tqdm(total=num_iteraciones_interno_1, desc='Bucle interno 1', leave=False)

    # Primer bucle hijo
    for j in range(num_iteraciones_interno_1):
        # Simular alguna operación dentro del primer bucle interno
        time.sleep(0.1)
        # Actualizar la barra de progreso interna del primer bucle hijo
        barra_interna_1.update(1)

    # Definir el rango del segundo bucle interno
    num_iteraciones_interno_2 = 15

    # Barra de progreso interna para el segundo bucle hijo
    barra_interna_2 = tqdm(total=num_iteraciones_interno_2, desc='Bucle interno 2', leave=False)

    # Segundo bucle hijo
    for k in range(num_iteraciones_interno_2):
        # Simular alguna operación dentro del segundo bucle interno
        time.sleep(0.1)
        # Actualizar la barra de progreso interna del segundo bucle hijo
        barra_interna_2.update(1)
    
    # Cerrar la barra de progreso interna del primer bucle hijo
    barra_interna_1.close()
    # Cerrar la barra de progreso interna del segundo bucle hijo
    barra_interna_2.close()

    # Simular alguna operación dentro del bucle externo
    time.sleep(0.5)



print("Bucles completados.")