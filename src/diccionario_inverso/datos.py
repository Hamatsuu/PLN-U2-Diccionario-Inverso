"""Compatibilidad de imports anteriores. Los lectores viven en data_loaders/.

Los DataFrames usan ahora los contratos de contratos.py, no word/definition
ni CUE/TARGET/FSG. El runtime importa los módulos responsables directamente.
"""
from .rutas import CARPETA
from .normalizacion.recursos import cargar_nlp
from .datasets import cargar_dataset
from .grafos.carga import cargar_grafo, grafo_nap_clase
from .data_loaders.asociaciones.nalc import leer_nalc
from .data_loaders.asociaciones.nap import leer_nap
from .data_loaders.definiciones.corpus_clase import leer_corpus_clase
from .data_loaders.definiciones.wordnet import leer_wordnet
