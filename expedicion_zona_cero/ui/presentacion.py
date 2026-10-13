"""Capa visual: funciones PURAS de presentación (no usan Tkinter).

Aquí se decide *qué* mostrar (textos, niveles, colores, filtros). Los widgets
de ``components.py`` solo se encargan de *dibujarlo*. Al no depender de Tkinter,
todo este módulo se puede probar sin abrir ninguna ventana.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Callable, Iterable, Mapping, Sequence

from logic.actions import planificar_accion
from logic.expedition_service import UMBRAL_ALERTA
from logic.reports import filtrar_historial
from models.events import Accion, Efecto
from models.expedition import (
    LIMITE_MAX,
    META_PROGRESO,
    EstadoMision,
    Expedicion,
    Registro,
)

# --------------------------------------------------------------------------
# Paleta: oscuro + oro eléctrico (naranja para alertas, turquesa de apoyo)
# --------------------------------------------------------------------------
PALETA: Mapping[str, str] = MappingProxyType(
    {
        "fondo": "#0B0E14",
        "panel": "#121722",
        "borde": "#262E42",
        "oro": "#FFC400",
        "oro_claro": "#FFD84D",
        "naranja": "#FF7A1A",
        "rojo": "#FF4D5E",
        "verde": "#2EE6A6",
        "turquesa": "#2FD4C8",
        "texto": "#E8ECF4",
        "tenue": "#8B94A8",
        "campo": "#161B26",
    }
)

NOMBRES_VISIBLES: Mapping[str, str] = MappingProxyType(
    {"agua": "AGUA", "alimentos": "ALIMENTOS", "energia": "ENERGÍA", "salud": "SALUD"}
)

ETIQUETAS_EFECTO: tuple[tuple[str, str], ...] = (
    ("agua", "agua"),
    ("alimentos", "alimentos"),
    ("energia", "energía"),
    ("salud", "salud"),
    ("progreso", "progreso"),
    ("integrantes", "integrantes"),
)

ETIQUETAS_TIPO: Mapping[str, str] = MappingProxyType(
    {
        "accion": "ACCIÓN",
        "evento": "EVENTO",
        "decision": "DECISIÓN",
        "turno": "TURNO",
        "sistema": "SISTEMA",
    }
)

NOMBRES_EXPEDICION: tuple[str, ...] = (
    "Alfa", "Beta", "Gamma", "Delta", "Épsilon", "Zeta", "Eta", "Theta",
)

# Acciones que ofrece el panel de controles: (etiqueta del botón, acción).
ACCIONES_UI: tuple[tuple[str, Accion], ...] = (
    ("Explorar", Accion("explorar")),
    ("Descansar", Accion("descansar")),
    ("Beber agua", Accion("consumir_recurso", "agua")),
    ("Racionar comida", Accion("consumir_recurso", "alimentos")),
    ("Recolectar agua", Accion("recolectar", "agua")),
    ("Recolectar comida", Accion("recolectar", "alimentos")),
    ("Atender emergencia", Accion("atender_emergencia")),
)

DIFICULTADES_UI: Mapping[str, str] = MappingProxyType(
    {"Normal": "normal", "Difícil": "dificil"}
)

UMBRAL_BAJO = 40  # por debajo de esto el recurso se muestra en naranja

# Criterios de filtrado del historial. Cada uno es un predicado
# ``Registro -> bool``; las lambdas son adecuadas porque cada criterio es una
# sola expresión sin lógica adicional.
CRITERIOS_HISTORIAL: Mapping[str, Callable[[Registro], bool]] = MappingProxyType(
    {
        "Todo": lambda registro: True,
        "Críticos": lambda registro: registro.critico,
        "Acciones": lambda registro: registro.tipo == "accion",
        "Eventos y decisiones": lambda registro: registro.tipo in ("evento", "decision"),
        "Turnos": lambda registro: registro.tipo == "turno",
    }
)


# --------------------------------------------------------------------------
# Recursos
# --------------------------------------------------------------------------
def nivel_recurso(valor: int) -> str:
    """Clasifica un recurso como ``"ok"``, ``"bajo"`` o ``"critico"``. (PURA)"""
    if valor <= UMBRAL_ALERTA:
        return "critico"
    if valor <= UMBRAL_BAJO:
        return "bajo"
    return "ok"


def estilo_barra(valor: int) -> str:
    """Estilo TtkBootstrap de la barra según el nivel del recurso. (PURA)

    ``primary`` es el oro del tema, ``warning`` el naranja y ``danger`` el rojo.
    """
    return {"ok": "primary", "bajo": "warning", "critico": "danger"}[nivel_recurso(valor)]


def color_nivel(valor: int) -> str:
    """Color de texto del valor de un recurso. (PURA)"""
    return {
        "ok": PALETA["texto"],
        "bajo": PALETA["naranja"],
        "critico": PALETA["rojo"],
    }[nivel_recurso(valor)]


def texto_recurso(valor: int) -> str:
    """Texto ``"80/100"`` de un recurso. (PURA)"""
    return f"{valor}/{LIMITE_MAX}"


# --------------------------------------------------------------------------
# Encabezado y estado de la misión
# --------------------------------------------------------------------------
def etiqueta_dia(expedicion: Expedicion) -> str:
    """Texto del día actual, sin superar el límite (``"DÍA 3 / 12"``). (PURA)"""
    return f"DÍA {min(expedicion.dia, expedicion.dia_limite)} / {expedicion.dia_limite}"


def etiqueta_estado(estado: EstadoMision) -> tuple[str, str]:
    """Texto y estilo (bootstyle) de la insignia de estado de la misión. (PURA)"""
    return {
        EstadoMision.EN_CURSO: ("EN CURSO", "@primary"),
        EstadoMision.COMPLETADA: ("COMPLETADA", "@success"),
        EstadoMision.FALLIDA: ("FALLIDA", "@danger"),
    }[estado]


def etiqueta_progreso(progreso: int, meta: int = LIMITE_MAX) -> str:
    """Texto del avance hacia la meta. (PURA)"""
    return f"PROGRESO  {progreso}/{meta}"


def texto_objetivo(expedicion: Expedicion) -> str:
    """Recordatorio del objetivo de la misión. (PURA)"""
    return (
        f"Objetivo: llegar a {META_PROGRESO} de progreso antes de que termine "
        f"el día {expedicion.dia_limite}."
    )


def estilo_boton_accion(accion: Accion) -> str:
    """Estilo (bootstyle) del botón de una acción. (PURA)

    La emergencia médica se destaca en naranja; el resto usa el oro del tema.
    """
    return "warning-outline" if accion.tipo == "atender_emergencia" else "primary-outline"


def nombre_expedicion(numero: int) -> str:
    """Nombre de la expedición número ``numero`` (1, 2, 3...). (PURA)"""
    if numero < 1:
        raise ValueError("El número de expedición debe ser al menos 1")
    indice = (numero - 1) % len(NOMBRES_EXPEDICION)
    vuelta = (numero - 1) // len(NOMBRES_EXPEDICION)
    sufijo = f" {vuelta + 1}" if vuelta else ""
    return f"Expedición {NOMBRES_EXPEDICION[indice]}{sufijo}"


def describir_accion(accion: Accion, integrantes: int) -> str:
    """Descripción de lo que haría una acción, con sus números reales. (PURA)

    Se apoya en :func:`logic.actions.planificar_accion`, así el texto nunca
    se desincroniza de las reglas de negocio.
    """
    plan = planificar_accion(accion, integrantes)
    return f"{plan.descripcion}\n{resumen_efecto(plan.efecto)}"


def texto_consumo(consumo: Mapping[str, int]) -> str:
    """Resumen del consumo previsto de la jornada. (PURA)"""
    return (
        f"Agua -{consumo['agua']}   Alimentos -{consumo['alimentos']}   "
        f"Energía -{consumo['energia']}"
    )


# --------------------------------------------------------------------------
# Tripulación
# --------------------------------------------------------------------------
def indicador_tripulacion(integrantes: int, total: int) -> str:
    """Puntos que representan a la tripulación: ``"●●●○"``. (PURA)"""
    vivos = max(0, min(integrantes, total))
    return "●" * vivos + "○" * (total - vivos)


def texto_clima(clima: str) -> str:
    """Nombre visible del clima. (PURA)"""
    return {"despejado": "Despejado", "tormenta": "TORMENTA"}.get(clima, clima.capitalize())


def texto_dificultad(dificultad: str) -> str:
    """Nombre visible de la dificultad. (PURA)"""
    return {"normal": "Normal", "dificil": "Difícil"}.get(dificultad, dificultad.capitalize())


# --------------------------------------------------------------------------
# Efectos, historial y filtros
# --------------------------------------------------------------------------
def resumen_efecto(efecto: Efecto) -> str:
    """Resume un efecto en texto: ``"+20 agua, -8 energía"``. (PURA)"""
    partes = [
        f"{getattr(efecto, campo):+d} {nombre}"
        for campo, nombre in ETIQUETAS_EFECTO
        if getattr(efecto, campo) != 0
    ]
    return ", ".join(partes)


def formatear_registro(registro: Registro) -> str:
    """Línea de texto de una entrada del historial. (PURA)"""
    marca = "(!) " if registro.critico else ""
    tipo = ETIQUETAS_TIPO.get(registro.tipo, registro.tipo.upper())
    return f"D{registro.dia:02d} {tipo:<8} {marca}{registro.descripcion}"


def etiqueta_tag(registro: Registro) -> str:
    """Nombre del estilo de texto que se aplica a una entrada. (PURA)"""
    return "critico" if registro.critico else registro.tipo


def aplicar_filtro(nombre: str, historial: Sequence[Registro]) -> tuple[Registro, ...]:
    """Filtra el historial con el criterio elegido en la interfaz. (PURA)

    Delega en :func:`logic.reports.filtrar_historial`, la función de orden
    superior que recibe el criterio como argumento.
    """
    if nombre not in CRITERIOS_HISTORIAL:
        raise ValueError(f"Filtro desconocido: {nombre!r}")
    return filtrar_historial(CRITERIOS_HISTORIAL[nombre], historial)


# --------------------------------------------------------------------------
# Tamaño de la ventana
# --------------------------------------------------------------------------
ANCHO_IDEAL = 1280
ALTO_IDEAL = 760
# Espacio que el sistema se queda: barra de título (~32 px) + barra de tareas
# (~48 px) + holgura. Se descuenta del alto de la pantalla.
MARGEN_ALTO_PANTALLA = 100
MARGEN_ANCHO_PANTALLA = 40


def calcular_geometria(
    req_ancho: int, req_alto: int, pantalla_ancho: int, pantalla_alto: int
) -> tuple[int, int]:
    """Tamaño inicial de la ventana ``(ancho, alto)`` según la pantalla. (PURA)

    Usa el tamaño ideal si la pantalla lo permite; si es más pequeña, se
    reduce, pero nunca por debajo del tamaño natural del contenido
    (``req_*``), que es lo mínimo que necesitan los widgets para verse completos.
    """
    ancho = max(req_ancho, min(ANCHO_IDEAL, pantalla_ancho - MARGEN_ANCHO_PANTALLA))
    alto = max(req_alto, min(ALTO_IDEAL, pantalla_alto - MARGEN_ALTO_PANTALLA))
    return ancho, alto


# --------------------------------------------------------------------------
# Fuentes
# --------------------------------------------------------------------------
def elegir_fuente(
    preferidas: Iterable[str], disponibles: Iterable[str], defecto: str
) -> str:
    """Primera fuente preferida que exista en el sistema. (PURA)

    La comparación ignora mayúsculas. Si ninguna está, devuelve ``defecto``.
    """
    existentes = {nombre.lower(): nombre for nombre in disponibles}
    for candidata in preferidas:
        if candidata.lower() in existentes:
            return existentes[candidata.lower()]
    return defecto
