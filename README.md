# Expedición: Zona Cero

Simulador de expedición de supervivencia con interfaz gráfica, hecho en **Python** con **Tkinter** y **TtkBootstrap**.
Proyecto de la actividad integradora de **Programación Funcional** (Unidades 1 y 2), UPSE.

Eres el jefe de una expedición de 4 personas. Tienes **12 días** para llegar a **100 de progreso** sin quedarte sin agua, comida, energía ni salud. Cada día eliges una acción y, con algo de suerte (o mala suerte), aparece un evento que te obliga a decidir.

## Requisitos

- Python **3.10 o superior** (se usa `match/case`).
- Tkinter (viene con Python; en Windows, al instalar Python marca la opción *tcl/tk and IDLE*).
- Las librerías de `requirements.txt` (`ttkbootstrap`, `pytest`).

## Instalación y ejecución (Windows PowerShell)

El ZIP se extrae dentro de otra carpeta. Entra a la carpeta que contiene `main.py`:

```powershell
cd expedicion_zona_cero
python -m pip install -r requirements.txt
python main.py
```

Si `python main.py` dice que no encuentra el archivo, no estás dentro de la carpeta correcta: usa `dir main.py` para comprobarlo.

## Pruebas

```powershell
python -m pytest -q
```

Hay **351 pruebas** (resultado en el equipo donde se desarrolló: Python 3.12 con pantalla virtual). Las pruebas de la ventana (`test_ui_smoke.py`, `test_integracion.py`) se omiten solas si no hay Tkinter o pantalla; el resto no necesita interfaz.

| Archivo | Qué comprueba |
|---|---|
| `tests/test_logic.py` | Reglas del juego: acciones, eventos, turnos, estados, reportes |
| `tests/test_immutability.py` | Que los estados no se pueden modificar y que cada cambio crea uno nuevo |
| `tests/test_closures.py` | Que `crear_modificador_consumo` es un closure real |
| `tests/test_ui_presentacion.py` | Funciones puras de presentación (textos, colores, filtros, geometría) |
| `tests/test_ui_smoke.py` | La ventana real: botones, eventos, fin de misión, exportación |
| `tests/test_integracion.py` | Partidas completas de un bot a través de la ventana real |

## Cómo se juega

- **Acciones** (una por jornada): Explorar, Descansar, Beber agua, Racionar comida, Recolectar agua, Recolectar comida, Atender emergencia. Un botón se deshabilita si no alcanzan los recursos; pasa el cursor por encima para ver el motivo.
- **Eventos**: al amanecer puede aparecer uno (75 % de probabilidad). Mientras haya un evento pendiente debes elegir una decisión; las acciones siguen visibles pero bloqueadas.
- **Fin de jornada**: se consumen agua, alimentos y energía. La tormenta multiplica el consumo (x1.5) y la dificultad *Difícil* también (x1.25).
- **Ganas** al llegar a 100 de progreso. **Pierdes** si la salud llega a 0, si no queda nadie o si pasa el día 12.
- **Exportar reporte** guarda un `.txt` con el resultado, la puntuación y todo el historial. **Nueva expedición** reinicia la partida.
- El panel **Historial** se puede filtrar (Todo, Críticos, Acciones, Eventos y decisiones, Turnos).

Valores iniciales: agua 80, alimentos 80, energía 90, salud 100. Exploración: +4 de progreso por integrante.

## Estructura (tres capas)

```
expedicion_zona_cero/
├── main.py                  Punto de entrada
├── models/                  CAPA DE DATOS: dataclasses inmutables
│   ├── expedition.py        Recursos, Registro, Expedicion, ResultadoAccion
│   └── events.py            Efecto, Opcion, Evento, Accion y catálogo de eventos
├── logic/                   CAPA LÓGICA: reglas del dominio (funciones puras)
│   ├── resources.py         Recursos, consumo, closure, filter/reduce
│   ├── actions.py           match/case para acciones y decisiones
│   ├── expedition_service.py  Turnos, eventos, estado de la misión
│   └── reports.py           Historial, puntuación y reporte
├── ui/                      CAPA VISUAL: Tkinter + TtkBootstrap
│   ├── presentacion.py      Funciones puras de presentación (sin Tkinter)
│   ├── components.py        Paneles y widgets
│   └── main_window.py       Ventana principal y callbacks cortos
└── tests/
```

Regla de dependencias: `ui` usa `logic` y `models`; `logic` usa `models`; `models` no importa de `logic` ni de `ui`. Los callbacks de la ventana solo llaman a la capa lógica y redibujan.

## Dónde está cada concepto de la guía

| Concepto | Dónde |
|---|---|
| Función de orden superior | `logic/resources.py: aplicar_a_recursos`, `calcular_consumo`; `logic/reports.py: filtrar_historial`, `ordenar_historial` |
| `match/case` | `logic/actions.py: planificar_accion` y `efecto_de_opcion` |
| `dataclass` | `models/` (todas con `frozen=True`) |
| Funcional vs imperativo | `logic/resources.py: consumo_total_imperativo` y `consumo_total_funcional` |
| `lambda` (y cuándo no) | `logic/reports.py: eventos_criticos`; `ui/presentacion.py: CRITERIOS_HISTORIAL`; explicación de por qué no en `crear_modificador_consumo` |
| Closure | `logic/resources.py: crear_modificador_consumo` |
| Inmutabilidad | `models/` + `dataclasses.replace` en `logic/` |
| Pureza y efectos secundarios | `analisis-funcional.md`, sección 5 y 6 |
| `filter` y `reduce` | `logic/resources.py: faltantes`; `logic/reports.py: total_consumido`, `total_recuperado` |

## Documentos de la entrega

- `analisis-funcional.md`: análisis técnico de la solución.
- `bitacora-ia.md`: registro del uso de IA.
- `enlace-video.txt`.


- Las pruebas de interfaz se ejecutaron con una pantalla virtual y en el equipo de la estudiante (Windows); no se probó en otros sistemas ni resoluciones.
- Las partidas tienen azar; los resultados varían entre partidas.
