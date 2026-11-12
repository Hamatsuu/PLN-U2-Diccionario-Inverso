"""Las 49 descripciones manuales; correcciones ortográficas solo del objetivo."""
import pandas as pd
from ...contratos import completar_definiciones
from ...normalizacion import normalizar_superficie


# Carga las definiciones manuales del equipo y corrige solo la ortografía de sus objetivos.
def leer_equipo(ruta):
    tabla = pd.read_csv(ruta)
    correcciones = {'lapiz': 'lápiz', 'telefono': 'teléfono', 'musica': 'música', 'rio': 'río', 'medico': 'médico'}
    resultado = pd.DataFrame(dict(id=[f'equipo_{i:02d}' for i in range(1, len(tabla)+1)],
                                  objetivo=tabla.concepto.replace(correcciones).map(normalizar_superficie),
                                  definicion=tabla.definicion))
    return completar_definiciones(resultado, 'equipo: 49 definiciones manuales', 'complemento_manual')
