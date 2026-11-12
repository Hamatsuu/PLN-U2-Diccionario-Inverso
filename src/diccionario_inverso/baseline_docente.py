"""Único baseline docente: protocolo publicado, sin ajustes por dataset."""
from functools import lru_cache
from pathlib import Path
import string
import networkx as nx
from .busqueda import crear_busqueda
from .normalizacion import cargar_nlp


# Prepara texto con el orden de operaciones original y sin consultar respuestas correctas.
def crear_preparador_docente(grafo, carpeta, nlp=None):
    nlp = nlp or cargar_nlp('es_core_news_sm')
    stopwords = set((Path(carpeta) / 'datos/baseline_docente/stopwords_spanish.txt').read_text().splitlines())

    # Reutiliza la lematización por palabra sin cambiar el procesamiento independiente de cada token.
    @lru_cache(maxsize=32768)
    def lema(palabra):
        return nlp(palabra)[0].lemma_

    # Elimina puntuación ASCII, filtra stopwords antes de lematizar y conserva semillas repetidas.
    def preparar(texto):
        for caracter in string.punctuation:
            texto = texto.replace(caracter, '')
        lemas = ''.join(lema(p) + ' ' for p in texto.strip().split() if p not in stopwords).lower().split(' ')
        semillas = [p for p in lemas if p and p in grafo]
        return dict(lemas=lemas, semillas=semillas, excluir=list(semillas),
                    fuera_vocabulario=[p for p in lemas if p not in grafo], cubierta=bool(semillas))

    return preparar


# Conserva costos exactos NAP; en otros grafos promedia fuerzas observadas de cada pareja no dirigida.
def preparar_grafo_docente(grafo):
    vista = nx.Graph()
    vista.add_nodes_from(grafo)
    fuerzas = {}
    for a, b, d in grafo.edges(data=True):
        clave = frozenset((a, b))
        if clave not in fuerzas:
            fuerzas[clave] = (a, b, [])
        fuerzas[clave][2].append(d)
    for a, b, datos in fuerzas.values():
        exactos = [d['costo_docente'] for d in datos if 'costo_docente' in d]
        costo = exactos[0] if exactos else 100 * (1 - sum(d['fuerza'] for d in datos) / len(datos))
        if costo < 0:
            raise ValueError('El costo docente debe ser no negativo.')
        vista.add_edge(a, b, costo_docente=costo)
    return vista


# Ordena por cercanía ponderada del subgrafo inducido y aplica el corte antes de filtrar semillas.
def buscar_cercania_docente(grafo, consulta):
    semillas = consulta['semillas']
    if not semillas:
        return []
    incluidos = set(semillas)
    for semilla in semillas:
        incluidos.update(grafo[semilla])
    subgrafo = nx.Graph()
    subgrafo.add_nodes_from(n for n in grafo if n in incluidos)
    subgrafo.add_edges_from((a, b, d) for a, b, d in grafo.edges(data=True) if a in incluidos and b in incluidos)
    valores = nx.closeness_centrality(subgrafo, distance='costo_docente')
    ranking = sorted(valores.items(), key=lambda par: par[1], reverse=True)[:99]
    return [str(n) for n, valor in ranking if n not in semillas and valor > 0]


# Compone el baseline como búsqueda pública de texto con sus propios recursos lingüísticos.
def construir_baseline_docente(grafo, carpeta):
    from functools import partial
    vista = preparar_grafo_docente(grafo)
    preparar = crear_preparador_docente(vista, carpeta)
    return crear_busqueda(partial(buscar_cercania_docente, vista), preparar), preparar
