"""Coseno de vectores españoles preentrenados de las semillas."""
import numpy as np
from .contexto import ordenar_consulta


# Prepara los vectores spaCy de los nodos y sus versiones unitarias para comparar por coseno.
def preparar_semantica(nlp, nodos):
    nodos = sorted(nodos)
    vectores = np.asarray([nlp.make_doc(n.replace("_", " ")).vector for n in nodos], dtype=np.float64)
    normas = np.linalg.norm(vectores, axis=1, keepdims=True)
    unitarios = np.divide(vectores, normas, out=np.zeros_like(vectores), where=normas > 0)
    return {"nodos": nodos, "indice": {n: i for i, n in enumerate(nodos)},
            "vectores": vectores, "unitarios": unitarios}


# Combina los vectores de las semillas y busca nodos con una orientación semántica similar.
def buscar_semantica(semantica, consulta):
    if not consulta["semillas"]:
        return []
    indices = [semantica["indice"][n] for n in consulta["semillas"]]
    vector = semantica["vectores"][indices].sum(axis=0)
    norma = np.linalg.norm(vector)
    if norma == 0:
        return []
    puntuaciones = np.einsum("ij,j->i", semantica["unitarios"], vector / norma)
    return ordenar_consulta(semantica["nodos"], puntuaciones, consulta["excluir"])

