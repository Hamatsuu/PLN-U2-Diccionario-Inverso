"""Carga explícita de recursos lingüísticos, sin efectos al importar."""


# Carga explícitamente el modelo spaCy solicitado; importar el paquete no lo carga.
def cargar_nlp(nombre='es_core_news_md'):
    import spacy
    return spacy.load(nombre, disable=['parser', 'ner'])

