"""Transformaciones explícitas de fuerza a costo y vistas experimentales."""
import networkx as nx
import numpy as np


# Convierte fuerza en costo inverso: una asociación más fuerte resulta más barata de recorrer.
def costo_inverso(fuerza):
    return 1.0 / fuerza


# Convierte fuerza en costo logarítmico y añade epsilon para evitar costos nulos.
def costo_logaritmico(fuerza, epsilon=1e-6):
    return -np.log(fuerza) + epsilon


# Añade los dos costos comparativos sin reemplazar el costo elegido al construir el grafo.
def calcular_distancias(grafo):
    for _, _, datos in grafo.edges(data=True):
        fuerza = datos['fuerza']
        if not np.isfinite(fuerza) or not 0 < fuerza <= 1:
            raise ValueError('fuerza debe estar en (0, 1].')
        datos['costo_inverso'] = costo_inverso(fuerza)
        datos['costo_log'] = costo_logaritmico(fuerza)
        datos.setdefault('costo', datos['costo_log'])
    return grafo


# Elimina la dirección promediando las fuerzas observadas y calcula los costos de esa vista.
def crear_vista_no_dirigida(grafo):
    vista = nx.Graph()
    vista.add_nodes_from(sorted(grafo))
    for a, b, datos in grafo.edges(data=True):
        if vista.has_edge(a, b):
            vista[a][b]['suma'] += datos['fuerza']
            vista[a][b]['observaciones'] += 1
        else:
            vista.add_edge(a, b, suma=datos['fuerza'], observaciones=1)
    for _, _, datos in vista.edges(data=True):
        datos['fuerza'] = datos.pop('suma') / datos.pop('observaciones')
    return calcular_distancias(vista)
