"""Preparación de descripciones sin acceso a la respuesta correcta."""
import re
import unicodedata
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm
from .normalizacion import preparar_descripcion


# Separa definiciones de significado de conjugaciones, glosas de forma y encabezados vacíos.
def seleccionar_definiciones(tabla):
    """Separa las filas que no son definiciones de significado.

    Devuelve dos tablas: las definiciones válidas y las excluidas con su motivo.
    """
    texto = tabla["definicion"].astype("string")

    # Regla 1: la palabra o el texto están vacíos.
    vacia = (
        tabla["objetivo"].astype("string").str.strip().eq("").fillna(True)
        | texto.isna()
        | texto.str.strip().eq("").fillna(True)
    )

    # Regla 2: Wiktionary marca la fila como conjugación.
    conjugacion = tabla["classification"].fillna("").str.strip().str.casefold().eq("conjugación")

    # Regla 3: el texto empieza como «Forma del/de … femenino/masculino/plural/singular».
    patron_forma = (
        r"^\s*forma\s+(?:(?:del?|de la|de los|de las)\s+)?"
        r"(?:femenin[oa]|masculin[oa]|plural|singular)\b"
    )
    forma = texto.str.contains(patron_forma, case=False, regex=True, na=False)

    # Regla 4: el texto es solo un encabezado, como «Nota de uso:.».
    encabezado = texto.str.fullmatch(
        r"\s*(?:nota de uso|uso|ámbito|etimología|sinónimos|antónimos|ejemplos?)\s*[:：]\s*[.\s]*",
        case=False, na=False,
    )

    # Asignar a cada fila el motivo de la primera regla que cumple.
    # Si ninguna se cumple, el motivo queda vacío y la fila se conserva.
    motivo = np.select(
        [vacia, conjugacion, forma, encabezado],
        ["registro_vacio", "conjugacion", "glosa_de_forma", "encabezado_sin_definicion"],
        default="",
    )

    excluidas = tabla.loc[motivo != ""].copy()
    excluidas["motivo"] = motivo[motivo != ""]

    validas = tabla.loc[motivo == ""].copy()
    return validas, excluidas


# Detecta si una descripción incluye la respuesta original, incluso con un número de acepción.
def menciona_original(texto, palabra):
    """Indica si el texto contiene la palabra original, incluso con un número de acepción.

    Por ejemplo, «gofio2» en el texto cuenta como «gofio».
    """
    palabra = unicodedata.normalize("NFC", str(palabra)).replace("_", " ").strip().casefold()
    if not palabra:
        return False

    texto = unicodedata.normalize("NFC", str(texto)).casefold()

    # Buscar la palabra completa: no debe estar pegada a otras letras.
    # Permite un número opcional al final (la acepción).
    patron = r"(?<!\w)" + r"\s+".join(re.escape(p) for p in palabra.split()) + r"\d*(?!\w)"
    return re.search(patron, texto) is not None


# Construye el conjunto evaluable y registra por qué se descarta cada definición.
def preparar_evaluacion(tabla, modelo, vocabulario, max_palabras):
    datos = tabla.copy()

    # Motivos: vacío significa que la fila sigue siendo válida.
    motivos = pd.Series("", index=datos.index)

    # Regla 1: la palabra correcta debe existir en el grafo.
    fuera = ~datos["objetivo"].isin(vocabulario)
    motivos.loc[fuera] = "objetivo_fuera_del_grafo"
    candidatas = datos.loc[~fuera].copy()

    # Clave de comparación: texto sin mayúsculas ni espacios extra.
    # Sirve solo para detectar repetidos; el texto original no cambia.
    candidatas["clave_definicion"] = (
        candidatas["definicion"].astype("string")
        .str.normalize("NFC").str.casefold()
        .str.replace(r"\s+", " ", regex=True).str.strip()
    )

    # Regla 2: el mismo texto con palabras distintas. No sabemos cuál es la correcta.
    conflictos = candidatas.groupby("clave_definicion")["objetivo"].transform("nunique").gt(1)
    motivos.loc[candidatas.index[conflictos]] = "texto_con_objetivos_distintos"

    # Regla 3: el mismo texto para la misma palabra. Conservamos la primera aparición.
    repetidas = ~conflictos & candidatas.duplicated("clave_definicion", keep="first")
    motivos.loc[candidatas.index[repetidas]] = "texto_repetido_mismo_objetivo"

    # Quedarse solo con las filas que no tienen conflicto ni repetición.
    candidatas = candidatas.loc[~conflictos & ~repetidas].copy()
    if candidatas.empty:
        raise ValueError("No quedaron definiciones después de los filtros. Revisa los datos y sus reglas.")

    # Preparar cada descripción con spaCy. Se hace en lotes para ir más rápido.
    docs = modelo.pipe(candidatas["definicion"].astype(str), batch_size=128)
    consultas = [
        preparar_descripcion(doc, vocabulario, max_palabras)
        for doc in tqdm(docs, total=len(candidatas), desc="Preparar descripciones")
    ]
    candidatas = pd.concat([candidatas.reset_index(), pd.DataFrame(consultas)], axis=1).set_index("index")

    # Regla 4: la descripción menciona su respuesta, ya sea como lema o como palabra original.
    menciona = [
        objetivo in excluir or menciona_original(texto, original)
        for objetivo, excluir, texto, original in zip(
            candidatas["objetivo"], candidatas["excluir"], candidatas["definicion"], candidatas["word_original"]
        )
    ]
    motivos.loc[candidatas.index[menciona]] = "descripcion_contiene_objetivo"

    # Auditoría: todas las filas retiradas, con su motivo.
    auditoria = datos.loc[motivos.ne("")].copy()
    auditoria["motivo"] = motivos.loc[auditoria.index]

    # Filas válidas: las que no recibieron ningún motivo.
    validas = candidatas.loc[motivos.loc[candidatas.index].eq("")].copy()

    # Comprobación: no debe perderse ninguna fila.
    assert len(datos) == len(validas) + len(auditoria)
    return validas, auditoria


# Separa desarrollo y prueba por concepto para no repartir sus glosas entre ambas particiones.
def dividir_definiciones(tabla, semilla, proporcion_desarrollo=0.25):
    conceptos = sorted(tabla["objetivo"].unique())
    if len(conceptos) < 4:
        raise ValueError("Se necesitan al menos cuatro conceptos para esta partición.")

    # Elegir qué conceptos van a desarrollo. El resto va a prueba.
    desarrollo, prueba = train_test_split(conceptos, train_size=proporcion_desarrollo, random_state=semilla)

    datos = tabla.copy()
    datos["particion"] = np.where(datos["objetivo"].isin(desarrollo), "desarrollo", "prueba")

    df_desarrollo = datos.loc[datos["particion"].eq("desarrollo")].copy()
    df_prueba = datos.loc[datos["particion"].eq("prueba")].copy()

    # Comprobación: ningún concepto ni ninguna descripción aparece en las dos particiones.
    assert set(df_desarrollo["objetivo"]).isdisjoint(df_prueba["objetivo"])
    assert set(df_desarrollo["clave_definicion"]).isdisjoint(df_prueba["clave_definicion"])
    return df_desarrollo, df_prueba

