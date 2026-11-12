"""Comparaciones de lectura; conserva por separado las variantes y las pruebas adicionales."""
import json
from pathlib import Path
import pandas as pd
from .rutas import CARPETA
from .experimentos import cargar_ejecucion


# Lee solo ejecuciones completas y verifica que los tres modelos compartan exactamente ids y textos.
def cargar_matriz_baseline(carpeta=CARPETA):
    carpeta = Path(carpeta)
    indice = json.loads((carpeta / 'resultados/baseline_docente.json').read_text())
    tablas = []
    for entrada in indice['ejecuciones']:
        resumen, detalle, _ = cargar_ejecucion(carpeta / entrada['ruta'])
        poblaciones = [grupo[['id', 'objetivo', 'definicion']].sort_values('id').reset_index(drop=True)
                       for _, grupo in detalle.groupby('modelo')]
        if len(poblaciones) != 3 or not all(poblaciones[0].equals(p) for p in poblaciones[1:]):
            raise ValueError('La comparación requiere los mismos ids, objetivos y textos.')
        tablas.append(resumen)
    return pd.concat(tablas, ignore_index=True)


# Reúne todas las configuraciones históricas y el baseline en poblaciones compatibles.
def comparaciones_completas(historicos, matriz):
    propios = historicos.loc[~historicos.modelo.str.startswith('clase_')].copy()
    baseline = matriz.loc[matriz.modelo.str.startswith('Baseline docente')].copy()
    claves = ['grafo', 'dataset', 'particion', 'n']
    # Equipo y las combinaciones nuevas se presentan en la matriz pareada, no se empalman al histórico.
    compatibles = propios.loc[~propios.dataset.eq('equipo'), claves].drop_duplicates()
    baseline = baseline.merge(compatibles, on=claves, how='inner')
    return pd.concat([propios, baseline], ignore_index=True)


# Muestra una configuración por familia sin elegirla por los resultados de prueba.
def comparaciones_principales(historicos, matriz):
    completas = comparaciones_completas(historicos, matriz)
    # Regla de lectura: reducido, costo log y local64. No es una nueva selección de modelos.
    nap = {
        'nuestro_pagerank', 'nuestro_grado_reducido',
        'nuestro_cercania_reducido_dist_log', 'nuestro_intermediacion_reducido_dist_log',
        'nuestro_node2vec_local64',
    }
    nalc = {'PageRank', 'Grado ponderado reducido', 'Cercanía -log FSG reducido', 'node2vec local64'}
    mascara = (completas.modelo.str.startswith('Baseline docente')
               | (completas.grafo.eq('nap_clase') & completas.modelo.isin(nap))
               | (completas.grafo.eq('nalc') & completas.modelo.isin(nalc)))
    # En desarrollo mostramos la intermediación clásica. Las pruebas solo guardaron la variante entre pistas.
    mascara |= (completas.grafo.eq('nalc')
                & ((completas.particion.eq('desarrollo') & completas.modelo.eq('Intermediación -log FSG reducido'))
                   | (~completas.particion.eq('desarrollo') & completas.modelo.eq('Subconjunto no dirigido'))))
    return completas.loc[mascara].copy()
