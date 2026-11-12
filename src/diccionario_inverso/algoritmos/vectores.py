"""Vectores unitarios e índices para recuperación por coseno."""
import numpy as np


# Construye el índice de nodos y normaliza los vectores para calcular similitud por coseno.
def preparar_vectores(nodos, vectores):
    matriz = np.asarray(vectores, dtype=np.float64)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    unitarios = np.divide(matriz, normas, out=np.zeros_like(matriz), where=normas > 0)
    return {"nodos": list(nodos), "indice": {n: i for i, n in enumerate(nodos)},
            "vectores": matriz, "unitarios": unitarios}


# Carga vectores ya entrenados desde un archivo NPZ, sin iniciar otro entrenamiento.
def cargar_node2vec(ruta):
    with np.load(ruta, allow_pickle=False) as archivo:
        return preparar_vectores(archivo["nodos"].tolist(), archivo["vectores"])


# Ordena los nodos por similitud con la suma de los vectores de las semillas.
def buscar_node2vec(vectores, consulta):
    indices = [vectores["indice"][p] for p in consulta["semillas"] if p in vectores["indice"]]
    if not indices:
        return []
    suma = vectores["vectores"][indices].sum(axis=0)
    norma = np.linalg.norm(suma)
    if norma == 0:
        return []
    similitudes = np.einsum("ij,j->i", vectores["unitarios"], suma / norma)
    # Los nodos están ordenados alfabéticamente; el orden estable resuelve empates.
    orden = np.argsort(-similitudes, kind="stable")
    excluir = set(consulta["excluir"])
    return [vectores["nodos"][i] for i in orden if vectores["nodos"][i] not in excluir]

