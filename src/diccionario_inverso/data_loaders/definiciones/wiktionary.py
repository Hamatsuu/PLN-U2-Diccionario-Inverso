"""Adaptador de la selección Wiktionary ya preparada y su prueba reservada."""
import pandas as pd
from ...contratos import completar_definiciones


# Carga las definiciones preparadas e identifica por separado la prueba reservada.
def leer_wiktionary(ruta, ids_reservados):
    tabla = pd.read_csv(ruta, dtype={'id': str}).rename(columns={'word': 'objetivo', 'definition': 'definicion'})
    reservada = pd.read_csv(ids_reservados, dtype={'id': str}).id
    tabla.loc[tabla.id.isin(reservada), 'particion'] = 'prueba_reservada'
    return completar_definiciones(tabla, 'Wiktionary preparado')
