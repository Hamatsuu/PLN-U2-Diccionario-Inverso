"""Caracterización estructural; no carga fuentes ni construye asociaciones."""
import time
import networkx as nx
import pandas as pd


# Resume tamaño, grados, componentes y agrupamiento en cuatro tablas para analizar el grafo.
def caracterizar_grafo(grafo):
    if not grafo:
        raise ValueError("El grafo debe tener al menos un nodo.")

    inicio = time.perf_counter()
    n = grafo.number_of_nodes()

    # Una fila por nodo; los aislados también cuentan en los promedios.
    nodos = sorted(grafo.nodes())
    grados = pd.DataFrame({
        "nodo": nodos,
        "entrada": [grafo.in_degree(nodo) for nodo in nodos],
        "salida": [grafo.out_degree(nodo) for nodo in nodos],
    })
    grados["total"] = grados["entrada"] + grados["salida"]

    resumen = {
        "nodos": n,
        "aristas": grafo.number_of_edges(),
        "grado_medio_entrada": grados["entrada"].mean(),
        "grado_medio_salida": grados["salida"].mean(),
        "grado_medio_total": grados["total"].mean(),
    }

    # Una fila por componente, ordenadas de mayor a menor tamaño.
    tablas_componentes = []
    for tipo, grupos in (
        ("debiles", nx.weakly_connected_components(grafo)),
        ("fuertes", nx.strongly_connected_components(grafo)),
    ):
        tamanos = sorted((len(grupo) for grupo in grupos), reverse=True)
        tablas_componentes.append(pd.DataFrame({
            "tipo": tipo,
            "componente": range(1, len(tamanos) + 1),
            "nodos": tamanos,
            "proporcion": [tamano / n for tamano in tamanos],
        }))
        resumen[f"componentes_{tipo}"] = len(tamanos)
        resumen[f"mayor_componente_{tipo}"] = tamanos[0]
    componentes = pd.concat(tablas_componentes, ignore_index=True)

    # Distribuciones separadas de grado de entrada, salida y total.
    tablas_distribucion = []
    for tipo in ("entrada", "salida", "total"):
        conteos = grados[tipo].value_counts().sort_index().rename_axis("grado").reset_index(name="nodos")
        conteos["tipo"] = tipo
        conteos["proporcion"] = conteos["nodos"] / n
        tablas_distribucion.append(conteos[["tipo", "grado", "nodos", "proporcion"]])
    distribucion = pd.concat(tablas_distribucion, ignore_index=True)

    resumen["agrupamiento_dirigido_sin_peso"] = nx.average_clustering(grafo, weight=None, count_zeros=True)
    resumen["segundos_calculo"] = time.perf_counter() - inicio
    return pd.DataFrame([resumen]), componentes, grados, distribucion

