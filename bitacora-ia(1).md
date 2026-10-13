"""# BITÁCORA DE USO DE INTELIGENCIA ARTIFICIAL

**Proyecto:** Expedición: Zona Cero  
**Asignatura:** Programación Funcional — Unidades 1 y 2

## 1. Prompts usados

### Prompt maestro para Claude

Utilicé ChatGPT para elaborar un prompt a partir de la guía de la actividad integradora. Después, utilicé ese prompt con Claude para orientar el desarrollo de *Expedición: Zona Cero*.

El prompt solicitaba crear un simulador de supervivencia en Python con una interfaz gráfica, administración de recursos, eventos y decisiones. También indicaba que debían incorporarse conceptos de programación funcional, como funciones de orden superior, `match/case`, closures, inmutabilidad, funciones puras e impuras y el uso de `map`, `filter` o `reduce`.

### Indicaciones posteriores a Claude

Durante el desarrollo, utilicé indicaciones para revisar el avance del proyecto y solicitar ajustes cuando encontraba problemas.

Entre mis indicaciones estuvieron elegir una interfaz oscura con detalles en oro eléctrico, solicitar que se corrigiera la visualización de las opciones de los eventos y decidir que los botones de acción permanecieran visibles durante los eventos, aunque estuvieran deshabilitados temporalmente.

También utilicé ChatGPT para recibir orientación sobre comandos y ejecución del proyecto.

## 2. Fragmentos de código sugeridos por la IA

Claude generó la mayor parte del código y las pruebas del proyecto. Estos son algunos de los fragmentos que revisé.

### 2.1. Closure y función de orden superior

**Archivo:** `logic/resources.py`

```python
def crear_modificador_consumo(factor: float) -> Callable[[int], int]:
    if factor < 0:
        raise ValueError("El factor de consumo no puede ser negativo")

    def modificador(consumo_base: int) -> int:
        return max(0, int(consumo_base * factor + 0.5))

    return modificador


def calcular_consumo(
    modificador: Callable[[int], int],
    base: Mapping[str, int] = CONSUMO_BASE,
) -> dict[str, int]:
    return {
        nombre: modificador(valor)
        for nombre, valor in base.items()
    }
```

El primer fragmento implementa un closure porque la función interna conserva el valor de `factor`. El segundo es una función de orden superior porque recibe otra función como argumento y la aplica a los recursos.

### 2.2. Procesamiento de acciones con `match/case`

**Archivo:** módulo de lógica de acciones; la ruta exacta debe verificarse en el proyecto.

```python
match accion:
    case Accion(tipo="explorar"):
        ganado = progreso_exploracion(integrantes)
        return PlanAccion(
            Efecto(progreso=ganado, energia=-12, agua=-4),
            f"Exploraron la zona y avanzaron {ganado} puntos de progreso.",
            (("energia", 12), ("agua", 4)),
        )
    case Accion(tipo="descansar"):
        return PlanAccion(
            Efecto(energia=30, salud=5, alimentos=-4),
            "El equipo descansó: recuperó energía y algo de salud.",
            (),
        )
    case _:
        raise AccionInvalida(f"Acción desconocida: {accion.tipo!r}.")
```

Este código organiza las acciones del jugador y define las consecuencias correspondientes a cada caso.

### 2.3. Actualización inmutable del historial

**Archivo:** `logic/resources.py`

```python
def agregar_registro(expedicion: Expedicion, registro: Registro) -> Expedicion:
    return replace(
        expedicion,
        historial=expedicion.historial + (registro,)
    )
```

La función crea una nueva versión de la expedición con un registro adicional, sin modificar directamente el estado anterior.

### 2.4. Funciones impuras

**Archivo:** `logic/expedition_service.py`

```python
def tirar_dado() -> float:
    return random.random()
```

Genera un número aleatorio y depende del estado del generador.

**Archivo:** `logic/reports.py`

```python
def exportar_reporte(expedicion: Expedicion, ruta: str | Path) -> Path:
    destino = Path(ruta)
    destino.write_text(
        formatear_reporte(expedicion),
        encoding="utf-8"
    )
    return destino
```

Esta función escribe un archivo en el disco, por lo que produce un efecto secundario.

## 3. Qué acepté

Acepté las propuestas que consideré útiles para el funcionamiento del simulador y el cumplimiento de la actividad.

- La separación del proyecto en módulos para organizar los datos, la lógica y la interfaz.
- El uso de funciones de orden superior y closures para trabajar con los recursos.
- El uso de `match/case` para procesar las acciones.
- Las actualizaciones inmutables para conservar el estado anterior.
- Las pruebas automatizadas para comprobar diferentes comportamientos.
- El diseño oscuro con detalles en oro eléctrico.
- La posibilidad de exportar reportes de la expedición.

Acepté estas propuestas porque contribuían a organizar el código y aplicar los conceptos estudiados.

## 4. Qué modifiqué

Durante las pruebas, identifiqué problemas y comuniqué los ajustes que consideraba necesarios.

- **Interfaz gráfica:** señalé problemas de tamaño y distribución que dificultaban visualizar algunos elementos.
- **Opciones de los eventos:** informé que no lograba ver las tres decisiones en determinados momentos. Después de las correcciones, comprobé que aparecían las tres opciones en los eventos diseñados para tenerlas.
- **Botones de acción:** solicité que permanecieran visibles durante los eventos, aunque estuvieran deshabilitados temporalmente.

Mi intervención consistió en revisar el código, ejecutar el juego, identificar problemas y comunicar los ajustes necesarios. No afirmo haber modificado directamente cada fragmento de código.

## 5. Qué rechacé

Rechacé la propuesta de ocultar los botones de acción mientras había un evento pendiente.

Preferí que permanecieran visibles, aunque estuvieran deshabilitados temporalmente, porque quería que el jugador pudiera reconocer las acciones disponibles y comprender mejor la interfaz.

No tengo documentados otros rechazos específicos que pueda atribuir con certeza a mi participación.

## 6. Por qué acepté, modifiqué o rechacé las propuestas

Acepté las propuestas que ayudaban a cumplir los requisitos académicos, organizar el código y mejorar el funcionamiento del juego.

Solicité modificaciones cuando las pruebas mostraron dificultades, especialmente en la visualización de la interfaz y las opciones de los eventos. Rechacé ocultar los botones porque consideré que mantenerlos visibles facilitaba la comprensión de la interfaz.

Además, revisé los archivos del proyecto línea por línea y ejecuté el juego para comprobar su funcionamiento. Consideré importante verificar las propuestas de la IA en lugar de asumir que todo funcionaba correctamente por el simple hecho de haber sido generado.

Reconozco que Claude generó la mayor parte del código y las pruebas, mientras que mi participación consistió en revisar el proyecto, probar sus funciones, comunicar problemas y tomar decisiones sobre determinados aspectos de la interfaz.
"""

