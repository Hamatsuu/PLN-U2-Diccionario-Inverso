"""Constructor genérico: no conoce archivos, corpus ni normas de asociación."""
import networkx as nx
import numpy as np
import pandas as pd
from ..contratos import validar_asociaciones


# Convierte asociaciones comunes en un grafo y audita descartes y colisiones, sin conocer la fuente.
def construir_grafo(tabla, convertir_costo, *, duplicados='media', conservar_bucles=False, nodos=(), ordenar=True, conservar_etiquetas_vacias=False):
    """Asociaciones normalizadas + fuerza→costo; devuelve grafo y tres auditorías.

    Las etiquetas vacías se auditan, no se convierten a nodos. La fuerza y el
    costo son atributos distintos. El costo debe ser finito y positivo.
    """
    if not callable(convertir_costo):
        raise TypeError('convertir_costo debe ser una función fuerza→costo.')
    if duplicados not in ('media', 'ultimo', 'error'):
        raise ValueError('duplicados debe ser media, ultimo o error.')
    tabla = tabla.copy()
    requeridas = {'estimulo', 'respuesta', 'fuerza'}
    if not requeridas.issubset(tabla):
        raise ValueError(f'Se requieren {sorted(requeridas)}')
    validas = tabla[['estimulo', 'respuesta']].map(
        lambda x: isinstance(x, str) and (conservar_etiquetas_vacias or bool(x.strip()))).all(axis=1)
    rechazadas = tabla.loc[~validas].assign(motivo='etiqueta_vacia')
    datos = tabla.loc[validas].copy()
    validar_asociaciones(datos, permitir_etiquetas_vacias=conservar_etiquetas_vacias)
    datos['fuerza'] = pd.to_numeric(datos.fuerza)
    etiquetas = list(dict.fromkeys([*nodos, *datos.estimulo, *datos.respuesta]))
    bucles = datos.estimulo.eq(datos.respuesta)
    retirados = datos.loc[bucles].assign(motivo='autoasociacion') if not conservar_bucles else datos.iloc[:0]
    if not conservar_bucles:
        datos = datos.loc[~bucles]
    pares = ['estimulo', 'respuesta']
    colisiones = datos.loc[datos.duplicated(pares, keep=False)].copy()
    if duplicados == 'error' and not colisiones.empty:
        raise ValueError('Hay pares repetidos.')
    if duplicados == 'media':
        aristas = datos.groupby(pares, as_index=False, sort=ordenar).agg(
            fuerza=('fuerza', 'mean'), registros_originales=('fuerza', 'size'))
    else:
        aristas = datos.drop_duplicates(pares, keep='last').copy()
    aristas['costo'] = aristas.fuerza.map(convertir_costo).astype(float)
    if not (np.isfinite(aristas.costo) & aristas.costo.gt(0)).all():
        raise ValueError('El costo debe ser finito y positivo.')
    grafo = nx.DiGraph()
    grafo.add_nodes_from(sorted(etiquetas) if ordenar else etiquetas)
    for fila in aristas.itertuples(index=False):
        grafo.add_edge(fila.estimulo, fila.respuesta, fuerza=float(fila.fuerza), costo=float(fila.costo))
    return grafo, aristas, colisiones, pd.concat([rechazadas, retirados], ignore_index=True)
