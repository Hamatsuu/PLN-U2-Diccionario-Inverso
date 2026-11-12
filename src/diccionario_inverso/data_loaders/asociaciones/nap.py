"""Dos adaptadores NAP explícitos: normalizado y reproducción docente."""
import networkx as nx
import pandas as pd
import xlrd
from ...contratos import validar_asociaciones


# Lee etiquetas de la columna 0 del Excel NAP y divide la fuerza de la columna 3 entre 100.
def leer_nap(ruta):
    tabla = pd.read_excel(ruta, header=None)
    estimulo, filas = None, []
    for i in range(len(tabla)):
        respuesta = tabla.iat[i, 0]
        if respuesta == '======':
            estimulo = tabla.iat[i + 1, 0] if i + 1 < len(tabla) else None
            continue
        fuerza = pd.to_numeric(tabla.iat[i, 3], errors='coerce')
        if pd.notna(estimulo) and pd.notna(respuesta) and pd.notna(fuerza) and 0 < fuerza <= 100:
            filas.append(dict(estimulo=str(estimulo), respuesta=str(respuesta), fuerza=fuerza / 100))
    return validar_asociaciones(pd.DataFrame(filas, columns=['estimulo', 'respuesta', 'fuerza']).assign(fuente=str(ruta)))


# Reproduce la lectura docente de NAP, conservando sus etiquetas y la sobrescritura no dirigida.
def leer_nap_clase(ruta):
    """Adapta columna 4 y sobrescritura no dirigida del histórico a arcos comunes.

    El Graph temporal reproduce el orden y la política del archivo docente.
    No lematiza, no elimina los dos bucles y no promedia duplicados.
    """
    hoja = xlrd.open_workbook(str(ruta)).sheet_by_index(0)
    historico = nx.Graph()
    estimulo = ''
    for fila in range(hoja.nrows - 1):
        marca = hoja.cell_value(fila, 0)
        if marca == '======':
            estimulo = hoja.cell_value(fila + 1, 4)
        elif marca not in ('--PALABRAS--', '', '=') and hoja.cell_value(fila, 2) != '':
            peso = 100 - float(hoja.cell_value(fila, 3))
            historico.add_edge(str(estimulo).strip(), str(hoja.cell_value(fila, 4)).strip(), fuerza=(100 - peso) / 100, costo_docente=peso)
    filas = [(a, b, d['fuerza'], d['costo_docente']) for a, b, d in historico.to_directed().edges(data=True)]
    tabla = pd.DataFrame(filas, columns=['estimulo', 'respuesta', 'fuerza', 'costo_docente']).assign(fuente=str(ruta))
    tabla.attrs['nodos'] = list(historico)
    # El histórico incluye un estímulo vacío (69 asociaciones); conservarlo es
    # necesario para reproducir sus 4239 nodos, no una regla para datos nuevos.
    return validar_asociaciones(tabla, permitir_etiquetas_vacias=True)
