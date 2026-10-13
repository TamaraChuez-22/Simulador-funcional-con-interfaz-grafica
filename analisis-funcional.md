# Análisis funcional — Expedición: Zona Cero

**Asignatura:** Programación Funcional (Unidades 1 y 2) · **Estudiante:** Tamara Chuez Sanchez · **Carrera:** Software, UPSE

> Este documento sigue las 11 secciones que exige la guía de la actividad. La sección 11 incluye una parte que solo la estudiante puede confirmar (ver nota allí).

---

## 1. Problema que resuelve la aplicación

*Expedición: Zona Cero* es un simulador de gestión de recursos. El jugador dirige una expedición de 4 personas que debe acumular **100 puntos de progreso en 12 días** administrando agua, alimentos, energía y salud. Cada jornada elige una acción y, con 75 % de probabilidad, aparece un evento que exige una decisión (tormenta, hallazgo de provisiones, avería, zona peligrosa, refugio, emergencia médica).

El dominio sirve para demostrar programación funcional porque casi todo es una **transformación de estado**: "dado el estado actual y una acción, ¿cuál es el estado nuevo?". Ese es el tipo de problema donde funciones puras, datos inmutables y composición encajan de forma natural.

## 2. Estructuras de datos utilizadas

Todas son `@dataclass(frozen=True)` (Unidad 1: modelado con `dataclass`). No se usó `NamedTuple` ni `Union`.

| Estructura | Archivo | Contenido |
|---|---|---|
| `Recursos` | `models/expedition.py` | agua, alimentos, energía, salud (enteros 0–100, validados en `__post_init__`) |
| `Registro` | `models/expedition.py` | Una entrada del historial: día, tipo, descripción, consumido, recuperado, crítico |
| `Expedicion` | `models/expedition.py` | **Estado completo**: recursos, día, progreso, integrantes, clima, dificultad, evento pendiente, historial |
| `ResultadoAccion` | `models/expedition.py` | Resultado de una operación: estado nuevo, mensaje, válido, nivel |
| `Efecto` | `models/events.py` | Cambio (delta) sobre recursos, progreso, integrantes o clima |
| `Opcion`, `Evento`, `Accion` | `models/events.py` | Decisión, situación inesperada y orden del jugador |
| `EstadoMision` | `models/expedition.py` | `Enum`: En curso / Completada / Fallida |

Las colecciones son **tuplas** (`historial`, `opciones`, `CATALOGO_EVENTOS`) y los parámetros de balance son `MappingProxyType` (vista de solo lectura). Esto es deliberado: `frozen=True` solo protege el primer nivel, y una `list` dentro de una dataclass congelada seguiría siendo mutable.

### Organización en capas

| Capa | Carpeta | Responsabilidad | Qué NO hace |
|---|---|---|---|
| Datos / estado | `models/` | Estructuras inmutables y catálogo de eventos | No importa de `logic` ni de `ui` |
| Lógica | `logic/` | Reglas del dominio: acciones, turnos, eventos, reportes | No importa Tkinter ni imprime |
| Visual | `ui/` | Ventanas, widgets, mensajes | No contiene reglas de negocio |

Los callbacks que ejecutan acciones y decisiones son de dos líneas; solo llaman a la lógica y redibujan:

```python
def _on_accion(self, accion):
    self._aplicar(ejecutar_turno(self.expedicion, accion, tirar_dado()))

def _on_decision(self, clave):
    self._aplicar(resolver_evento(self.expedicion, clave, tirar_dado()))
```

Los callbacks de diálogo (`_reiniciar`, `_exportar`, `_anunciar_fin`) tienen 12 a 15 líneas, pero solo manejan cuadros de diálogo y llaman a funciones de la lógica; no contienen reglas del juego. `ui/presentacion.py` (puro) decide *qué* mostrar y `ui/components.py` solo lo dibuja. Incluso la decisión de habilitar o deshabilitar un botón reutiliza `motivo_no_disponible` de la capa lógica, sin duplicar reglas.

## 3. Dónde se aplicó la Unidad 1

| Contenido | Dónde | Por qué ahí |
|---|---|---|
| **Funciones de orden superior** | `aplicar_a_recursos(transformacion, recursos)` y `calcular_consumo(modificador)` en `logic/resources.py`; `filtrar_historial(criterio, historial)` y `ordenar_historial(clave, historial)` en `logic/reports.py` | Reciben una función como argumento: la misma maquinaria sirve para distintos criterios (p. ej. el filtro de la interfaz le pasa uno distinto a `filtrar_historial` según la opción elegida) |
| **`match/case`** | `planificar_accion` y `efecto_de_opcion` en `logic/actions.py` | Cada acción es un caso con reglas distintas. Se usan *patrones de clase* (`Accion(tipo="consumir_recurso", parametro="agua")`), un *guard* (`if recurso in ("agua", "alimentos")`), un patrón sobre tupla `(evento.tipo, opcion.clave)` y un caso `_` que rechaza lo desconocido |
| **Modelado con `dataclass`** | Todo `models/` | Ver sección 2 |
| **Funcional vs. imperativo** | `consumo_total_imperativo` y `consumo_total_funcional` en `logic/resources.py` | Mismo problema (sumar todo el consumo de varios turnos) en los dos estilos; la prueba `test_imperativo_y_funcional_dan_el_mismo_total` comprueba que dan igual |

**Por qué `match/case` no es adorno:** `planificar_accion` tiene 9 casos con comportamientos distintos, incluidos casos que dependen de un segundo campo (`parametro`) y casos de error. Hacerlo con `if/elif` encadenados mezclaría la comprobación del tipo con la del parámetro; con `match` cada patrón declara exactamente qué forma de dato espera.

### Comparación funcional vs. imperativo

```python
# Imperativo: bucles y un acumulador que se va modificando
def consumo_total_imperativo(consumos):
    total = 0
    for consumo_turno in consumos:
        for valor in consumo_turno.values():
            total += valor
    return total

# Funcional: una expresión, sin variable que cambie
def consumo_total_funcional(consumos):
    return reduce(lambda acumulado, turno: acumulado + sum(turno.values()), consumos, 0)
```

Ambas dan el mismo resultado (hay una prueba). En la aplicación se usa la funcional; la imperativa existe para esta comparación y para esa prueba.

| Aspecto | Imperativa | Funcional |
|---|---|---|
| Mutabilidad | Cambia la variable `total` en cada vuelta | No hay variable que cambie |
| Efectos secundarios | Ninguno (ambas son puras hacia afuera) | Ninguno |
| Legibilidad | Más fácil para quien empieza | Más compacta; exige entender `reduce` y `lambda` |
| Reutilización | El bucle está atado a este cálculo | `reduce` con otra función sirve para otros acumulados |
| Facilidad de prueba | Igual de fácil (misma entrada, misma salida) | Igual |
| Adecuación al problema | Correcta | Expresa mejor la idea "colapsar muchos valores en uno" |

No se presenta la funcional como universalmente superior: aquí gana poco en prueba y legibilidad; su ventaja es conceptual (no depender de un acumulador mutable).

## 4. Dónde se aplicó la Unidad 2

| Contenido | Dónde |
|---|---|
| **lambda** | `eventos_criticos` y `historial_por_tipo` (`logic/reports.py`); las 5 reglas de `CRITERIOS_HISTORIAL` (`ui/presentacion.py`); el acumulador de `reduce` |
| **Closure** | `crear_modificador_consumo(factor)` (sección 8) |
| **Inmutabilidad** | Todo el estado (sección 7) |
| **Pureza y efectos secundarios** | Secciones 5 y 6 |
| **`filter`** | `faltantes` y `penalizacion_por_agotamiento` (`logic/resources.py`), `filtrar_historial` (`logic/reports.py`) |
| **`reduce`** | `consumo_total_funcional` (`logic/resources.py`), `total_consumido` y `total_recuperado` (`logic/reports.py`) |

**Sobre `map`:** el proyecto **no usa `map`**. Donde se transforma una colección (por ejemplo `calcular_consumo` o `aplicar_a_recursos`) se usó una *comprensión de diccionario*, que en Python es más legible que `map` + `dict`. La guía pide "al menos una" entre `map`, `filter` y `reduce`; aquí hay `filter` y `reduce`, usados porque expresan exactamente la necesidad (quedarse con los que cumplen / colapsar muchos valores en uno).

### `filter` y `reduce`: entrada, transformación, resultado y justificación

| Función | Entrada | Transformación | Resultado | Por qué esa herramienta |
|---|---|---|---|---|
| `faltantes(recursos, requisitos)` | `Recursos` y mínimos exigidos | `filter` deja los nombres cuyo valor no alcanza el mínimo | Tupla con los recursos que faltan | La necesidad es "quedarse con los que NO cumplen" |
| `total_consumido(historial)` | Tupla de `Registro` | `reduce` suma el campo `consumido` | Un entero | Muchos valores colapsan en uno (acumulado) |
| `consumo_total_funcional` | Lista de consumos por turno | `reduce` suma los totales | Un entero | Igual que la anterior |

### `lambda`: dónde sí y dónde no

**Dónde sí:** expresiones mínimas, de un solo uso y locales, p. ej. `lambda registro: registro.critico` (el criterio que se le pasa a `filtrar_historial`) o las 5 reglas de `CRITERIOS_HISTORIAL`.

**Dónde no (y por qué):** el closure `modificador` **no** es una lambda aunque podría escribirse como una:

```python
modificador = lambda consumo_base: max(0, int(consumo_base * factor + 0.5))
```

No conviene porque la función (1) encierra una regla de negocio (redondeo *half-up* y piso en 0) que merece nombre y explicación; (2) se reutiliza y se prueba por separado; (3) con `def` los errores muestran `modificador` en lugar de `<lambda>`. Esta explicación también está como comentario en `logic/resources.py`, y la prueba `test_el_closure_tiene_nombre_propio_y_no_es_una_lambda` verifica que tiene nombre propio. Tampoco se usó lambda para `planificar_accion`: son 9 casos con lógica, y una lambda no puede contener sentencias ni `match`.

## 5. Partes puras e impuras

Una función es **pura** si (a) con los mismos argumentos devuelve siempre lo mismo y (b) no produce efectos observables fuera de ella (no imprime, no lee ni escribe archivos, no modifica nada que reciba ni variables globales).

### Funciones puras (todas las de `models/` y `logic/` salvo las dos impuras de abajo)

| Función | Por qué es pura |
|---|---|
| `limitar(valor)` | Solo calcula `max(0, min(100, valor))` |
| `aplicar_delta(recursos, ...)` | Construye unos `Recursos` **nuevos**; el recibido no cambia |
| `crear_modificador_consumo(factor)` | Solo crea y devuelve una función; no toca nada externo |
| `planificar_accion(accion, integrantes)` | Mismo `Accion` y mismos integrantes → mismo plan; no modifica nada |
| `elegir_evento(catalogo, tirada)` | El azar **no ocurre dentro**: la tirada llega como argumento |
| `efecto_de_opcion(evento, opcion, tirada)` | Igual: determinista dada la tirada |
| `ejecutar_turno(expedicion, accion, tirada_evento)` | Compone funciones puras y devuelve un estado nuevo |
| `calcular_puntuacion`, `formatear_reporte` | Calculan y devuelven un valor/texto; **no** escriben el archivo |

Además, todas las funciones de `ui/presentacion.py` son puras (`nivel_recurso`, `estilo_barra`, `texto_recurso`, `formatear_registro`, `calcular_geometria`, …): deciden *qué* mostrar sin importar Tkinter, y por eso se prueban sin abrir ventanas.

**Decisión de diseño para aislar el azar:** el azar es un efecto. En lugar de llamar a `random` dentro de la lógica, `tirar_dado()` es la única función impura de aleatoriedad y su resultado entra a la lógica como argumento (`tirada`). Así toda la lógica es determinista y se puede probar con valores fijos.

### Funciones impuras

| Función | Efecto que produce |
|---|---|
| `tirar_dado()` (`logic/expedition_service.py`) | Lee el generador aleatorio global (`random.random()`): dos llamadas con los mismos argumentos devuelven valores distintos |
| `exportar_reporte(expedicion, ruta)` (`logic/reports.py`) | **Escribe un archivo en disco** |
| `actualizar_indicadores`, `mostrar_mensaje`, `_anunciar_fin`, `_reiniciar`, `_exportar`, `_ajustar_tamano`, `_reservar_alto_eventos` (`ui/main_window.py`) | Modifican widgets, abren diálogos o escriben archivos |
| Métodos `actualizar`/`mostrar` de los paneles (`ui/components.py`) | Modifican widgets |

> Se evitó declarar pura una función que no lo es: por ejemplo `formatear_reporte` es pura **precisamente porque** la escritura al disco se separó en `exportar_reporte`.

## 6. Efectos secundarios que existen

1. **Azar:** `tirar_dado()`.
2. **Disco:** `exportar_reporte` (invocada desde `VentanaPrincipal._exportar`).
3. **Interfaz gráfica:** actualizar widgets, mostrar mensajes, tamaño de ventana.
4. **Diálogos del sistema:** `askyesno` (confirmar reinicio, ofrecer exportar) y `asksaveasfilename` (elegir dónde guardar).
5. **Referencia de estado en la ventana:** `self.expedicion` se reasigna con el estado nuevo. Es el **único** punto mutable del programa y está confinado a la capa visual.

Todos están en los bordes del sistema (capa visual y dos funciones nombradas); el núcleo de reglas no tiene ninguno.

## 7. Qué parte del estado se maneja de forma inmutable

**Todo el modelo:** `Recursos`, `Registro`, `Expedicion`, `Efecto`, `Evento`, `Opcion` y `Accion` son `frozen=True`. Intentar asignar un campo lanza `FrozenInstanceError`.

Cada cambio de estado crea una instancia nueva con `dataclasses.replace`, por ejemplo en `logic/resources.py`:

```python
def agregar_registro(expedicion, registro):
    return replace(expedicion, historial=expedicion.historial + (registro,))
```

`historial + (registro,)` crea una tupla nueva; la anterior queda intacta. `tests/test_immutability.py` comprueba, entre otras cosas, que tras ejecutar un turno el estado original **no cambió** y que el nuevo es un objeto distinto.

**Matiz honesto:** la inmutabilidad aquí no es "copiar por copiar". Cumple un fin concreto: poder comparar el estado antes/después, deshacer fácilmente, probar sin preparar entornos y evitar que un panel de la interfaz modifique por accidente el estado que usa otro. También tiene un límite: `frozen=True` es inmutabilidad *superficial*, por eso las colecciones son tuplas.

## 8. Closure implementado y para qué

`crear_modificador_consumo(factor)` en `logic/resources.py`:

```python
def crear_modificador_consumo(factor):
    def modificador(consumo_base):
        return max(0, int(consumo_base * factor + 0.5))   # factor viene del closure
    return modificador
```

- **Por qué es un closure real:** `modificador` usa `factor`, que **no es ni su parámetro ni una variable local**; la toma del entorno de la función que la creó y la sigue recordando después de que `crear_modificador_consumo` terminó. Los tests lo verifican con `modificador.__code__.co_freevars == ("factor",)` y `modificador.__closure__[0].cell_contents == 1.5`. Un test contrasta con una función anidada que *no* usa variables externas y por tanto **no** es closure.
- **Para qué sirve:** `consumo_proyectado` calcula `factor = FACTOR_CLIMA[clima] * FACTOR_DIFICULTAD[dificultad]`, crea el modificador y se lo pasa a `calcular_consumo` (función de orden superior). Así el consumo de la jornada (agua 6, alimentos 4, energía 4 de base) se escala x1.5 con tormenta y x1.25 en dificultad Difícil, sin repetir la regla en cada sitio. La interfaz reutiliza `consumo_proyectado` para mostrar el consumo previsto, por lo que lo que se ve y lo que ocurre no se desincronizan.

## 9. Qué partes sugirió la IA

**Prácticamente todo el código fuente fue generado por Claude (IA de Anthropic) a partir de las instrucciones de la estudiante:** arquitectura de tres capas, modelos, lógica, interfaz, pruebas y estos documentos. La estudiante tomó decisiones de producto (aceptar el diseño, incluir exportación de reportes, tema oscuro con oro eléctrico, delegar el balance) y reportó problemas al probar el programa en su computadora. Los detalles, con cada decisión, están en `bitacora-ia.md`.

ChatGPT se usó **solo** para obtener comandos de instalación y ejecución (descomprimir, `pip install`, `pytest`), no para escribir el código del proyecto.

## 10. Qué se corrigió o rechazó de la IA

Detalle completo, con quién detectó cada cosa, en `bitacora-ia.md`.

**Detectado y decidido por la estudiante** (al jugar y revisar la interfaz):
- El pie de la ventana quedaba tapado por la barra de tareas y algunos eventos se cortaban. Se rediseñó el tamaño de la ventana a partir del contenido.
- Notó que en algunos eventos aparecían 2 decisiones y en otros 3. Aclaración técnica: es **por diseño**: unos eventos tienen 2 decisiones (Tormenta, Zona peligrosa, Refugio, Emergencia) y otros 3 (Provisiones, Avería). Como en versiones anteriores el panel de eventos llegó a cortarse, no se puede asegurar si lo que vio entonces era el diseño o un recorte; la estudiante no recuerda en qué evento ocurrió. En la versión actual confirmó ver las tres opciones donde corresponde.
- Los botones de acciones se ocultaban durante un evento; **rechazó** ese comportamiento y pidió que se queden visibles (ahora se ven pero bloqueados mientras hay un evento).
- `python main.py` fallaba por ejecutarlo desde la carpeta equivocada (el ZIP se extrae anidado); se documentó `cd expedicion_zona_cero`.

**Detectado por la IA:**
- Un posible bloqueo del juego (sin acciones válidas): `descansar` ya no tiene requisitos.
- Pruebas de mutación mal planteadas y una prueba débil, reescritas.
- Al auditar contra la guía: faltaba en el código el fragmento que explica por qué no usar `lambda`; se añadió en `crear_modificador_consumo`. También se eliminaron dos importaciones sin uso.

**Verificación:** 351 pruebas con `pytest`, repartidas en 6 archivos (ver `README.md`).
- En el entorno de desarrollo (Python 3.12, pantalla virtual, instalación limpia con `pip install -r requirements.txt`): 351 pasaron.
- En el equipo de la estudiante (Windows): 350 pasaron en la Fase 5; las pruebas añadidas después **aún no se han ejecutado en su equipo**.
- Pruebas de mutación manuales: se rompió el código a propósito (ignorar decisiones, omitir registros del reporte, reiniciar conservando el historial…) y las 5 mutaciones probadas fueron detectadas.
- Un bot juega partidas completas con semillas fijas a través de la ventana real: toda partida termina en estado final coherente y los recursos nunca salen de 0–100.

**Limitaciones:** el tamaño de la ventana se verificó en pantallas virtuales de 1280×720 y 1366×768 y en el equipo de la estudiante, no en otros sistemas. El balance se evaluó con un bot simple (en 400 partidas ganó 339), no con jugadores reales. `frozen=True` es inmutabilidad superficial. No se usa `map`, `Union` ni `NamedTuple` (justificado en las secciones 2 y 4).

## 11. Qué se aprendió técnicamente

> **Nota:** esta sección tiene dos partes. La primera es lo que la estudiante indicó que hizo y aprendió. La segunda son conceptos que el proyecto aplica y que **aún debe estudiar antes de afirmarlos como aprendidos**; no se declaran aprendizajes que no se hayan dicho.

**Aprendizajes de la estudiante (según sus propias palabras):**
- Aprendió algunos comandos para trabajar con el proyecto: descomprimir el ZIP, entrar a la carpeta (`cd`), instalar dependencias (`pip install -r requirements.txt`), ejecutar las pruebas (`python -m pytest -q`) y abrir la aplicación (`python main.py`). Los obtuvo de Claude y de ChatGPT.
- Aprendió a **probar una aplicación como usuaria y reportar errores con evidencia**: jugó el juego, notó que la interfaz se cortaba y que no siempre aparecían tres decisiones, y lo reportó con capturas.
- Observó que las acciones y condiciones del juego tienen ventajas y desventajas (consumen o recuperan agua, alimentos y energía de forma distinta).

**Conceptos que el proyecto aplica y que debe estudiar (pendiente):**
- Aislar el azar: `tirada` entra como argumento a la lógica y por eso se puede probar con valores fijos.
- Estado inmutable con `dataclasses.replace`: cada función devuelve un estado nuevo y el anterior queda como comparación.
- Closure: `crear_modificador_consumo` recuerda `factor` sin variables globales ni clases.
- `match/case` con patrones de clase y guards frente a cadenas de `if`.
- Pureza como frontera: lo puro se prueba sin interfaz; los efectos (interfaz, disco, azar) están en los bordes.
- Cuándo no usar `lambda`: si la expresión esconde una regla de negocio, se reutiliza o se prueba, conviene `def`.

Para la exposición, `guion-video.md` incluye una tabla con preguntas probables y dónde mirar en el código para cada una.
