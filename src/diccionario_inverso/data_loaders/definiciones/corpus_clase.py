from pathlib import Path
import unicodedata
import pandas as pd
from ...normalizacion import normalizar_superficie
from ...contratos import completar_definiciones


# Lee los textos del corpus docente y, si se indica, incorpora su auditoría histórica de consultas.
def leer_corpus_clase(directorio, auditoria=None):
    filas = []
    for archivo in sorted(Path(directorio).glob('*.txt')):
        lineas = archivo.read_text(encoding='utf-8-sig').splitlines()
        for numero, texto in enumerate(lineas[1:], start=2):
            if texto.strip():
                filas.append(dict(id=f'{unicodedata.normalize("NFC", archivo.stem)}_{numero:02d}', objetivo=normalizar_superficie(lineas[0]),
                                  definicion=texto.strip(), fuente=archivo.name, particion='benchmark_docente'))
    tabla = completar_definiciones(pd.DataFrame(filas), 'corpus_clase')
    if auditoria is not None:
        preparado = pd.read_json(auditoria, lines=True).set_index('id')
        for col, origen in [('semillas', 'semillas_nuestro'), ('excluir', 'excluir_nuestro'),
                            ('lemas', 'lemas_nuestro'), ('fuera_vocabulario', 'fuera_vocabulario')]:
            tabla[col] = tabla.id.map(preparado[origen])
        if tabla.semillas.isna().any():
            raise ValueError('Los ids del corpus no coinciden con la auditoría de consultas.')
        tabla['cubierta'] = tabla.semillas.map(bool)
    return tabla

