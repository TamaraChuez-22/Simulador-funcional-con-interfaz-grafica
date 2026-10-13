# Análisis funcional — Expedición: Zona Cero

**Asignatura:** Programación Funcional (Unidades 1 y 2)  
**Estudiante:** Tamara Alejandra Chuez Sanchez  
**Carrera:** Software  

## 1. Problema que resuelve la aplicación

Desarrollé el proyecto **Expedición: Zona Cero** con ayuda de herramientas de inteligencia artificial. Es un simulador de supervivencia en el que debo administrar los recursos de una expedición formada por cuatro integrantes. El objetivo es alcanzar 100 puntos de progreso en un máximo de 12 días, procurando mantener los niveles de agua, alimentos, energía y salud.

Durante la partida, selecciono acciones y puedo enfrentarme a eventos que requieren tomar decisiones, como tormentas, hallazgos de provisiones, averías, zonas peligrosas y emergencias médicas. Las decisiones influyen en los recursos y en el desarrollo de la expedición.

Con este proyecto relacioné los conceptos de programación funcional con una aplicación práctica, porque las acciones y los eventos transforman el estado de la expedición y generan nuevos resultados.

## 2. Estructuras de datos utilizadas

En el proyecto se utilizaron estructuras de datos que representan los elementos y el estado de la expedición. Entre las principales identifiqué las siguientes:

| Estructura | Archivo | Función |
|---|---|---|
| `Recursos` | `models/expedition.py` | Representa el agua, los alimentos, la energía y la salud. |
| `Registro` | `models/expedition.py` | Almacena información sobre las acciones realizadas durante la partida. |
| `Expedicion` | `models/expedition.py` | Contiene el estado general de la expedición, el día, el progreso, los recursos y el historial. |
| `ResultadoAccion` | `models/expedition.py` | Representa el resultado de una operación. |
| `EstadoMision` | `models/expedition.py` | Identifica si la misión está en curso, completada o fallida mediante un `Enum`. |
| `Efecto` | `models/events.py` | Define los cambios que una acción o decisión puede producir. |
| `Opcion` | `models/events.py` | Representa una alternativa que puedo seleccionar durante un evento. |
| `Evento` | `models/events.py` | Describe las situaciones que pueden aparecer durante la expedición. |
| `Accion` | `models/events.py` | Representa la acción elegida por el jugador. |

Para representar estas estructuras se utilizaron clases de datos (`dataclass`). En los modelos correspondientes se aplicó `frozen=True`, que impide reasignar sus atributos después de crear una instancia.

También se utilizaron tuplas para colecciones como el historial y las opciones de los eventos, y `MappingProxyType` para disponer de configuraciones de solo lectura.

El proyecto está organizado en tres capas:

- **`models/`:** contiene los modelos de datos.
- **`logic/`:** contiene las reglas y operaciones del juego.
- **`ui/`:** se encarga de la interfaz gráfica.

Esta organización permite separar los datos, la lógica y la presentación.

## 3. Dónde apliqué los contenidos de la Unidad 1

**Funciones de orden superior.** En `logic/resources.py` identifiqué las funciones `calcular_consumo` y `aplicar_a_recursos`, que permiten aplicar transformaciones a los recursos mediante funciones recibidas como argumentos. En `logic/reports.py`, las funciones `filtrar_historial` y `ordenar_historial` permiten procesar el historial utilizando diferentes criterios.

**Estructuras de selección con `match/case`.** En el archivo `logic/actions.py`, las funciones `planificar_accion` y `efecto_de_opcion` utilizan `match/case` para reconocer las acciones y decisiones del jugador. Cada caso aplica una regla diferente, mientras que el caso comodín permite manejar situaciones no contempladas.

**Modelado con `dataclass`.** En los archivos de `models/` se representan los recursos, los eventos, las acciones y el estado de la expedición. De esta manera, la información queda organizada en estructuras con responsabilidades definidas.

**Programación funcional e imperativa.** En `logic/resources.py`, las funciones `consumo_total_funcional` y `consumo_total_imperativo` permiten comparar dos maneras de resolver el mismo cálculo. La versión imperativa utiliza bucles y un acumulador, mientras que la funcional emplea `reduce` para obtener el total.

Esta comparación me permitió observar que un mismo problema puede resolverse con diferentes estilos de programación y que cada enfoque tiene características que conviene comprender antes de elegirlo.

## 4. Dónde apliqué los contenidos de la Unidad 2

**Funciones lambda.** En `logic/reports.py` se utilizan expresiones lambda para definir criterios breves de procesamiento del historial. También aparecen en `ui/presentacion.py`, en los criterios utilizados para filtrar registros, y en las operaciones de reducción.

**Closures.** En `logic/resources.py` se implementó `crear_modificador_consumo(factor)`, que devuelve una función interna capaz de conservar el valor de `factor` después de que termina la ejecución de la función externa. Este mecanismo permite ajustar el consumo de recursos según las condiciones de la expedición.

**Inmutabilidad.** Se aplica en los modelos de datos mediante `frozen=True` y en las operaciones que generan nuevas instancias en lugar de modificar directamente las anteriores. Este concepto se relaciona con las pruebas del archivo `tests/test_immutability.py`.

**Funciones puras e impuras.** La lógica del juego separa los cálculos y las transformaciones del estado de las operaciones que interactúan con elementos externos, como el generador aleatorio, los archivos y la interfaz gráfica.

**`filter`.** En `logic/resources.py` y `logic/reports.py` se utiliza para seleccionar elementos que cumplen determinadas condiciones, como recursos que no alcanzan ciertos requisitos o registros que coinciden con un criterio.

**`reduce`.** En `logic/resources.py`, `consumo_total_funcional` utiliza `reduce` para acumular valores. En `logic/reports.py`, las funciones `total_consumido` y `total_recuperado` permiten obtener totales a partir del historial.

En el proyecto no se utilizó `map`. Para algunas transformaciones se prefirieron las comprensiones de diccionarios, que permiten expresar de forma directa cómo se construye una colección nueva. En este caso, `filter` y `reduce` permitieron trabajar con la selección y la acumulación de datos.

## 5. Partes puras e impuras del programa

Al revisar el código, identifiqué que las funciones puras se encargan principalmente de realizar cálculos y devolver resultados sin modificar el estado recibido ni producir efectos externos.

Entre los ejemplos se encuentran:

- `limitar`, que restringe un valor a un intervalo determinado.
- `aplicar_delta`, que calcula nuevos valores para los recursos.
- `crear_modificador_consumo`, que crea y devuelve una función.
- `planificar_accion`, que determina los efectos de una acción.
- `elegir_evento`, que recibe la tirada aleatoria como argumento y selecciona un evento.
- `ejecutar_turno`, que combina operaciones de la lógica para producir un nuevo estado.
- `formatear_reporte`, que construye el texto de un reporte sin guardarlo en un archivo.

También se utilizan funciones de presentación que calculan textos, niveles, estilos o dimensiones sin manipular directamente los componentes gráficos.

Entre las funciones impuras identifiqué:

- `tirar_dado()`, porque obtiene un valor del generador aleatorio.
- `exportar_reporte()`, porque escribe información en el disco.
- Los métodos de la interfaz que actualizan componentes, muestran mensajes, abren ventanas de diálogo o cambian el tamaño de la ventana.

Esta separación permite mantener las reglas del juego más fáciles de probar, ya que la mayoría de los cálculos no necesita interactuar directamente con la interfaz ni con archivos externos.

## 6. Efectos secundarios existentes

En la aplicación identifiqué varios efectos secundarios necesarios para que el simulador funcione:

1. **Generación aleatoria:** `tirar_dado()` obtiene valores que se utilizan para determinar la aparición de eventos y sus resultados.
2. **Escritura de archivos:** `exportar_reporte()` guarda el reporte de la expedición en la ubicación seleccionada.
3. **Actualización de la interfaz:** los componentes gráficos cambian para mostrar los recursos, el historial, las decisiones y el estado actual del juego.
4. **Diálogos del sistema:** se muestran cuadros de confirmación y selección de archivos, por ejemplo, al reiniciar o exportar un reporte.
5. **Actualización del estado de la ventana:** la interfaz asigna a `self.expedicion` el nuevo estado que devuelve la lógica del juego.

Estos efectos son necesarios para permitir la interacción del jugador, visualizar los resultados y conservar los reportes. La lógica central se mantiene separada de estas operaciones siempre que es posible.

## 7. Parte del estado que se manejó de forma inmutable

En el proyecto se aplicó la inmutabilidad principalmente a los modelos que representan la expedición, los recursos, los registros, los eventos, las opciones, las acciones y sus efectos.

Por ejemplo, en la función `agregar_registro`, ubicada en `logic/resources.py` según la organización del proyecto, se utiliza `replace` para crear una nueva instancia de la expedición con un historial actualizado:

```python
def agregar_registro(expedicion, registro):
    return replace(
        expedicion,
        historial=expedicion.historial + (registro,)
    )
```

En este caso, `historial + (registro,)` genera una tupla nueva que incluye el registro agregado. La expedición original conserva su historial anterior.

Para comprobar este comportamiento, el proyecto incluye pruebas en `tests/test_immutability.py`, destinadas a verificar que las operaciones generen un estado nuevo y que el estado original conserve sus valores.

Comprendí que esta forma de trabajar ayuda a evitar modificaciones accidentales y facilita la comparación entre el estado anterior y el posterior a una acción. También observé que `frozen=True` proporciona inmutabilidad superficial, por lo que es importante utilizar colecciones inmutables cuando se necesita proteger el contenido interno.

## 8. Closure implementado y para qué sirve

El closure se implementó mediante `crear_modificador_consumo(factor)`, ubicada en `logic/resources.py`.

```python
def crear_modificador_consumo(factor):
    def modificador(consumo_base):
        return max(0, int(consumo_base * factor + 0.5))
    return modificador
```

Identifiqué que se trata de un closure porque la función interna `modificador` utiliza la variable `factor` de la función externa. Aunque `crear_modificador_consumo` termine su ejecución, la función devuelta conserva el valor de ese factor.

Su finalidad es ajustar el consumo base de los recursos según condiciones como el clima y la dificultad. En lugar de repetir el cálculo en diferentes partes del programa, se crea un modificador que puede reutilizarse.

Este ejemplo también se relaciona con las funciones de orden superior, porque la función creada se puede pasar a `calcular_consumo`, también ubicada en `logic/resources.py`, para aplicar el ajuste a los diferentes recursos.

La validación de este concepto se encuentra en `tests/test_closures.py`, donde se comprueba que la función interna conserva la variable externa `factor` y funciona como un closure.

## 9. Partes sugeridas por la inteligencia artificial

Claude generó gran parte del código fuente del proyecto a partir de las instrucciones elaboradas con ayuda de ChatGPT y de las indicaciones que fui proporcionando. La ayuda de la inteligencia artificial incluyó los modelos de datos, la lógica del juego, la interfaz gráfica, las pruebas y parte de la documentación.

También se propuso una organización por capas para separar los modelos, la lógica y la interfaz. En el código se incorporaron conceptos de programación funcional como funciones de orden superior, `match/case`, `lambda`, closures, inmutabilidad, funciones puras, `filter` y `reduce`.

Mi participación consistió en proporcionar las instrucciones de la actividad, tomar decisiones sobre el diseño, revisar el código y comprobar el comportamiento de la aplicación. Además, utilicé ChatGPT para obtener orientación sobre los comandos necesarios para instalar dependencias, ejecutar el programa y realizar pruebas.

## 10. Qué corregí o rechacé de las sugerencias de la IA

Durante las pruebas del simulador detecté aspectos de la interfaz que necesitaban ajustes. Uno de ellos fue el tamaño de la ventana, ya que parte del contenido podía quedar cortado o cubierto por la barra de tareas. Informé del problema para que se revisara la distribución de los componentes.

También solicité que los botones de acciones permanecieran visibles durante los eventos. No quería que desaparecieran, por lo que se ajustó el comportamiento para que siguieran mostrándose, pero deshabilitados mientras existiera una decisión pendiente.

Otro aspecto que revisé fue la visualización de las opciones de los eventos. En la versión actual comprobé que aparecen las tres opciones en los eventos que están diseñados para tener tres alternativas. No todos los eventos tienen tres opciones, porque algunos cuentan con dos según las reglas del juego.

Además, tuve que considerar la ubicación correcta desde la que se ejecuta el programa, ya que ejecutarlo desde una carpeta equivocada puede provocar errores al buscar los archivos del proyecto.

Durante la revisión técnica con ayuda de la IA también se identificaron aspectos relacionados con las acciones disponibles, algunas pruebas y las importaciones innecesarias. Se mejoraron, además, explicaciones del código relacionadas con el uso de `lambda`.

No acepté todas las propuestas automáticamente: revisé el comportamiento de la aplicación, indiqué los problemas que encontré y solicité ajustes cuando el resultado no coincidía con lo que esperaba. Los detalles de estas interacciones se documentan en `bitacora-ia.md`.

## 11. Qué aprendí técnicamente

Con este proyecto aprendí a trabajar con una aplicación de Python que combina una interfaz gráfica con una lógica organizada en módulos. También practiqué comandos para instalar dependencias, entrar en la carpeta correcta, ejecutar el programa y lanzar pruebas.

Al revisar el código, pude identificar cómo se utilizan las funciones de orden superior, `match/case`, `lambda`, los closures, `filter` y `reduce`. Asimismo, comprendí mejor la diferencia entre una función que calcula un resultado y otra que produce efectos secundarios, como escribir un archivo o modificar la interfaz.

Otro aprendizaje importante fue la inmutabilidad. Comprendí que crear un nuevo estado en lugar de modificar directamente el anterior ayuda a mantener un comportamiento más controlado y facilita las pruebas.

Finalmente, aprendí que utilizar inteligencia artificial para desarrollar un proyecto no significa aceptar todas sus propuestas sin revisarlas. Es necesario comprobar el funcionamiento del programa, identificar errores, comunicar los problemas y verificar que los cambios realizados respondan a los requisitos de la actividad.
