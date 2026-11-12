"""Enrutamiento de fuentes; todos los adaptadores devuelven el mismo contrato."""
from pathlib import Path
from .rutas import CARPETA
from .data_loaders.definiciones.corpus_clase import leer_corpus_clase
from .data_loaders.definiciones.wordnet import leer_preparado_wordnet
from .data_loaders.definiciones.wiktionary import leer_wiktionary
from .data_loaders.definiciones.equipo import leer_equipo
from .data_loaders.definiciones.csv import leer_csv

PARTICIONES_PREDETERMINADAS = {
    'wordnet': 'desarrollo',
    'wiktionary': 'desarrollo',
    'corpus_clase': 'benchmark_docente',
    'equipo': 'complemento_manual',
    'csv': 'exploratorio',
}
DATASETS_DISPONIBLES = tuple(PARTICIONES_PREDETERMINADAS)


# Elige una partición compatible con la fuente, sin seleccionar nunca prueba por defecto.
def particion_predeterminada(nombre):
    if nombre not in PARTICIONES_PREDETERMINADAS:
        raise ValueError(f'Dataset desconocido: {nombre}. Disponibles: {DATASETS_DISPONIBLES}')
    return PARTICIONES_PREDETERMINADAS[nombre]


# Elige el loader de definiciones solicitado y devuelve una tabla con el contrato común.
def cargar_dataset(nombre, grafo='nalc', carpeta=CARPETA, ruta=None):
    carpeta = Path(carpeta)
    if nombre == 'wordnet':
        if grafo not in ('nalc', 'nap_clase'):
            raise ValueError('WordNet preparado solo es compatible con nalc o nap_clase; use un CSV para otro grafo.')
        prefijo = 'nap' if grafo == 'nap_clase' else 'nalc'
        return leer_preparado_wordnet(carpeta / f'datos/preparados/{prefijo}_wordnet.jsonl', grafo)
    if nombre == 'corpus_clase':
        auditoria = carpeta / 'datos/preparados/corpus_consultas.jsonl' if grafo == 'nap_clase' else None
        return leer_corpus_clase(carpeta / 'datos/fuentes/corpus_clase', auditoria)
    if nombre == 'wiktionary':
        return leer_wiktionary(carpeta / 'datos/preparados/wiktionary.csv', carpeta / 'datos/preparados/ids_prueba_reservada.csv')
    if nombre == 'equipo':
        return leer_equipo(carpeta / 'datos/fuentes/equipo.csv')
    if nombre == 'csv':
        if ruta is None:
            raise ValueError('El dataset csv necesita la ruta del archivo en ruta o ruta_csv.')
        return leer_csv(ruta)
    raise ValueError(f'Dataset desconocido: {nombre}. Disponibles: {DATASETS_DISPONIBLES}')
