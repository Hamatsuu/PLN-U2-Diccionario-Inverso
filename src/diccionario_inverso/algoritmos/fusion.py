"""Fusión de rankings sin entrenamiento con las respuestas."""
from .contexto import buscar_armonica_consulta
from .semantica import buscar_semantica


# Combina rankings sumando 1/(k+posición) por candidato, sin ajustar pesos con las respuestas.
def fusion_rrf(rankings, k=60):
    puntuaciones = {}
    for ranking in rankings:
        for posicion, palabra in enumerate(ranking, start=1):
            puntuaciones[palabra] = puntuaciones.get(palabra, 0.0) + 1.0 / (k + posicion)
    return sorted(puntuaciones, key=lambda palabra: (-puntuaciones[palabra], palabra))


# Fusiona la cercanía armónica no dirigida y la similitud semántica con RRF.
def buscar_fusion(contexto_no_dirigido, semantica, consulta):
    return fusion_rrf([
        buscar_armonica_consulta(contexto_no_dirigido, consulta),
        buscar_semantica(semantica, consulta),
    ], k=60)

