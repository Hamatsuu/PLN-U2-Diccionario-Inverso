"""Configuración y ejecución serial. No se evalúa nada al importar este módulo."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time
import numpy as np
import pandas as pd

from .normalizacion import preparar_descripcion, crear_preparador, cargar_nlp
from .rutas import CARPETA
from .datasets import cargar_dataset
from .grafos.carga import cargar_grafo
from .contratos import validar_definiciones
from .busqueda import preparar_reproduccion
from .evaluacion import evaluar
from .modelos import Modelo, construir_modelos


# Reúne las opciones de datos, modelos y evaluación de una ejecución reproducible.
@dataclass
class Experimento:
    grafo: str = 'nalc'
    dataset: str = 'wordnet'
    particion: str = 'desarrollo'
    modelos: list[Modelo] = field(default_factory=lambda: [Modelo('PageRank', 'pagerank', {'alpha': .85})])
    limite: int | None = 100
    semilla: int = 1950
    modelo_spacy: str = 'es_core_news_md'
    ruta_csv: str | None = None
    permitir_prueba: bool = False
    repreparar_consultas: bool = False


# Genera la auditoría de lemas, semillas y exclusiones usando únicamente las descripciones.
def preparar_consultas(datos, nlp, grafo):
    resultado = datos.copy()
    vocabulario = set(grafo)
    max_palabras = max((n.count('_')+1 for n in grafo), default=1)
    consultas = [preparar_descripcion(doc, vocabulario, max_palabras)
                 for doc in nlp.pipe(datos.definicion.astype(str), batch_size=128)]
    for columna in ('lemas', 'semillas', 'excluir', 'fuera_vocabulario', 'cubierta'):
        resultado[columna] = [consulta[columna] for consulta in consultas]
    return resultado


# Selecciona la partición y la muestra reproducible, evitando evaluar prueba sin autorización.
def seleccionar_consultas(datos, config):
    if config.particion in ('prueba', 'todas', 'prueba_reservada') and not config.permitir_prueba:
        raise ValueError('Prueba protegida: habilite permitir_prueba conscientemente; no sirve para elegir parámetros.')
    if config.particion == 'todas':
        tabla = datos.copy()
    else:
        tabla = datos.loc[datos.particion.eq(config.particion)].copy()
    if tabla.empty:
        raise ValueError(f'Partición vacía: {config.particion}. Disponibles: {sorted(datos.particion.unique())}')
    if config.limite is not None:
        if config.limite < 1:
            raise ValueError('limite debe ser positivo o None.')
        if len(tabla) > config.limite:
            tabla = tabla.sample(n=config.limite, random_state=config.semilla)
    return tabla.sort_values('id').reset_index(drop=True)


# Obtiene la huella de un archivo para detectar cambios en datos, código o vectores.
def _sha_archivo(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


# Resume nodos, aristas, fuerzas y costos en una huella que identifica el grafo utilizado.
def _identidad_grafo(grafo):
    datos = {'dirigido': grafo.is_directed(), 'nodos': sorted(grafo),
             'aristas': sorted((a, b, float(d['fuerza']), float(d['costo']), float(d['costo_log']), float(d['costo_inverso']))
                               for a, b, d in grafo.edges(data=True))}
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False).encode()).hexdigest()


# Coordina la carga, preparación, evaluación y guardado de un experimento identificado por sus hashes.
def ejecutar(config, carpeta=CARPETA, guardar=True):
    """Prepara recursos, busca y guarda detalle y protocolo. Nunca reutiliza cachés.

    El id contiene datos, grafo, parámetros, código, dependencias y vectores.
    Si ya existe una ejecución idéntica se detiene antes de buscar.
    """
    carpeta = Path(carpeta)
    inicio = time.perf_counter()
    if not config.modelos:
        raise ValueError('Elija al menos un modelo.')

    # Carga solo los recursos necesarios para el grafo, los textos y los modelos elegidos.
    tiene_docente = any(m.algoritmo == 'docente_cercania' for m in config.modelos)
    tiene_propios = any(m.algoritmo != 'docente_cercania' for m in config.modelos)
    necesita_nlp = config.grafo.endswith('_normalizado') or (tiene_propios and (
        config.repreparar_consultas or config.dataset in ('wiktionary', 'equipo', 'csv')
    ))
    necesita_nlp |= any(m.algoritmo in ('semantica', 'rrf') for m in config.modelos)
    nlp = cargar_nlp(config.modelo_spacy) if necesita_nlp else None
    grafo = cargar_grafo(config.grafo, carpeta, nlp)
    datos = seleccionar_consultas(cargar_dataset(config.dataset, config.grafo, carpeta, config.ruta_csv), config)
    validar_definiciones(datos)

    # Elige cómo preparar textos: reproducir la auditoría histórica o normalizar de nuevo.
    historico = not config.repreparar_consultas and 'semillas' in datos
    if not tiene_propios:
        preparar_texto = None
        modo_consulta = 'solo_baseline_docente_desde_texto'
    elif historico:
        preparar_texto = preparar_reproduccion(datos, grafo)
        modo_consulta = 'reproduccion_historica_por_texto'
    else:
        nlp = nlp or cargar_nlp(config.modelo_spacy)
        datos = preparar_consultas(datos, nlp, grafo)  # Auditoría de cobertura, no entrada gold al buscador.
        preparar_texto = crear_preparador(nlp, grafo)
        modo_consulta = 'normalizacion_desde_texto'

    preparar_docente, datos_docente, recursos_docente = None, None, {}
    if tiene_docente:
        from .baseline_docente import crear_preparador_docente
        nlp_docente = cargar_nlp('es_core_news_sm')
        preparar_docente = crear_preparador_docente(grafo, carpeta, nlp_docente)
        datos_docente = datos.copy()
        auditoria = [preparar_docente(texto) for texto in datos.definicion]
        for columna in ('lemas', 'semillas', 'excluir', 'fuera_vocabulario', 'cubierta'):
            datos_docente[columna] = [consulta[columna] for consulta in auditoria]
        recursos_docente = dict(spacy=nlp_docente.meta, archivos={
            p.name: _sha_archivo(p) for p in sorted((carpeta / 'datos/baseline_docente').iterdir()) if p.is_file()})

    # Identifica exactamente datos, código y recursos para no confundir ejecuciones distintas.
    codigo = {str(p.relative_to(Path(__file__).parent)): _sha_archivo(p)
              for p in sorted(Path(__file__).parent.rglob('*.py'))}
    versiones = {nombre: importlib.metadata.version(nombre) for nombre in
                 ('networkx', 'numpy', 'pandas', 'scipy', 'spacy', 'igraph', 'gensim')}
    archivos_vectores = {}
    for modelo in config.modelos:
        if modelo.algoritmo == 'node2vec' and not modelo.parametros.get('entrenar', False):
            perfil = modelo.parametros.get('perfil', 'local64')
            ruta = carpeta / f'datos/vectores/{config.grafo}/{perfil}.npz'
            archivos_vectores[str(ruta.relative_to(carpeta))] = _sha_archivo(ruta)
    protocolo = dict(configuracion=asdict(config), grafo_sha256=_identidad_grafo(grafo),
                     consultas_sha256=hashlib.sha256(datos.to_json(orient='records', force_ascii=False).encode()).hexdigest(),
                     codigo=codigo, versiones=versiones, python=platform.python_version(),
                     vectores=archivos_vectores, spacy=nlp.meta if nlp else None,
                     contrato_busqueda='str -> list[str]', modo_consulta=modo_consulta,
                     baseline_docente=recursos_docente,
                     auditoria_docente_sha256=(hashlib.sha256(datos_docente.to_json(orient='records', force_ascii=False).encode()).hexdigest()
                                               if tiene_docente else None),
                     tiempo_consulta='llamada completa; incluye normalización desde texto o acceso a auditoría histórica según modo_consulta',
                     tipo='exploratorio', nota='No usar prueba para seleccionar modelos o parámetros.')
    identidad = hashlib.sha256(json.dumps(protocolo, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    destino = carpeta / 'resultados/experimentos' / identidad
    if guardar and destino.exists():
        raise FileExistsError(f'La ejecución {identidad} ya existe. Cargue sus resultados o cambie la configuración.')

    # Separa el costo de preparar los modelos del tiempo de atender cada consulta.
    preparacion_datos_s = time.perf_counter() - inicio
    inicio = time.perf_counter()
    modelos, entrenados = construir_modelos(grafo, config.modelos, carpeta, config.grafo, nlp,
                                                preparar_texto=preparar_texto, preparar_docente=preparar_docente)
    preparacion_modelos_s = time.perf_counter() - inicio

    # Todos los modelos reciben los mismos textos; el evaluador recibe solo el buscador ya preparado.
    resumenes, detalles = [], []
    for nombre, buscar in modelos.items():
        es_docente = next(m.algoritmo for m in config.modelos if m.nombre == nombre) == 'docente_cercania'
        detalle, resumen = evaluar(datos_docente if es_docente else datos, buscar)
        detalle['modelo'] = nombre
        resumen.update(modelo=nombre, grafo=config.grafo, dataset=config.dataset, particion=config.particion,
                       tipo='exploratorio', ejecucion=identidad)
        detalle['ejecucion'] = identidad
        resumenes.append(resumen)
        detalles.append(detalle)
    if not detalles:
        raise ValueError('Elija al menos un modelo.')
    resumen, detalle = pd.DataFrame(resumenes), pd.concat(detalles, ignore_index=True)
    protocolo.update(ejecucion=identidad, fecha_utc=datetime.now(timezone.utc).isoformat(),
                     preparacion_datos_s=preparacion_datos_s, preparacion_modelos_s=preparacion_modelos_s)

    # Guarda la evidencia del experimento en una carpeta nueva, sin reemplazar resultados anteriores.
    if guardar:
        destino.mkdir(parents=True, exist_ok=False)
        # Un directorio sin COMPLETO no es un resultado utilizable.
        (destino / 'protocolo.json').write_text(json.dumps(protocolo, ensure_ascii=False, indent=2))
        resumen.to_csv(destino / 'metricas.csv', index=False)
        detalle.to_json(destino / 'detalle.jsonl', orient='records', lines=True, force_ascii=False)
        datos.to_json(destino / 'consultas.jsonl', orient='records', lines=True, force_ascii=False)
        if tiene_docente:
            datos_docente.to_json(destino / 'consultas_docente.jsonl', orient='records', lines=True, force_ascii=False)
        for i, (nombre, datos_vectores) in enumerate(entrenados.items()):
            np.savez_compressed(destino / f'vectores_{i}.npz', nodos=datos_vectores['nodos'], vectores=datos_vectores['vectores'])
        (destino / 'COMPLETO').write_text(identidad)
    return resumen, detalle, protocolo


# Lee una ejecución completa y adapta en memoria los nombres de columnas anteriores.
def cargar_ejecucion(ruta):
    ruta = Path(ruta)
    if not (ruta / 'COMPLETO').exists():
        raise ValueError(f'Ejecución incompleta: {ruta}')
    # Adaptación de lectura de ejecuciones anteriores; nunca reescribe sus archivos.
    detalle = pd.read_json(ruta / 'detalle.jsonl', lines=True)
    detalle = detalle.rename(columns={'word': 'objetivo', 'definition': 'definicion'})
    return (pd.read_csv(ruta / 'metricas.csv'), detalle,
            json.loads((ruta / 'protocolo.json').read_text()))
