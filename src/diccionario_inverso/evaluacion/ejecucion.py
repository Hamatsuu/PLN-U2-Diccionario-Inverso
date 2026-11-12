"""Evaluador ajeno a grafos, fuentes y procesamiento lingüístico."""
import time
import pandas as pd
from ..contratos import validar_definiciones
from .metricas import metricas_ranking


# Ejecuta una búsqueda por definición y compara cada ranking con el objetivo y sus alias.
def evaluar(dataset, buscar):
    """Ejecuta buscar(definicion: str) -> list[str] y devuelve detalle y resumen.

    Solo el texto entra en la búsqueda. consulta_ms mide la llamada completa,
    incluido el preprocesamiento que decida capturar el callable. La cobertura
    es una auditoría opcional del dataset, no se infiere del ranking.
    """
    validar_definiciones(dataset)
    if dataset.empty:
        raise ValueError('No hay consultas para evaluar.')
    if not callable(buscar):
        raise TypeError('buscar debe ser callable.')

    # El buscador solo recibe la definición: objetivo y alias se reservan para puntuar el resultado.
    filas = []
    for fila in dataset.to_dict('records'):
        inicio = time.perf_counter()
        ranking = buscar(fila['definicion'])
        ms = (time.perf_counter() - inicio) * 1000
        if not isinstance(ranking, list) or not all(isinstance(p, str) for p in ranking):
            raise ValueError('La búsqueda debe devolver list[str].')
        if len(ranking) != len(set(ranking)):
            raise ValueError('El ranking no debe tener duplicados.')
        filas.append({**fila, 'top5': ranking[:5], 'longitud_ranking': len(ranking),
                      'consulta_ms': ms, **metricas_ranking(fila['objetivo'], ranking, fila.get('alias', []))})

    # Agrega todas las consultas, incluidos los rankings vacíos, para no inflar los aciertos.
    detalle = pd.DataFrame(filas)
    resumen = {col: detalle[col].mean() for col in [f'hit@{k}{s}' for k in (1, 3, 5) for s in ('', '_alias')]}
    resumen.update(n=len(detalle), conceptos=detalle.objetivo.nunique(), MRR=detalle.RR.mean(),
                   MRR_alias=detalle.RR_alias.mean(),
                   cobertura=detalle.cubierta.mean() if 'cubierta' in detalle else float('nan'),
                   consulta_ms_promedio=detalle.consulta_ms.mean(), consulta_ms_mediana=detalle.consulta_ms.median(),
                   consulta_ms_p95=detalle.consulta_ms.quantile(.95), rankings_vacios=int(detalle.longitud_ranking.eq(0).sum()))
    for k in (1, 3, 5):
        resumen[f'macro_hit@{k}'] = detalle.groupby('objetivo')[f'hit@{k}'].mean().mean()
    return detalle, resumen
