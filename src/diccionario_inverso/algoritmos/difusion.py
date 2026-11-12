"""PageRank personalizado y distancias desde las semillas."""
import networkx as nx


# Difunde importancia desde las semillas y devuelve candidatos que no aparezcan en la descripción.
def buscar_pagerank(grafo, consulta, alpha=0.85):
    semillas = consulta["semillas"]
    if not semillas:
        return []

    # Cada semilla empieza con la misma importancia.
    pesos = {palabra: 1 / len(semillas) for palabra in semillas}

    # Calcular PageRank. Los nodos sin salidas devuelven su importancia a las semillas.
    puntuaciones = nx.pagerank(
        grafo,
        personalization=pesos,
        dangling=pesos,
        weight="fuerza",
        alpha=alpha,
        max_iter=1000,
        tol=1e-8,
    )

    # Ordenar de mayor a menor puntuación y, en empate, alfabéticamente.
    ordenadas = sorted(puntuaciones, key=lambda palabra: (-puntuaciones[palabra], palabra))

    # No devolver palabras que ya están en la descripción.
    excluir = set(consulta["excluir"])
    return [palabra for palabra in ordenadas if palabra not in excluir]


# Ordena candidatos por el costo mínimo de llegar a ellos desde alguna semilla.
def buscar_distancia(grafo, consulta, atributo):
    """Ordena las palabras por el costo mínimo desde las semillas.

    atributo: "costo_inverso", "costo_log" o el "costo" del constructor.
    """
    semillas = consulta["semillas"]
    if not semillas:
        return []

    # Calcular el costo mínimo desde todas las semillas a la vez.
    # Solo sigue aristas en su dirección, igual que PageRank.
    distancias = nx.multi_source_dijkstra_path_length(grafo, semillas, weight=atributo)

    # Costo más bajo primero; en empate, orden alfabético.
    ordenadas = sorted(distancias, key=lambda palabra: (distancias[palabra], palabra))

    # No devolver palabras de la propia descripción.
    excluir = set(consulta["excluir"])
    return [palabra for palabra in ordenadas if palabra not in excluir]

