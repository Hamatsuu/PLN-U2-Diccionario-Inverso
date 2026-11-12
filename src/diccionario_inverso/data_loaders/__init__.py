"""Entradas públicas: elegir la fuente por nombre, no por import específico."""
from ..rutas import CARPETA
from .asociaciones import cargar_asociaciones, FUENTES_ASOCIACIONES


# Selecciona una fuente de definiciones usando el enrutador común de datasets.
def cargar_definiciones(nombre, grafo='nalc', carpeta=CARPETA, ruta=None):
    # El import local evita un ciclo al cargar los adaptadores de definiciones.
    from ..datasets import cargar_dataset
    return cargar_dataset(nombre, grafo=grafo, carpeta=carpeta, ruta=ruta)
