"""Orquesta perfiles explícitos de carga usando el constructor común."""
from pathlib import Path
import pandas as pd
from ..data_loaders import cargar_asociaciones
from ..normalizacion import normalizar_asociaciones
from ..rutas import CARPETA
from .construccion import construir_grafo
from .distancias import calcular_distancias, costo_logaritmico


# Construye el perfil histórico NAP aplicando explícitamente sus políticas de conservación.
def grafo_nap_clase(ruta):
    tabla = cargar_asociaciones('nap_clase', ruta=ruta)
    grafo, *_ = construir_grafo(tabla, costo_logaritmico, duplicados='error', conservar_bucles=True,
                                nodos=tabla.attrs['nodos'], ordenar=False, conservar_etiquetas_vacias=True)
    for fila in tabla.itertuples(index=False):
        grafo[fila.estimulo][fila.respuesta]['costo_docente'] = fila.costo_docente
    return calcular_distancias(grafo)


# Carga el perfil de grafo elegido; solo reconstruye y lematiza si se solicita un perfil normalizado.
def cargar_grafo(nombre='nalc', carpeta=CARPETA, nlp=None):
    carpeta = Path(carpeta)
    if nombre == 'nap_clase':
        return grafo_nap_clase(carpeta / 'datos/fuentes/nap/NAP.xls')
    if nombre == 'nalc':
        tabla = cargar_asociaciones('nalc', carpeta, ruta=carpeta / 'datos/grafos/nalc_aristas.csv')
        nodos = pd.read_csv(carpeta / 'datos/grafos/nalc_nodos.csv').nodo
        grafo, *_ = construir_grafo(tabla, costo_logaritmico, duplicados='error', nodos=nodos, ordenar=False)
    elif nombre in ('nap_normalizado', 'nalc_normalizado'):
        if nlp is None:
            raise ValueError('Reconstruir asociaciones requiere nlp explícito.')
        tabla = cargar_asociaciones(nombre.removesuffix('_normalizado'), carpeta)
        tabla = normalizar_asociaciones(tabla, nlp)
        grafo, *_ = construir_grafo(tabla, costo_logaritmico)
    else:
        raise ValueError(f'Grafo desconocido: {nombre}')
    return calcular_distancias(grafo)
