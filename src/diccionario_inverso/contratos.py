"""Contratos tabulares compartidos. Validar no transforma ni descarta registros."""
import numpy as np
import pandas as pd

ASOCIACIONES = ('estimulo', 'respuesta', 'fuerza')
DEFINICIONES = ('id', 'objetivo', 'definicion')


# Comprueba que la entrada sea una tabla con las columnas necesarias, sin nombres repetidos.
def _columnas(tabla, columnas):
    if not isinstance(tabla, pd.DataFrame):
        raise TypeError('Se requiere un DataFrame.')
    faltan = set(columnas) - set(tabla.columns)
    if faltan:
        raise ValueError(f'Faltan columnas del contrato: {sorted(faltan)}')
    if tabla.columns.duplicated().any():
        raise ValueError('Hay columnas repetidas.')


# Verifica que las columnas indicadas contengan textos no vacíos.
def _textos(tabla, columnas):
    for columna in columnas:
        if not tabla[columna].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
            raise ValueError(f'{columna} debe contener textos no vacíos.')


# Valida los extremos de cada asociación y que su fuerza esté en (0, 1].
def validar_asociaciones(tabla, *, permitir_etiquetas_vacias=False):
    _columnas(tabla, ASOCIACIONES)
    if permitir_etiquetas_vacias:
        if not tabla[['estimulo', 'respuesta']].map(lambda x: isinstance(x, str)).all().all():
            raise ValueError('Las etiquetas deben ser str incluso en el perfil histórico.')
    else:
        _textos(tabla, ('estimulo', 'respuesta'))
    fuerza = pd.to_numeric(tabla.fuerza, errors='raise')
    if not (np.isfinite(fuerza) & fuerza.gt(0) & fuerza.le(1)).all():
        raise ValueError('fuerza debe ser finita y estar en (0, 1].')
    return tabla


# Valida los textos, la unicidad de los ids y el formato de alias y particiones.
def validar_definiciones(tabla):
    _columnas(tabla, DEFINICIONES)
    _textos(tabla, DEFINICIONES)
    if tabla.id.duplicated().any():
        raise ValueError('Los ids deben ser únicos.')
    if 'alias' in tabla:
        if not tabla.alias.map(lambda x: isinstance(x, list) and all(isinstance(a, str) and a.strip() for a in x)).all():
            raise ValueError('alias debe ser una lista de textos por fila.')
    if 'particion' in tabla:
        _textos(tabla, ('particion',))
    return tabla


# Añade los metadatos que falten y valida la tabla sin cambiar sus definiciones.
def completar_definiciones(tabla, fuente, particion='exploratorio'):
    tabla = tabla.copy()
    if 'alias' not in tabla:
        tabla['alias'] = [[] for _ in range(len(tabla))]
    if 'fuente' not in tabla:
        tabla['fuente'] = fuente
    if 'particion' not in tabla:
        tabla['particion'] = particion
    return validar_definiciones(tabla)
