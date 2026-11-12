"""Normalización explícita de etiquetas; sin carga de modelos al importar."""
import re
import unicodedata
from tqdm.auto import tqdm


# Normaliza a Unicode NFC y minúsculas, cambia espacios por «_» y conserva acentos, sin lematizar.
def normalizar_superficie(texto):
    texto = unicodedata.normalize("NFC", str(texto)).strip().lower()
    return re.sub(r"\s+", "_", texto)


# Lematiza una columna por lotes y reutiliza la caché para no procesar etiquetas repetidas.
def normalizar_columna(columna, modelo, cache):
    valores = columna.astype("string")

    # Buscar solo los textos que todavía no están en la caché.
    pendientes = [t for t in valores.dropna().unique() if t not in cache]

    # nlp.pipe procesa muchos textos juntos, es más rápido que llamar a nlp uno por uno.
    docs = modelo.pipe((t.replace("_", " ") for t in pendientes), batch_size=256)

    for original, doc in tqdm(zip(pendientes, docs), total=len(pendientes), desc=f"Normalizar {columna.name}"):
        # Usar el lema de cada palabra. Descartar signos y números.
        cache[original] = "_".join(
            normalizar_superficie(t.lemma_ or t.text) for t in doc if t.is_alpha
        )

    # Reemplazar cada valor por su versión normalizada usando la caché.
    return valores.map(cache)


# Normaliza estímulos y respuestas con el mismo modelo y una caché compartida.
def normalizar_asociaciones(tabla, modelo):
    from ..contratos import validar_asociaciones
    validar_asociaciones(tabla)
    resultado = tabla.copy()
    cache = {}
    for columna in ("estimulo", "respuesta"):
        resultado[columna] = normalizar_columna(resultado[columna], modelo, cache)
    return resultado
