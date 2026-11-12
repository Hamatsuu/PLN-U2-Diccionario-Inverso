"""Consultas libres, catálogo y ejecución explícita de experimentos."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .modelos import Modelo, MODELOS, BASELINE_CLASE


# Interpreta modos excluyentes y carga solo los recursos del modo solicitado.
def main(argv=None):
    parser = argparse.ArgumentParser(description='Consultar el diccionario inverso o ejecutar un experimento explícito.')
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument('--config', type=Path, help='Ejecutar el experimento descrito en un JSON.')
    modos.add_argument('--listar', action='store_true', help='Mostrar la referencia de la clase y las 24 configuraciones.')
    modos.add_argument('--consulta', metavar='TEXTO', help='Buscar candidatos para una descripción.')
    modos.add_argument('--interactivo', action='store_true', help='Consultar varias descripciones en una sesión.')
    catalogo = {m.nombre: m for m in MODELOS}
    catalogo['clase'] = BASELINE_CLASE
    parser.add_argument('--grafo', choices=['nap_clase', 'nalc'], help='Grafo de consultas (por defecto: nap_clase).')
    parser.add_argument('--modelo', choices=list(catalogo), help='Nombre del catálogo entre comillas, o clase (por defecto: PageRank).')
    parser.add_argument('--top', type=int, help='Número máximo de candidatos (por defecto: 5).')
    args = parser.parse_args(argv)
    if not (args.config is not None or args.listar or args.consulta is not None or args.interactivo):
        args.interactivo = True
    consulta_libre = args.consulta is not None or args.interactivo
    if not consulta_libre and any(v is not None for v in (args.grafo, args.modelo, args.top)):
        parser.error('--grafo, --modelo y --top requieren --consulta o --interactivo.')
    if args.top is not None and args.top < 1:
        parser.error('--top debe ser un entero positivo.')
    if args.consulta is not None and not args.consulta.strip():
        parser.error('--consulta no puede estar vacía.')
    if args.listar:
        print(json.dumps([asdict(m) for m in [BASELINE_CLASE, *MODELOS]], ensure_ascii=False, indent=2))
        return
    if consulta_libre:
        from .cli import configurar_consulta, crear_consultor, mostrar_consulta, sesion_interactiva
        try:
            if args.interactivo:
                grafo, nombre, top = configurar_consulta(catalogo, args.grafo, args.modelo, args.top)
            else:
                grafo, nombre, top = args.grafo or 'nap_clase', args.modelo or 'PageRank', args.top or 5
            while True:
                print(f'Grafo: {grafo} | Modelo: {nombre} | Top: {top}', flush=True)
                print('Cargando recursos de consulta…', flush=True)
                consultar = crear_consultor(grafo, catalogo[nombre])
                if not args.interactivo:
                    mostrar_consulta(consultar, args.consulta.strip(), top)
                    break
                if sesion_interactiva(consultar, top) != 'menu':
                    break
                grafo, nombre, top = configurar_consulta(catalogo)
        except EOFError:
            print()
        except KeyboardInterrupt:
            print('\nConsulta interrumpida.')
            return 130
        except (OSError, ValueError, ImportError) as error:
            parser.exit(1, f'No se pudo consultar: {error}\n')
        return
    from .experimentos import Experimento, ejecutar
    datos = json.loads(args.config.read_text())
    datos['modelos'] = [Modelo(**m) for m in datos['modelos']]
    resumen, _, protocolo = ejecutar(Experimento(**datos))
    print(resumen[['modelo', 'n', 'hit@1', 'hit@3', 'hit@5', 'MRR']].to_string(index=False))
    print('Ejecución:', protocolo['ejecucion'])


if __name__ == '__main__':
    raise SystemExit(main())
