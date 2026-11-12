from pathlib import Path
import json
import pandas as pd
from ...normalizacion import normalizar_superficie
from ...contratos import completar_definiciones


# Une glosas y lemas españoles de WordNet; audita las glosas que no tienen un objetivo disponible.
def leer_wordnet(ruta):
    """Glosas con objetivo español; registra glosas sin lema en attrs['auditoria'].

    spa:def tiene cuatro columnas. El objetivo es el primer alias ordenado,
    sin consultar el vocabulario de ningún grafo. No sustituye las selecciones
    históricas preparadas. Las glosas sin lema no son evaluables por contrato.
    """
    lemas, glosas = {}, []
    with Path(ruta).open(encoding='utf-8') as archivo:
        for numero, linea in enumerate(archivo, 1):
            partes = linea.rstrip('\n').split('\t')
            if len(partes) >= 3 and partes[1] == 'spa:lemma':
                lemas.setdefault(partes[0], []).append(normalizar_superficie(partes[2]))
            elif len(partes) >= 4 and partes[1] == 'spa:def':
                glosas.append(dict(id=f'{partes[0]}_{partes[2]}', synset=partes[0],
                                   definicion='\t'.join(partes[3:]), linea=numero, fuente='MCR/OMW spa:def'))
    tabla = pd.DataFrame(glosas)
    tabla['alias'] = tabla.synset.map(lambda s: sorted(set(lemas.get(s, []))))
    tabla['objetivo'] = tabla.alias.map(lambda a: a[0] if a else '')
    sin_objetivo = tabla.objetivo.eq('')
    auditoria = tabla.loc[sin_objetivo].assign(motivo='sin_lema_espanol').to_dict('records')
    resultado = completar_definiciones(tabla.loc[~sin_objetivo], 'MCR/OMW spa:def')
    resultado.attrs['auditoria'] = auditoria
    resultado.attrs['glosas_leidas'] = len(tabla)
    return resultado


# Adapta la selección histórica de WordNet y conserva las consultas y particiones de su grafo.
def leer_preparado_wordnet(ruta, grafo):
    filas = []
    for linea in Path(ruta).read_text().splitlines():
        fila = json.loads(linea)
        consulta = fila.get('consulta', fila.get('consulta_nuestro'))
        filas.append(dict(id=fila['id'], objetivo=fila['concepto'], definicion=fila['definicion'],
                          alias=fila[f'alias_en_{"nap" if grafo == "nap_clase" else "nalc"}'],
                          fuente=fila['fuente'], particion=fila['particion'], grupo=fila['grupo'],
                          **consulta))
    return completar_definiciones(pd.DataFrame(filas), 'WordNet preparado')

