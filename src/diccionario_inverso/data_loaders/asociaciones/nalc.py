"""NALC: nombres originales a estímulo, respuesta y fuerza."""
import pandas as pd
from ...contratos import validar_asociaciones


# Adapta las columnas del CSV NALC al contrato común de asociaciones.
def leer_nalc(ruta):
    tabla = pd.read_csv(ruta, encoding='utf-8-sig', float_precision='round_trip')
    tabla = tabla.rename(columns={'CUE': 'estimulo', 'TARGET': 'respuesta', 'FSG': 'fuerza'})
    return validar_asociaciones(tabla[['estimulo', 'respuesta', 'fuerza']].assign(fuente=str(ruta)))
