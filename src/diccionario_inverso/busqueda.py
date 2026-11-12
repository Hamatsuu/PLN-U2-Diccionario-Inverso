"""Composición pública texto→ranking e importación explícita de consultas históricas."""
from copy import deepcopy


# Une un preparador de texto y un algoritmo de semillas en una búsqueda pública texto→ranking.
def crear_busqueda(algoritmo, preparar_texto):
    # Prepara la descripción, ejecuta el algoritmo y comprueba que no devuelva términos excluidos.
    def buscar(definicion: str) -> list[str]:
        if not isinstance(definicion, str):
            raise TypeError('buscar recibe una definición str, no una fila ni un diccionario.')
        consulta = preparar_texto(definicion)
        ranking = algoritmo({'semillas': list(consulta['semillas']), 'excluir': list(consulta['excluir'])})
        if set(ranking) & set(consulta['excluir']):
            raise ValueError('El ranking contiene palabras de la descripción excluidas.')
        return ranking

    return buscar


# Prepara la reproducción histórica por texto, sin capturar objetivos, ids ni alias.
def preparar_reproduccion(consultas, vocabulario):
    """Indexa SOLO texto, semillas y exclusiones de una auditoría histórica.

    Conserva el preprocesamiento original sin introducir objetivo, id o alias
    en la búsqueda. Textos iguales con consultas distintas son ambiguos:
    se rechazan, en vez de elegir por id o por respuesta correcta.
    """
    indice = {}
    for fila in consultas[['definicion', 'semillas', 'excluir']].to_dict('records'):
        texto = fila.pop('definicion')
        if not isinstance(texto, str):
            raise ValueError('La definición histórica debe ser str.')
        if not all(isinstance(fila[k], list) and all(isinstance(x, str) for x in fila[k]) for k in fila):
            raise ValueError('Semillas y exclusiones deben ser listas de textos.')
        if not set(fila['semillas']).issubset(vocabulario):
            raise ValueError('Las semillas preparadas no pertenecen a este grafo.')
        if texto in indice and indice[texto] != fila:
            raise ValueError('Texto histórico ambiguo: active repreparar_consultas para normalizar desde texto.')
        indice[texto] = deepcopy(fila)

    # Recupera una copia de la consulta histórica del texto y rechaza los textos desconocidos.
    def preparar(texto):
        if texto not in indice:
            raise ValueError('Texto sin auditoría histórica; use un preparador lingüístico para consultas nuevas.')
        return deepcopy(indice[texto])

    return preparar
