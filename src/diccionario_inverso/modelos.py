"""Registro configurable de algoritmos. Prepara solo los recursos solicitados."""
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
import numpy as np

from .algoritmos import centralidad, contexto, difusion, fusion, node2vec, semantica, vectores
from .grafos import crear_vista_no_dirigida
from .busqueda import crear_busqueda
from .normalizacion import crear_preparador


# Describe una configuración del catálogo: nombre, algoritmo y parámetros.
@dataclass
class Modelo:
    nombre: str
    algoritmo: str
    parametros: dict = field(default_factory=dict)


# El nombre guardado permanece igual para poder leer las ejecuciones anteriores.
BASELINE_DOCENTE = Modelo('Baseline docente · Cercanía reducida', 'docente_cercania')
BASELINE_CLASE = BASELINE_DOCENTE


# Catálogo base; los bucles siguientes añaden variantes de costo, alcance y orientación.
MODELOS = [
    Modelo('PageRank', 'pagerank', {'alpha': 0.85}),
    Modelo('Grado completo', 'grado', {'ambito': 'completo'}),
    Modelo('Grado reducido', 'grado'),
    Modelo('Semántica spaCy', 'semantica'),
    Modelo('Fusión RRF', 'rrf', {'k': 60}),
]
for etiqueta, costo in [('inversa', 'costo_inverso'), ('log', 'costo_log')]:
    MODELOS.append(Modelo(f'Distancia {etiqueta}', 'distancia', {'atributo': costo}))
    for ambito in ('completo', 'reducido'):
        MODELOS.append(Modelo(f'Cercanía {etiqueta} {ambito}', 'cercania', {'atributo': costo, 'ambito': ambito}))
        MODELOS.append(Modelo(f'Intermediación {etiqueta} {ambito}', 'intermediacion',
                              {'atributo': costo, 'ambito': ambito, 'k': 64 if ambito == 'completo' else 16, 'semilla': 1950}))
for orientacion in ('dirigido', 'no_dirigido'):
    for algoritmo in ('subconjunto', 'armonica', 'contrastivo'):
        MODELOS.append(Modelo(f'{algoritmo} {orientacion}', algoritmo, {'orientacion': orientacion}))
for perfil in ('local64', 'neutral64', 'explorador64'):
    MODELOS.append(Modelo(f'node2vec {perfil}', 'node2vec', {'perfil': perfil}))


# Prepara buscadores de texto que ya capturan su algoritmo, recursos y normalización.
def construir_modelos(grafo, especificaciones, carpeta, nombre_grafo, nlp=None, *, preparar_texto=None, preparar_docente=None):
    """Devuelve búsquedas públicas str→list[str] y recursos entrenados.

    El preprocesamiento queda capturado antes de llamar al evaluador.
    """
    from .baseline_docente import crear_preparador_docente
    propios = [m for m in especificaciones if m.algoritmo != 'docente_cercania']
    if preparar_texto is None and propios:
        if nlp is None:
            raise ValueError('Indique preparar_texto o nlp para construir búsquedas de texto.')
        preparar_texto = crear_preparador(nlp, grafo)
    algoritmos, entrenados = construir_algoritmos(grafo, especificaciones, carpeta, nombre_grafo, nlp)
    docentes = {m.nombre for m in especificaciones if m.algoritmo == 'docente_cercania'}
    if docentes:
        preparar_docente = preparar_docente or crear_preparador_docente(grafo, carpeta)
    return {nombre: crear_busqueda(algoritmo, preparar_docente if nombre in docentes else preparar_texto)
            for nombre, algoritmo in algoritmos.items()}, entrenados


# Prepara los algoritmos internos de semillas y solo los recursos que requieren los modelos pedidos.
def construir_algoritmos(grafo, especificaciones, carpeta, nombre_grafo, nlp=None):
    """Interfaz interna semillas→ranking; no es el contrato del evaluador.

    Las centralidades completas se calculan una vez por ejecución. Se separa su
    costo del tiempo de consulta. Los vectores congelados solo sirven para el
    grafo original; para otro grafo se debe activar entrenar=True.
    """
    carpeta = Path(carpeta)
    recursos, entrenados, funciones = {}, {}, {}

    # Reutiliza los recursos de búsqueda de cada orientación del grafo durante esta ejecución.
    def obtener_contexto(orientacion):
        if orientacion not in ('dirigido', 'no_dirigido'):
            raise ValueError(f'Orientación desconocida: {orientacion}')
        if orientacion not in recursos:
            vista = grafo if orientacion == 'dirigido' else crear_vista_no_dirigida(grafo)
            recursos[orientacion] = contexto.preparar_busqueda_consulta(vista)
        return recursos[orientacion]

    # Comprueba los vectores spaCy y prepara el recurso semántico una sola vez.
    def obtener_semantica():
        if nlp is None:
            raise ValueError('Semántica y RRF requieren nlp con vectores españoles.')
        if 'semantica' not in recursos:
            if nlp.vocab.vectors_length == 0:
                raise ValueError('El modelo spaCy no tiene vectores. Use es_core_news_md.')
            recursos['semantica'] = semantica.preparar_semantica(nlp, grafo)
        return recursos['semantica']

    for especificacion in especificaciones:
        nombre, algoritmo = especificacion.nombre, especificacion.algoritmo
        p = dict(especificacion.parametros)
        if nombre in funciones:
            raise ValueError(f'Nombre de modelo repetido: {nombre}')
        if algoritmo == 'docente_cercania':
            from .baseline_docente import preparar_grafo_docente, buscar_cercania_docente
            if p:
                raise ValueError('La referencia de la clase tiene protocolo fijo, sin parámetros ajustables.')
            funciones[nombre] = partial(buscar_cercania_docente, preparar_grafo_docente(grafo))
        elif algoritmo == 'pagerank':
            funciones[nombre] = partial(difusion.buscar_pagerank, grafo, **p)
        elif algoritmo == 'distancia':
            funciones[nombre] = partial(difusion.buscar_distancia, grafo, **p)
        elif algoritmo in ('grado', 'cercania', 'intermediacion'):
            ambito = p.pop('ambito', 'reducido')
            if ambito not in ('completo', 'reducido'):
                raise ValueError(f'Ámbito desconocido: {ambito}')
            puntuaciones = None
            if ambito == 'completo':
                if algoritmo == 'grado':
                    puntuaciones = dict(grafo.in_degree(weight='fuerza'))
                elif algoritmo == 'cercania':
                    puntuaciones = centralidad.calcular_cercania(grafo, p['atributo'])
                else:
                    puntuaciones = centralidad.calcular_intermediacion(grafo, **p)
            if algoritmo == 'grado':
                funciones[nombre] = partial(centralidad.buscar_grado_ponderado, grafo, grados_completos=puntuaciones, **p)
            else:
                buscar = centralidad.buscar_cercania if algoritmo == 'cercania' else centralidad.buscar_intermediacion
                funciones[nombre] = partial(buscar, grafo, puntuaciones_completas=puntuaciones, **p)
        elif algoritmo in ('subconjunto', 'armonica', 'contrastivo'):
            ctx = obtener_contexto(p.pop('orientacion', 'dirigido'))
            buscar = {'subconjunto': contexto.buscar_subconjunto, 'armonica': contexto.buscar_armonica_consulta,
                      'contrastivo': contexto.buscar_pagerank_contrastivo}[algoritmo]
            funciones[nombre] = partial(buscar, ctx, **p)
        elif algoritmo == 'semantica':
            funciones[nombre] = partial(semantica.buscar_semantica, obtener_semantica(), **p)
        elif algoritmo == 'rrf':
            ctx = obtener_contexto(p.pop('orientacion', 'no_dirigido'))
            sem = obtener_semantica()
            funciones[nombre] = partial(_buscar_rrf, ctx, sem, **p)
        elif algoritmo == 'node2vec':
            entrenar = p.pop('entrenar', False)
            perfil = p.pop('perfil', 'local64')
            if entrenar:
                semilla = p.pop('semilla', 1950)
                configuracion = dict(dimension=64, longitud=20, caminatas=10, p=1.0, q=1.0)
                desconocidos = set(p) - set(configuracion)
                if desconocidos:
                    raise ValueError(f'Parámetros node2vec desconocidos: {sorted(desconocidos)}')
                configuracion.update(p)
                datos = node2vec.entrenar_node2vec(grafo, configuracion, semilla)
                entrenados[nombre] = datos
            else:
                if p:
                    raise ValueError('Cambiar caminatas, p o q requiere entrenar=True.')
                if nombre_grafo not in ('nalc', 'nap_clase') or perfil not in ('local64', 'neutral64', 'explorador64'):
                    raise ValueError('No hay vectores congelados compatibles. Use entrenar=True.')
                datos = vectores.cargar_node2vec(carpeta / f'datos/vectores/{nombre_grafo}/{perfil}.npz')
                if set(datos['nodos']) != set(grafo):
                    raise ValueError('Los vectores y el grafo no comparten vocabulario.')
            funciones[nombre] = partial(vectores.buscar_node2vec, datos)
        else:
            raise ValueError(f'Algoritmo desconocido: {algoritmo}')
    return funciones, entrenados


# Fusiona los rankings armónico y semántico con el parámetro k solicitado.
def _buscar_rrf(ctx, sem, consulta, k=60):
    if k <= 0:
        raise ValueError('k de RRF debe ser positivo.')
    return fusion.fusion_rrf([contexto.buscar_armonica_consulta(ctx, consulta),
                             semantica.buscar_semantica(sem, consulta)], k=k)
