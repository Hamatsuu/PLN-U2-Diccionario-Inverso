"""CSV de usuario: contrato común o adaptación explícita del esquema anterior."""
import json
import pandas as pd
from ...contratos import completar_definiciones
from ...normalizacion import normalizar_superficie


# Adapta un CSV de definiciones nuevas o del formato anterior al contrato común.
def leer_csv(ruta):
    tabla = pd.read_csv(ruta, dtype={'id': str})
    # Solo este adaptador conoce los nombres del formato anterior.
    tabla = tabla.rename(columns={'word': 'objetivo', 'definition': 'definicion'})
    if 'objetivo' in tabla:
        tabla['objetivo'] = tabla.objetivo.map(lambda x: normalizar_superficie(x) if isinstance(x, str) else x)
    if 'alias' in tabla:
        tabla['alias'] = tabla.alias.map(lambda x: [] if pd.isna(x) else json.loads(x))
        tabla['alias'] = tabla.alias.map(lambda a: [normalizar_superficie(x) for x in a] if isinstance(a, list) else a)
    return completar_definiciones(tabla, str(ruta))
