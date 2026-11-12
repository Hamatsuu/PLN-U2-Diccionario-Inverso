"""Tablas de lectura y figuras Plotly; aquí no se entrenan ni evalúan modelos."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .rutas import CARPETA
from .evaluacion import intervalo_wilson

ACENTO = '#087e8b'
CONTRASTE = '#b36a27'
NOMBRES_GRAFOS = {'nalc': 'NALC normalizado', 'nap_clase': 'NAP de la clase',
                  'nalc_normalizado': 'NALC reconstruido', 'nap_normalizado': 'NAP normalizado'}
NOMBRES_DATASETS = {'wordnet': 'WordNet', 'wiktionary': 'Wiktionary',
                    'corpus_clase': 'corpus de la clase', 'equipo': 'equipo', 'csv': 'CSV'}
NOMBRES_PARTICIONES = {'desarrollo': 'desarrollo', 'prueba': 'prueba',
                       'prueba_reservada': 'prueba reservada', 'benchmark_docente': 'corpus de la clase',
                       'complemento_manual': 'complemento manual', 'exploratorio': 'exploratoria'}


# Identifica las asociaciones, las definiciones y las consultas dentro de cada figura de resultados.
def contexto_consultas(grafo, dataset, particion, n):
    if not grafo or not dataset or not particion:
        raise ValueError('Indique el grafo, las definiciones y la partición de la figura.')
    cantidad = f'{int(n):,}'.replace(',', '\u202f')
    return (f'Grafo: {NOMBRES_GRAFOS.get(grafo, grafo)} · Definiciones: {NOMBRES_DATASETS.get(dataset, dataset)}'
            f'<br>Partición: {NOMBRES_PARTICIONES.get(particion, particion)} · {cantidad} consultas')


# Aplica el estilo común de las figuras Plotly para mantener una lectura consistente.
def estilo(figura, titulo, altura=440, *, subtitulo=None):
    figura.update_layout(template='plotly_white',
                          title=dict(text=titulo, font=dict(family='Georgia', size=23),
                                     subtitle=dict(text=subtitulo or '', font=dict(family='Helvetica Neue, sans-serif', size=12))),
                          height=altura, font=dict(family='Helvetica Neue, sans-serif', size=13), separators=',\u202f',
                          margin=dict(l=30, r=30, t=120 if subtitulo else 80, b=55), paper_bgcolor='rgba(0,0,0,0)',
                          colorway=[ACENTO, CONTRASTE, '#6c737f'])
    figura.update_xaxes(showgrid=True, gridcolor='#e7eaed', zeroline=False)
    figura.update_yaxes(zeroline=False)
    return figura


# Lee los resúmenes históricos incluidos sin volver a ejecutar sus experimentos.
def cargar_historicos(carpeta=CARPETA):
    return pd.read_csv(Path(carpeta) / 'resultados/historicos/metricas.csv')


# Selecciona una sola combinación de grafo, dataset y partición para comparar modelos.
def filtrar_comparacion(tabla, grafo, dataset, particion, brazo=None):
    resultado = tabla.loc[tabla.grafo.eq(grafo) & tabla.dataset.eq(dataset) & tabla.particion.eq(particion)].copy()
    if brazo is not None and 'brazo' in resultado:
        resultado = resultado.loc[resultado.brazo.eq(brazo)]
    if resultado.empty:
        raise ValueError('No hay resultados para esa combinación de grafo, dataset y partición.')
    return resultado


# Presenta nombres históricos legibles sin cambiar los identificadores de las métricas.
def etiqueta_modelo(nombre):
    if nombre.startswith('Baseline docente'):
        return 'Cercanía reducida de la clase'
    if nombre == 'Subconjunto no dirigido':
        return 'Intermediación entre pistas · sin dirección'
    if not nombre.startswith(('nuestro_', 'clase_')):
        return nombre
    prefijo, resto = nombre.split('_', 1)
    for original, legible in (
        ('dist_inversa', '1/FSG'), ('dist_log', '−ln(FSG)'),
        ('vector_propio', 'vector propio'), ('intermediacion', 'intermediación'),
        ('cercania', 'cercanía'), ('asociacion', 'asociación'), ('pagerank', 'PageRank'),
    ):
        resto = resto.replace(original, legible)
    resto = resto.replace('_', ' ')
    for centralidad in ('cercanía', 'intermediación'):
        resto = resto.replace(f'{centralidad} reducido', f'{centralidad} reducida')
        resto = resto.replace(f'{centralidad} completo', f'{centralidad} completa')
    legible = resto if resto.startswith('node2vec') else resto[0].upper() + resto[1:]
    return ('De la clase · ' if prefijo == 'clase' else '') + legible


# Formatea tablas de lectura con unidades explícitas, sin modificar los datos originales.
def tabla_lectura(tabla, formatos=None):
    tabla = tabla.copy(deep=True)
    for columna in ('modelo', 'Modelo', 'modelo_a', 'modelo_b'):
        if columna in tabla:
            tabla[columna] = tabla[columna].map(etiqueta_modelo)
    for columna, nombres in (('grafo', NOMBRES_GRAFOS), ('dataset', NOMBRES_DATASETS),
                             ('particion', NOMBRES_PARTICIONES),
                             ('Algoritmo', {'docente_cercania': 'Cercanía de la clase'})):
        if columna in tabla:
            tabla[columna] = tabla[columna].replace(nombres)
    return (tabla.style.format(formatos or {}, na_rep='—', escape='html', decimal=',', thousands='\u202f')
            .hide(axis='index')
            .set_properties(**{'text-align': 'left', 'padding': '10px 14px', 'vertical-align': 'top'})
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'left'), ('padding', '10px 14px'),
                                             ('border-bottom', '2px solid var(--border, #dce5e4)')]},
                {'selector': 'td', 'props': [('border-bottom', '1px solid var(--border, #e7edec)')]},
                {'selector': 'table', 'props': [('border-collapse', 'collapse'), ('width', '100%')]},
            ]))


# Compara aciertos de modelos de la misma población con intervalos Wilson descriptivos.
def grafico_modelos(tabla, metrica='hit@5'):
    if tabla[['grafo', 'dataset', 'particion']].drop_duplicates().shape[0] != 1:
        raise ValueError('No mezcle grafos, datasets o particiones en un ranking de modelos.')
    if tabla.n.nunique() != 1:
        raise ValueError('No compare modelos evaluados con distintos tamaños de muestra.')
    datos = tabla.sort_values(metrica).copy()
    intervalos = [intervalo_wilson(int(round(p*n)), n) for p, n in zip(datos[metrica], datos.n)]
    error_menos = [p-lo for p, (lo, hi) in zip(datos[metrica], intervalos)]
    error_mas = [hi-p for p, (lo, hi) in zip(datos[metrica], intervalos)]
    colores = [CONTRASTE if n.startswith(('clase_', 'Baseline docente')) else ACENTO for n in datos.modelo]
    figura = go.Figure(go.Bar(x=datos[metrica], y=datos.modelo.map(etiqueta_modelo), orientation='h',
                             marker_color=colores,
                             error_x=dict(type='data', array=error_mas, arrayminus=error_menos),
                             customdata=np.column_stack([datos.n, datos.cobertura, datos.MRR]),
                             hovertemplate='%{y}<br>Acierto: %{x:.2%}<br>n=%{customdata[0]:.0f}'
                                           '<br>Cobertura: %{customdata[1]:.1%}<br>MRR: %{customdata[2]:.4f}<extra></extra>'))
    fila = datos.iloc[0]
    contexto = contexto_consultas(fila.grafo, fila.dataset, fila.particion, fila.n)
    estilo(figura, f'{metrica.replace("hit", "Hit")} · Comparación de métodos',
           max(400, 27*len(datos)+170), subtitulo=contexto)
    figura.update_xaxes(title=f'{metrica} · IC 95 % Wilson descriptivo', tickformat='.0%', range=[0, min(1, max(hi for lo, hi in intervalos)*1.18)])
    figura.update_yaxes(title=None, automargin=True)
    return figura


# Muestra qué proporción de las descripciones de cada partición tiene al menos una semilla.
def grafico_cobertura(tabla, *, grafo, dataset):
    tabla = tabla.copy()
    tabla['particion'] = tabla.particion.replace(NOMBRES_PARTICIONES)
    figura = px.bar(tabla, x='particion', y='cobertura', text='n', color_discrete_sequence=[ACENTO],
                    hover_data=['conceptos', 'semillas_mediana', 'palabras_mediana'])
    contexto = contexto_consultas(grafo, dataset, 'varias (ver eje horizontal)', tabla.n.sum())
    estilo(figura, 'Consultas con al menos una pista en el grafo', subtitulo=contexto)
    figura.update_yaxes(tickformat='.0%', range=[0, 1.08], title='Cobertura')
    figura.update_xaxes(title=None)
    return figura


# Muestra cómo se distribuye el número de conexiones y señala los nodos aislados.
def grafico_grados(grafo, *, fuente):
    grados = pd.Series(dict(grafo.degree()), name='grado').value_counts().sort_index().rename_axis('grado').reset_index(name='nodos')
    positivos = grados.loc[grados.grado.gt(0)]
    figura = px.scatter(positivos, x='grado', y='nodos', log_x=True, log_y=True, color_discrete_sequence=[ACENTO])
    if not fuente:
        raise ValueError('Indique la fuente de asociaciones de la figura.')
    nombre = NOMBRES_GRAFOS.get(fuente, fuente)
    direccion = ('arcos en los dos sentidos' if fuente == 'nap_clase'
                 else 'con dirección' if grafo.is_directed() else 'sin dirección')
    cantidad_nodos = f'{grafo.number_of_nodes():,}'.replace(',', '\u202f')
    cantidad_aristas = f'{grafo.number_of_edges():,}'.replace(',', '\u202f')
    palabras = 'palabra' if grafo.number_of_nodes() == 1 else 'palabras'
    arcos = 'arco' if grafo.number_of_edges() == 1 else 'arcos'
    contexto = (f'Asociaciones: {nombre} · Grafo completo, {direccion}'
                f'<br>{cantidad_nodos} {palabras} · {cantidad_aristas} {arcos} · Sin definiciones ni modelos')
    nombre_corto = 'NALC' if fuente.startswith('nalc') else 'NAP' if fuente.startswith('nap') else fuente
    estilo(figura, f'Conexiones por palabra · {nombre_corto}', altura=480, subtitulo=contexto)
    eje_grado = 'Conexiones de entrada + salida' if grafo.is_directed() else 'Conexiones por palabra'
    figura.update_xaxes(title=f'{eje_grado} · escala logarítmica', dtick=1, tickformat=',.0f')
    figura.update_yaxes(title='Número de palabras · escala logarítmica', dtick=1, tickformat=',.0f')
    aislados = int(grados.loc[grados.grado.eq(0), 'nodos'].sum())
    figura.add_annotation(text=f'Aislados: {aislados} (fuera del eje log)', xref='paper', yref='paper', x=1, y=1, showarrow=False)
    return figura


# Muestra la diferencia entre dos modelos y su intervalo bootstrap por objetivo.
def grafico_pareado(comparacion, *, grafo, dataset, particion):
    fila = comparacion.iloc[0]
    figura = go.Figure(go.Scatter(x=[fila.diferencia], y=[f'{etiqueta_modelo(fila.modelo_a)} − {etiqueta_modelo(fila.modelo_b)}'], mode='markers',
                                 marker=dict(size=12, color=CONTRASTE),
                                 error_x=dict(type='data', array=[fila.ic_superior-fila.diferencia],
                                              arrayminus=[fila.diferencia-fila.ic_inferior])))
    figura.add_vline(x=0, line_dash='dot', line_color='#727b86')
    contexto = contexto_consultas(grafo, dataset, particion, fila.n)
    estilo(figura, 'Diferencia entre modelos · bootstrap por objetivo', 380, subtitulo=contexto)
    figura.update_xaxes(tickformat='+.1%', title=f'Diferencia en {fila.metrica} (puntos porcentuales)')
    return figura


# Agrupa las consultas según la posición obtenida por su objetivo, incluyendo los fallos.
def grafico_posiciones(detalle, *, grafo, dataset, particion):
    tabla = detalle.copy()
    tabla['modelo'] = tabla.modelo.map(etiqueta_modelo)
    tabla['resultado'] = pd.cut(tabla.posicion, bins=[0, 1, 3, 5, 10, 50, np.inf],
                                labels=['1', '2–3', '4–5', '6–10', '11–50', '>50']).astype('string').fillna('No devuelto')
    conteos = tabla.groupby(['modelo', 'resultado'], observed=True).size().reset_index(name='consultas')
    figura = px.bar(conteos, x='modelo', y='consultas', color='resultado',
                    color_discrete_sequence=[ACENTO, '#4d9a9e', '#85b2ac', '#cec6a4', CONTRASTE, '#997360', '#b9bdc3'])
    contexto = contexto_consultas(grafo, dataset, particion, detalle.id.nunique())
    return estilo(figura, 'Posición de la respuesta · todas las consultas cuentan', 500, subtitulo=contexto)


# Selecciona ejemplos no resueltos en el top 5 para inspeccionar texto, semillas y predicciones.
def tabla_errores(detalle, modelo, limite=15):
    columnas = ['id', 'objetivo', 'definicion', 'semillas', 'fuera_vocabulario', 'top5', 'posicion']
    errores = detalle.loc[detalle.modelo.eq(modelo) & detalle['hit@5'].eq(0)]
    return errores.sort_values('id')[columnas].head(limite)
