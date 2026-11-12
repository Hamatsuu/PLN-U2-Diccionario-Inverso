## Quince casos de error clasificados


La ejecución de RRF sobre NALC + WordNet prueba obtiene 9,99 % p@5 (97 aciertos de 971 consultas). Por tanto, hay 874 fallos disponibles. No se eligieron al azar: se buscó que cubrieran las causas que pide el enunciado y que tuvieran evidencia visible en los campos guardados. RRF es el modelo final del sistema, aunque no sea una centralidad pura; por eso los casos se clasifican a nivel de pipeline, no solo de algoritmo de grafos.

Campos usados para clasificar:

- `semillas`: lemas de la definición que sí están en el grafo.
- `fuera_vocabulario`: lemas que no están en el grafo.
- `top5`: primeras cinco palabras devueltas.
- `posicion`: lugar del objetivo en el ranking completo; vacío significa que no se devolvió.
- `longitud_ranking`: tamaño de la lista devuelta.
- Grado total del objetivo y de las palabras del top-5 en `nalc_nodos.csv`.


Los 15 casos son una muestra intencional, no una muestra aleatoria ni una estimación de la frecuencia de cada causa. Sirven para discutir mecanismos, no para decir “el 40 % de los errores son de polisemia”. Además, las causas pueden solaparse: un caso puede ser a la vez OOV y descripción ambigua.

### Tabla

| # | ID | Objetivo | Definición (resumen) | Semillas | Top-5 devuelto | Pos. | Causa principal | Evidencia |
|---:|:---|:---|:---|:---|:---|:---:|:---|:---|
| 1 | `00064370-n_0` | sorpresa | notoriedad imprevista | ∅ | ∅ | — | OOV / sin cobertura | `imprevista` y `notoriedad` fuera del grafo; ranking vacío |
| 2 | `00132322-r_0` | personalmente | concerniente al hablante | ∅ | ∅ | — | OOV / lematización | `concerniente` y `hablante` fuera; objetivo con grado 1; ranking vacío |
| 3 | `00250056-r_0` | al_lado | lado a lado | ∅ | ∅ | — | expresión multipalabra / palabras funcionales | `lemas = []`; `lado_a_lado` no existe como nodo; ranking vacío |
| 4 | `00090076-n_0` | embargo | resolución judicial de un acreedor para recobrar el bien… | judicial, mora, resolución | sentencia, juicio, acusación, juez, pleito | 895 | OOV / dominio jurídico | `acreedor`, `entablado`, `prestado`, `recobrar` fuera; top-5 jurídico pero no el objetivo |
| 5 | `00504019-v_0` | pellizcar | molestar como si fuera por un pellizco, una punzada… | molestar | fastidiar, irritar, ofender, agobiar, incordiar | 5188 | lematización / derivación + deriva semántica | `pellizco`, `punzada` y `desgarro` fuera; solo queda `molestar`; el top-5 son sinónimos de “molestar” |
| 6 | `00085046-v_0` | drogar | dar un narcótico | narcótico | droga, cocaína, coca, opio, heroína | 18 | POS / metonimia | El objetivo es verbo; el top-5 son sustantivos de sustancias; objetivo con grado 1 |
| 7 | `01246601-v_0` | afilar | hacer agudo o más agudo | agudo | crónico, leve, grave, dolor, punzante | 5342 | polisemia | `agudo` activa el sentido de dolor, no el de filo; el objetivo cae a 5342 |
| 8 | `00118567-a_0` | animado | dotado de vida, vigor o espíritu | de_vida, dotado, espíritu, vigor | vitalidad, evocación, fuerza, libre, fuerza_de_voluntad | 1601 | polisemia / abstracción | “animado” tiene varios sentidos; el top-5 son atributos, no la palabra |
| 9 | `00093163-v_0` | recuperar | devolver la buena salud o la fuerza | devolver, fuerza, salud | vitalidad, sanidad, bienestar, debilidad, resistencia | 6 | polisemia / sentido | El objetivo queda a una posición del top-5; compite con el sentido “recuperar(se)” y con nombres de salud |
| 10 | `00049220-r_0` | ahora | en el momento presente | momento, presente | instante, trance, circunstancia, acontecimiento, ausente | 11 | descripción ambigua | Top-5 temporal, pero el objetivo no queda primero; adverbio abstracto |
| 11 | `00082081-n_0` | compra | transacción en un mercado | mercado | exportación, consumo, mercader, mercadillo, venta | 7 | OOV + hiperónimo | `transacción` fuera; solo queda `mercado`; el top-5 es el campo comercial, no la acción |
| 12 | `00312932-n_0` | crucero | viaje por el mar que se realiza por placer | mar, placer, realizar, viaje | travesía, océano, velero, barco, lancha | 7 | especificidad / hiperónimo | El top-5 son tipos de barco o viaje; `barco` tiene grado 122; el objetivo es un tipo específico |
| 13 | `00560247-v_0` | fallar | probar insuficiente | insuficiente, probar | demostrar, preparar, comprobar, comida, trar | 264 | sesgo a nodos muy conectados | `comida` aparece en el top-5 con grado 440; el objetivo queda en 264 |
| 14 | `00546613-n_0` | villancico | canción alegre que celebra el nacimiento de Cristo | alegre, canción, celebrar, cristo, nacimiento | celebración, fiesta, jubiloso, resurrección, guateque | 15 | sesgo a hubs / categoría | `celebración` tiene grado 259; el top-5 se queda en la fiesta, no en la canción |
| 15 | `07591961-n_0` | paella | plato con arroz, marisco y pollo | arroz, marisco, plato, pollo | curry, garbanzo, fideo, repollo, comida | 88 | sesgo a hubs / categoría | `comida` tiene grado 440; el top-5 son alimentos, no el plato concreto |

| Causa | Casos | Comentario |
|:---|:---|:---|
| OOV / cobertura | 1, 2, 4, 11 | La definición pierde las palabras que más discriminan |
| Lematización / derivación | 2, 5 | Formas derivadas o flexivas no llegan al nodo correcto |
| Expresión multipalabra / normalización | 3 | El objetivo y la definición usan expresiones distintas |
| POS / metonimia | 6 | Se recupera la categoría (droga) y no la acción (drogar) |
| Polisemia | 7, 8, 9 | Una semilla activa el sentido equivocado |
| Descripción ambigua | 10, 11 | La definición es demasiado general o depende del contexto |
| Especificidad / hiperónimo | 12 | Se devuelve el hiperónimo o el tipo de objeto, no el objetivo |
| Sesgo a hubs | 13, 14, 15 | Nodos muy conectados (comida, celebración) desplazan al objetivo |


---

## Pregunta 3 ¿Qué ponderación funciona mejor?

En NAP hay tres ponderaciones distintas: **asociación**, **frecuencia** y **tiempo**.

### Los datos de NAP

| Modelo | Ponderación | p@1 | p@3 | p@5 |
|:---|:---|---:|---:|---:|
| Cercanía reducida | **Asociación** | **22,46** | **42,75** | **51,81** |
| Cercanía reducida | Frecuencia | 19,57 | 35,51 | 51,45 |
| Cercanía reducida | Tiempo | 7,97 | 21,01 | 28,26 |
| Intermediación reducida | **Asociación** | **17,03** | **36,23** | **44,93** |
| Intermediación reducida | Frecuencia | 13,77 | 30,80 | 36,23 |
| Intermediación reducida | Tiempo | 8,33 | 21,01 | 26,81 |

1. Asociación gana en p@1, p@3 y p@5.
2. Frecuencia queda cerca en p@5 para cercanía (51,45 vs 51,81), pero pierde en p@1 (19,57 vs 22,46).
3. Tiempo es la peor por mucho. No parece capturar bien qué palabra es la respuesta.

### Los datos de NALC

NALC solo tiene fuerza de asociación. Lo que se compara es la transformación:

| Modelo | 1/FSG p@1 / p@5 | −log FSG p@1 / p@5 |
|:---|:---:|:---:|
| Distancia | 0,9 / 3,0 | **0,9 / 3,5** |
| Cercanía reducida | 0,3 / 1,4 | **0,3 / 1,5** |
| Intermediación reducida | **0,8 / 3,1** | 0,7 / **3,4** |
| Intermediación completa | **0,5 / 1,4** | 0,4 / 1,0 |
| Cercanía completa | 0,1 / 1,0 | 0,1 / 0,9 |

- En el grafo reducido, `−log FSG` suele ganar.
- En el grafo completo, `1/FSG` puede ganar, sobre todo en intermediación.
- La diferencia es pequeña, pero se repite.

---

## Pregunta 1 ¿Qué se pierde al quitar la dirección?


Al una asociación no ser una calle de doble sentido como “perro” puede jalar “ladrar” con mucha fuerza, pero “ladrar” no jala a “perro” con la misma fuerza. Al hacer el grafo no dirigido, esa diferencia desaparece.

En NALC:

| Métrica | Valor |
|:---|---:|
| Nodos | 12 141 |
| Aristas dirigidas | 85 663 |
| Aristas que tienen inversa | **20,6 %** |
| Pares recíprocos con la misma fuerza | **7,3 %** |
| Diferencia media de fuerza en pares recíprocos | 0,085 |
| Nodos en la mayor componente fuerte | **41,9 %** |
| Nodos en la mayor componente débil | **100 %** |
| Pares no dirigidos únicos | 76 854 |


- Solo el 20,6 % de las aristas tienen inversa. La mayoría de las asociaciones van en un solo sentido.
- Solo el 7,3 % de los pares recíprocos tienen la misma fuerza. Aunque exista ida y vuelta, no valen lo mismo.
- El 41,9 % de los nodos está en la mayor componente fuerte, pero el 100 % está en la componente débil. Al quitar la dirección, todo queda conectado; con dirección, no.
- Hay 76 854 pares no dirigidos únicos frente a 85 663 aristas dirigidas. Al colapsar, se pierden 8 809 pares que iban en ambos sentidos.

Los hubs lo muestran claro:

| Palabra | Entradas | Salidas |
|:---|---:|---:|
| comida | 416 | 24 |
| casa | 348 | 60 |
| dolor | 339 | 24 |

Muchas palabras apuntan a `comida`, pero `comida` no devuelve esas asociaciones con la misma fuerza.

### Qué información se pierde

1. La asimetría de la fuerza. A → B no es igual a B → A.
2. La alcanzabilidad. Un camino que existe en un sentido puede no existir en el otro.
3. El flujo de PageRank. La importancia que se reparte desde las semillas cambia si cambias la dirección.
4. El significado del camino. La cercanía dirigida mide “quién llega a quién”; la no dirigida mide “quién está conectado con quién”.
5. La interpretación psicológica. La asociación libre es asimétrica; el grafo no dirigido borra esa hipótesis.

### Evidencia en los resultados

En NALC desarrollo, con las mismas consultas:

| Modelo | Dirigido p@5 | No dirigido p@5 |
|:---|---:|---:|
| PageRank contrastivo | 3,8 % | **5,6 %** |
| Armónica | 3,5 % | **4,6 %** |

El no dirigido mejora en este caso. Pero no puedes decir que la dirección sea la única causa: también cambian la matriz de transición, los candidatos y la forma de puntuar. Lo correcto es decir que la dirección sí influye y que el resultado no es neutral.


