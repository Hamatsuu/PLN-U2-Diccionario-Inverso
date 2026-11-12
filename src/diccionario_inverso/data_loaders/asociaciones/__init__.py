"""Selección de asociaciones por nombre; todos los lectores comparten contrato."""
from pathlib import Path
from ...rutas import CARPETA
from .nalc import leer_nalc
from .nap import leer_nap, leer_nap_clase

FUENTES_ASOCIACIONES = ('nap', 'nalc', 'nap_clase')


# Selecciona el lector y la ruta por nombre, sin que el llamador importe un adaptador específico.
def cargar_asociaciones(nombre, carpeta=CARPETA, ruta=None):
    lectores = {
        'nap': (leer_nap, 'datos/fuentes/nap/NAP.xls'),
        'nalc': (leer_nalc, 'datos/fuentes/nalc/asociaciones.csv'),
        'nap_clase': (leer_nap_clase, 'datos/fuentes/nap/NAP.xls'),
    }
    if nombre not in lectores:
        raise ValueError(f'Fuente de asociaciones desconocida: {nombre}. Disponibles: {FUENTES_ASOCIACIONES}')
    leer, predeterminada = lectores[nombre]
    return leer(Path(ruta) if ruta is not None else Path(carpeta) / predeterminada)
