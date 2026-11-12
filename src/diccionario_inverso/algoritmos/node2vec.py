"""Caminatas de segundo orden y entrenamiento reproducible con un trabajador."""
import time
import zlib
import numpy as np
from .vectores import preparar_vectores


# Asigna probabilidades de transición según la fuerza de las aristas y los sesgos p y q.
def probabilidades_node2vec(grafo, actual, anterior=None, p=1.0, q=1.0):
    if not (np.isfinite(p) and np.isfinite(q) and p > 0 and q > 0):
        raise ValueError("p y q deben ser positivos y finitos.")
    vecinos = sorted(grafo.successors(actual))
    if not vecinos:
        return vecinos, np.array([], dtype=float)
    pesos = np.array([grafo[actual][vecino]["fuerza"] for vecino in vecinos], dtype=float)
    if anterior is not None:
        pesos *= [1 / p if vecino == anterior else 1.0 if grafo.has_edge(anterior, vecino) else 1 / q
                  for vecino in vecinos]
    return vecinos, pesos / pesos.sum()


# Genera recorridos aleatorios reproducibles que servirán para aprender vectores del grafo.
def generar_caminatas_node2vec(grafo, longitud, caminatas, p, q, semilla):
    if longitud < 1 or caminatas < 1:
        raise ValueError("La longitud y el número de caminatas deben ser positivos.")
    if not (np.isfinite(p) and np.isfinite(q) and p > 0 and q > 0):
        raise ValueError("p y q deben ser positivos y finitos.")
    rng = np.random.default_rng(semilla)
    nodos = sorted(grafo)
    cache = {}
    recorridos = []
    for _ in range(caminatas):
        for inicio in rng.permutation(nodos):
            camino = [str(inicio)]
            while len(camino) < longitud:
                actual = camino[-1]
                anterior = camino[-2] if len(camino) > 1 else None
                clave = (anterior, actual)
                if clave not in cache:
                    cache[clave] = probabilidades_node2vec(grafo, actual, anterior, p, q)
                vecinos, probabilidades = cache[clave]
                if not vecinos:
                    break
                camino.append(vecinos[int(rng.choice(len(vecinos), p=probabilidades))])
            recorridos.append(camino)
    return recorridos


# Produce el mismo hash en cada ejecución para mantener reproducible el entrenamiento.
def hash_estable(texto):
    return zlib.crc32(texto.encode("utf-8"))


# Entrena skip-gram sobre las caminatas y registra sus tiempos de preparación y entrenamiento.
def entrenar_node2vec(grafo, configuracion, semilla):
    from gensim.models import Word2Vec

    inicio = time.perf_counter()
    recorridos = generar_caminatas_node2vec(
        grafo, configuracion["longitud"], configuracion["caminatas"],
        configuracion["p"], configuracion["q"], semilla,
    )
    segundos_caminatas = time.perf_counter() - inicio
    inicio = time.perf_counter()
    modelo = Word2Vec(
        sentences=recorridos, vector_size=configuracion["dimension"], window=5,
        min_count=1, sg=1, negative=5, sample=0, epochs=5,
        workers=1, seed=semilla, sorted_vocab=1, hashfxn=hash_estable,
    )
    segundos_entrenamiento = time.perf_counter() - inicio
    nodos = sorted(modelo.wv.index_to_key)
    datos = preparar_vectores(nodos, np.vstack([modelo.wv[nodo] for nodo in nodos]))
    datos["segundos_caminatas"] = segundos_caminatas
    datos["segundos_entrenamiento"] = segundos_entrenamiento
    return datos

