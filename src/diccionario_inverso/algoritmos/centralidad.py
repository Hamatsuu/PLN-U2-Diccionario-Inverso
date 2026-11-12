"""Centralidades completas o calculadas en el subgrafo local."""
import networkx as nx
import numpy as np
from scipy.sparse.csgraph import dijkstra


# Limita los candidatos a las semillas y sus vecinos salientes a un salto.
def reducir_grafo(grafo, semillas):
    nodos = set(semillas)
    for semilla in semillas:
        nodos.update(grafo.successors(semilla))
    return grafo.subgraph(nodos)


# Ordena los candidatos locales por la fuerza de sus asociaciones entrantes.
def buscar_grado_ponderado(grafo, consulta, grados_completos=None):
    """Ordena los candidatos de la consulta por fuerza de entrada.

    Con grados_completos usa puntuaciones precalculadas del grafo completo.
    Sin ese diccionario calcula las puntuaciones en el subgrafo reducido.
    """
    if not consulta["semillas"]:
        return []

    subgrafo = reducir_grafo(grafo, consulta["semillas"])
    candidatos = set(subgrafo) - set(consulta["excluir"])

    if grados_completos is None:
        puntuaciones = dict(subgrafo.in_degree(weight="fuerza"))
    else:
        puntuaciones = grados_completos

    return sorted(candidatos, key=lambda palabra: (-puntuaciones[palabra], palabra))


# Calcula cercanía entrante con corrección WF, equivalente a NetworkX: favorece recorridos de bajo costo.
def calcular_cercania(grafo, atributo, lote=128):
    nodos = list(grafo)
    n = len(nodos)
    if n <= 1:
        return dict.fromkeys(nodos, 0.0)

    # Transponer conserva la dirección conceptual: buscamos quién puede llegar al candidato.
    matriz = nx.to_scipy_sparse_array(grafo, nodelist=nodos, weight=atributo, format="csr").T.tocsr()
    puntuaciones = {}
    for inicio in range(0, n, lote):
        fin = min(inicio + lote, n)
        distancias = dijkstra(matriz, directed=True, indices=range(inicio, fin))
        alcanzables = np.isfinite(distancias)
        r = alcanzables.sum(axis=1) - 1  # No contar al propio nodo.
        suma_distancias = np.where(alcanzables, distancias, 0.0).sum(axis=1)

        valores = np.zeros(fin - inicio)
        np.divide(r, suma_distancias, out=valores, where=suma_distancias > 0)
        valores *= r / (n - 1)
        puntuaciones.update(zip(nodos[inicio:fin], valores))

    return puntuaciones


# Ordena los candidatos locales por cercanía, usando puntuaciones completas o del subgrafo.
def buscar_cercania(grafo, consulta, atributo, puntuaciones_completas=None):
    if not consulta["semillas"]:
        return []

    subgrafo = reducir_grafo(grafo, consulta["semillas"])
    candidatos = set(subgrafo) - set(consulta["excluir"])
    if not candidatos:
        return []

    if puntuaciones_completas is None:
        puntuaciones = calcular_cercania(subgrafo, atributo)
    else:
        puntuaciones = puntuaciones_completas
    return sorted(candidatos, key=lambda palabra: (-puntuaciones[palabra], palabra))


# Calcula intermediación dirigida normalizada; es exacta con hasta k nodos y muestreada para grafos mayores.
def calcular_intermediacion(grafo, atributo, k=64, semilla=1950):
    # Una copia pequeña evita recorrer repetidamente los filtros de una vista de subgrafo.
    trabajo = grafo.copy()
    muestra = k if len(trabajo) > k else None
    return nx.betweenness_centrality(
        trabajo, k=muestra, normalized=True, weight=atributo, seed=semilla,
    )


# Ordena los candidatos locales por su participación en caminos mínimos.
def buscar_intermediacion(grafo, consulta, atributo, puntuaciones_completas=None, k=16, semilla=1950):
    if not consulta["semillas"]:
        return []
    subgrafo = reducir_grafo(grafo, consulta["semillas"])
    candidatos = set(subgrafo) - set(consulta["excluir"])
    if not candidatos:
        return []
    if puntuaciones_completas is None:
        puntuaciones = calcular_intermediacion(subgrafo, atributo, k, semilla)
    else:
        puntuaciones = puntuaciones_completas
    return sorted(candidatos, key=lambda palabra: (-puntuaciones[palabra], palabra))

