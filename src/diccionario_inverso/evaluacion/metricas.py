"""Métricas de recuperación y sus intervalos descriptivos."""
import numpy as np


# Calcula la posición, los aciertos Hit@k y el rango recíproco, con y sin aceptación de alias.
def metricas_ranking(objetivo, ranking, alias=()):
    posicion = ranking.index(objetivo) + 1 if objetivo in ranking else None
    aceptadas = set(alias) | {objetivo}
    posicion_alias = next((i for i, palabra in enumerate(ranking, 1) if palabra in aceptadas), None)
    return {
        'posicion': posicion, 'posicion_alias': posicion_alias,
        **{f'hit@{k}': int(posicion is not None and posicion <= k) for k in (1, 3, 5)},
        **{f'hit@{k}_alias': int(posicion_alias is not None and posicion_alias <= k) for k in (1, 3, 5)},
        'RR': 1 / posicion if posicion else 0., 'RR_alias': 1 / posicion_alias if posicion_alias else 0.,
    }


# Estima un intervalo descriptivo para una proporción de aciertos.
def intervalo_wilson(aciertos, n, z=1.959963984540054):
    if n <= 0:
        return np.nan, np.nan
    p = aciertos / n
    centro = (p + z*z / (2*n)) / (1 + z*z/n)
    radio = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return max(0., centro-radio), min(1., centro+radio)

