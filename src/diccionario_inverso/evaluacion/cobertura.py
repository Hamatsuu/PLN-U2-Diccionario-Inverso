"""Resumen de auditorías de preprocesamiento, separado del evaluador."""


# Resume por partición cuántas descripciones tienen semillas y cuánto texto contienen.
def resumir_cobertura(datos):
    tabla = datos.copy()
    tabla['semillas_n'] = tabla.semillas.map(len)
    tabla['longitud'] = tabla.definicion.str.split().map(len)
    return tabla.groupby('particion', dropna=False).agg(
        n=('id', 'size'), conceptos=('objetivo', 'nunique'),
        cobertura=('semillas_n', lambda s: s.gt(0).mean()),
        semillas_promedio=('semillas_n', 'mean'), semillas_mediana=('semillas_n', 'median'),
        palabras_mediana=('longitud', 'median')).reset_index()

