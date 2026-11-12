"""Recuperación dependiente de consulta, con distancias reutilizables."""
from functools import lru_cache
import igraph as ig
import networkx as nx
import numpy as np
from scipy.sparse.csgraph import dijkstra


# Prepara el grafo, las distancias y el PageRank global para reutilizarlos entre consultas.
def preparar_busqueda_consulta(grafo, atributo='costo'):
    nodos = sorted(grafo)
    indice = {nodo: i for i, nodo in enumerate(nodos)}
    aristas = list(grafo.edges(data=True))
    nativo = ig.Graph(n=len(nodos), edges=[(indice[a], indice[b]) for a, b, _ in aristas],
                      directed=grafo.is_directed())
    nativo.es["costo"] = [datos[atributo] for _, _, datos in aristas]
    matriz = nx.to_scipy_sparse_array(grafo, nodelist=nodos, weight=atributo, format="csr")

    # Caché acotada: cada vector ocupa unos 97 KB con 12,141 nodos.

    # Calcula y guarda temporalmente las distancias desde una semilla para no repetir el trabajo.
    @lru_cache(maxsize=128)
    def distancias(semilla):
        return dijkstra(matriz, directed=grafo.is_directed(), indices=indice[semilla])

    prior = nx.pagerank(grafo, alpha=0.85, weight="fuerza")
    return {"grafo": grafo, "nodos": nodos, "indice": indice, "nativo": nativo,
            "distancias": distancias, "prior": np.array([prior[n] for n in nodos])}


# Ordena puntuaciones positivas, resuelve empates y retira las palabras excluidas.
def ordenar_consulta(nodos, puntuaciones, excluir):
    excluir = set(excluir)
    puntuaciones = np.asarray(puntuaciones)
    orden = np.argsort(-puntuaciones, kind="stable")
    return [nodos[i] for i in orden
            if np.isfinite(puntuaciones[i]) and puntuaciones[i] > 0 and nodos[i] not in excluir]


# Busca nodos que conecten pares de semillas mediante caminos de bajo costo.
def buscar_subconjunto(contexto, consulta):
    semillas = sorted(set(consulta["semillas"]))
    if len(semillas) < 2:
        return []
    indices = [contexto["indice"][n] for n in semillas]
    puntuaciones = np.asarray(contexto["nativo"].betweenness(
        directed=contexto["grafo"].is_directed(), weights="costo", sources=indices, targets=indices,
    ))
    n = len(contexto["nodos"])
    if n > 2:
        factor = 1.0 if contexto["grafo"].is_directed() else 2.0
        puntuaciones *= factor / ((n - 1) * (n - 2))
    return ordenar_consulta(contexto["nodos"], puntuaciones, consulta["excluir"])


# Favorece candidatos cercanos sumando 1/(1+d) desde las semillas; los inalcanzables no suman.
def buscar_armonica_consulta(contexto, consulta):
    semillas = consulta["semillas"]
    if not semillas:
        return []
    puntuaciones = np.zeros(len(contexto["nodos"]))
    for semilla in semillas:
        distancias = contexto["distancias"](semilla)
        puntuaciones += 1.0 / (1.0 + distancias)
    puntuaciones /= len(semillas)
    return ordenar_consulta(contexto["nodos"], puntuaciones, consulta["excluir"])


# Ajusta el PageRank de la consulta para reducir la ventaja de los nodos populares.
def buscar_pagerank_contrastivo(contexto, consulta):
    if not consulta["semillas"]:
        return []
    personalizacion = dict.fromkeys(contexto["grafo"], 0.0)
    for semilla in consulta["semillas"]:
        personalizacion[semilla] = 1.0 / len(consulta["semillas"])
    ranking = nx.pagerank(contexto["grafo"], alpha=0.85, personalization=personalizacion,
                          weight="fuerza", tol=1e-6, max_iter=100)
    personalizada = np.array([ranking[n] for n in contexto["nodos"]])
    puntuaciones = personalizada / np.sqrt(contexto["prior"])
    return ordenar_consulta(contexto["nodos"], puntuaciones, consulta["excluir"])

