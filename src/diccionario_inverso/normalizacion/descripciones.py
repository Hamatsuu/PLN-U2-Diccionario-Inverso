"""Texto a semillas y exclusiones; nunca recibe objetivos ni alias."""
from .etiquetas import normalizar_superficie


# Extrae las semillas y los términos a excluir, reconociendo expresiones del vocabulario del grafo.
def preparar_descripcion(doc, vocabulario, max_palabras):
    """Convierte un texto procesado por spaCy en lemas, semillas y palabras a excluir.

    No recibe la respuesta correcta.
    """
    # Paso 1: lista de (lema, es_palabra_funcional) para cada palabra del texto.
    unidades = [(normalizar_superficie(t.lemma_ or t.text), t.is_stop) for t in doc if t.is_alpha]

    # Paso 2: buscar todas las expresiones de hasta max_palabras que existan en el grafo.
    coincidencias = {}
    excluir = {palabra for palabra, _ in unidades}
    for inicio in range(len(unidades)):
        for longitud in range(1, min(max_palabras, len(unidades) - inicio) + 1):
            etiqueta = "_".join(p for p, _ in unidades[inicio:inicio + longitud])
            if etiqueta in vocabulario:
                excluir.add(etiqueta)
                # Una palabra funcional sola no cuenta como lema, pero sí dentro de una expresión.
                if longitud > 1 or not unidades[inicio][1]:
                    coincidencias.setdefault(inicio, []).append((longitud, etiqueta))

    # Paso 3: recorrer el texto y tomar, en cada posición, la expresión más larga disponible.
    lemas = []
    inicio = 0
    while inicio < len(unidades):
        opciones = coincidencias.get(inicio, [])
        if opciones:
            longitud, etiqueta = max(opciones)
            lemas.append(etiqueta)
            inicio += longitud
        else:
            # Si no hay expresión, usar la palabra sola, salvo que sea funcional.
            if not unidades[inicio][1]:
                lemas.append(unidades[inicio][0])
            inicio += 1

    # Paso 4: quitar duplicados y ordenar para que el resultado sea reproducible.
    lemas = sorted(set(lemas))
    semillas = sorted(set(lemas) & vocabulario)

    return {
        "lemas": lemas,
        "semillas": semillas,
        "excluir": sorted(excluir),
        "fuera_vocabulario": sorted(set(lemas) - vocabulario),
        "cubierta": bool(semillas),
    }


# Captura el modelo lingüístico y el vocabulario para convertir nuevos textos en consultas de semillas.
def crear_preparador(nlp, vocabulario):
    vocabulario = frozenset(vocabulario)
    max_palabras = max((n.count("_")+1 for n in vocabulario), default=1)

    # Procesa un texto nuevo con el modelo lingüístico y extrae su consulta de semillas.
    def preparar(texto):
        if not isinstance(texto, str):
            raise TypeError("La definición debe ser str.")
        return preparar_descripcion(nlp(texto), vocabulario, max_palabras)

    return preparar
