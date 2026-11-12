"""Consultas libres con recursos preparados una vez, sin evaluar ni entrenar."""
from functools import lru_cache


# Carga un grafo y un modelo fijo y devuelve un consultor de texto con diagnóstico.
def crear_consultor(nombre_grafo, modelo):
    from .grafos import cargar_grafo
    from .modelos import construir_modelos
    from .normalizacion import cargar_nlp, crear_preparador
    from .rutas import CARPETA

    grafo = cargar_grafo(nombre_grafo, CARPETA)
    if modelo.algoritmo == 'docente_cercania':
        from .baseline_docente import crear_preparador_docente
        preparar = crear_preparador_docente(grafo, CARPETA)
        nlp = None
    else:
        nlp = cargar_nlp('es_core_news_md')
        preparar = crear_preparador(nlp, grafo)
    # La búsqueda y el diagnóstico comparten la preparación de la consulta actual.
    preparar = lru_cache(maxsize=1)(preparar)
    buscadores, _ = construir_modelos(
        grafo, [modelo], CARPETA, nombre_grafo, nlp=nlp,
        preparar_texto=preparar, preparar_docente=preparar,
    )
    buscar = buscadores[modelo.nombre]

    # Envía únicamente el texto al buscador y acompaña el ranking con sus semillas.
    def consultar(texto):
        consulta = preparar(texto)
        return consulta, buscar(texto)

    return consultar


# Muestra semillas, términos ausentes y candidatos, sin atribuirles probabilidades.
def mostrar_consulta(consultar, texto, top):
    consulta, ranking = consultar(texto)
    print('Semillas:', ', '.join(consulta['semillas']) or '(ninguna)')
    fuera = [p for p in consulta['fuera_vocabulario'] if p]
    if fuera:
        print('Fuera del grafo:', ', '.join(fuera))
    if not consulta['semillas']:
        print('No hay palabras útiles en el grafo. Pruebe otra descripción.')
    elif not ranking:
        print('No se encontraron candidatos después de excluir las palabras de la descripción.')
    else:
        for posicion, palabra in enumerate(ranking[:top], 1):
            print(f'{posicion}. {palabra}')


# Pide una elección numerada y repite el menú si la entrada no es válida.
def elegir_opcion(titulo, opciones):
    print(f'\n{titulo}')
    for numero, (etiqueta, _) in enumerate(opciones, 1):
        print(f'  {numero}. {etiqueta}')
    while True:
        entrada = input('Opción [1]: ').strip() or '1'
        if entrada.isascii() and entrada.isdecimal() and 1 <= int(entrada) <= len(opciones):
            return opciones[int(entrada) - 1][1]
        print(f'Escriba un número entre 1 y {len(opciones)}.')


# Recoge las opciones que no llegaron como argumentos antes de cargar recursos.
def configurar_consulta(catalogo, grafo=None, modelo=None, top=None):
    print('\nDiccionario inverso · Configuración')
    print('Enter acepta la primera opción. Ctrl-D o Ctrl-C termina.')
    if grafo is None:
        grafo = elegir_opcion('Grafo', [('NAP · de la clase', 'nap_clase'), ('NALC', 'nalc')])
    if modelo is None:
        opciones = [('Cercanía reducida de la clase' if n == 'clase' else n, n) for n in catalogo]
        modelo = elegir_opcion('Modelo (los completos pueden tardar más)', opciones)
    while top is None:
        entrada = input('\nNúmero de resultados [5]: ').strip() or '5'
        if entrada.isascii() and entrada.isdecimal() and int(entrada) > 0:
            top = int(entrada)
        else:
            print('Escriba un entero positivo.')
    return grafo, modelo, top


# Mantiene consultas sucesivas y permite volver al menú para cambiar la configuración.
def sesion_interactiva(consultar, top):
    print('Escriba una descripción; /menu cambia opciones; /salir termina. Ctrl-D o Ctrl-C también termina.')
    while True:
        try:
            texto = input('\nDescripción> ').strip()
        except EOFError:
            print()
            return
        if texto.casefold() == '/salir':
            return
        if texto.casefold() == '/menu':
            return 'menu'
        if not texto:
            continue
        mostrar_consulta(consultar, texto, top)
