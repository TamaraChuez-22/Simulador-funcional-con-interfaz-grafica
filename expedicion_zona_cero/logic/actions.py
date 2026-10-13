"""Capa lógica: procesamiento de acciones y eventos con ``match/case``."""

from __future__ import annotations

from dataclasses import dataclass, replace

from models.events import (
    EFECTO_ACCIDENTE,
    PROBABILIDAD_ACCIDENTE,
    Accion,
    Efecto,
    Evento,
    Opcion,
)
from models.expedition import EstadoMision, Expedicion, Registro, ResultadoAccion

from .resources import (
    agregar_registro,
    aplicar_efecto,
    faltantes,
    resumir_efecto,
)


class AccionInvalida(ValueError):
    """La acción pedida no existe o está mal formada."""


@dataclass(frozen=True)
class PlanAccion:
    """Qué hace una acción: su efecto, su descripción y sus requisitos mínimos."""

    efecto: Efecto
    descripcion: str
    requisitos: tuple[tuple[str, int], ...]


def progreso_exploracion(integrantes: int) -> int:
    return 4 * integrantes


def planificar_accion(accion: Accion, integrantes: int) -> PlanAccion:

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
        case Accion(tipo="consumir_recurso", parametro="agua"):
            return PlanAccion(
                Efecto(agua=-10, salud=6),
                "Racionaron agua para hidratar al equipo y recuperar salud.",
                (("agua", 10),),
            )
        case Accion(tipo="consumir_recurso", parametro="alimentos"):
            return PlanAccion(
                Efecto(alimentos=-10, energia=15),
                "Repartieron raciones de comida y recuperaron energía.",
                (("alimentos", 10),),
            )
        case Accion(tipo="consumir_recurso"):
            raise AccionInvalida(
                f"No se puede consumir {accion.parametro!r}: elige agua o alimentos."
            )
        case Accion(tipo="recolectar", parametro=recurso) if recurso in (
            "agua",
            "alimentos",
        ):
            return PlanAccion(
                Efecto(energia=-8, **{recurso: 30}),
                f"Recolectaron {recurso}: +30 a cambio de energía.",
                (("energia", 8),),
            )
        case Accion(tipo="recolectar"):
            raise AccionInvalida(
                f"No se puede recolectar {accion.parametro!r}: elige agua o alimentos."
            )
        case Accion(tipo="atender_emergencia"):
            return PlanAccion(
                Efecto(agua=-10, alimentos=-5, energia=-10, salud=25),
                "Atendieron una emergencia médica y recuperaron salud.",
                (("agua", 10), ("alimentos", 5), ("energia", 10)),
            )
        case _:
            raise AccionInvalida(f"Acción desconocida: {accion.tipo!r}.")


def procesar_accion(expedicion: Expedicion, accion: Accion) -> ResultadoAccion:
    
    if expedicion.estado is not EstadoMision.EN_CURSO:
        return ResultadoAccion(
            expedicion,
            "La misión ya terminó. Inicia una nueva expedición.",
            False,
            "error",
        )
    try:
        plan = planificar_accion(accion, expedicion.integrantes)
    except AccionInvalida as error:
        return ResultadoAccion(expedicion, str(error), False, "error")

    requisitos = dict(plan.requisitos)
    faltan = faltantes(expedicion.recursos, requisitos)
    if faltan:
        detalle = ", ".join(f"{n} (mínimo {requisitos[n]})" for n in faltan)
        return ResultadoAccion(
            expedicion, f"Recursos insuficientes: {detalle}.", False, "warning"
        )

    nuevo = aplicar_efecto(expedicion, plan.efecto)
    consumido, recuperado = resumir_efecto(plan.efecto)
    nuevo = agregar_registro(
        nuevo, Registro(expedicion.dia, "accion", plan.descripcion, consumido, recuperado)
    )
    return ResultadoAccion(nuevo, plan.descripcion, True, "info")


def motivo_no_disponible(expedicion: Expedicion, accion: Accion) -> str | None:
    
    if expedicion.estado is not EstadoMision.EN_CURSO:
        return "La misión ya terminó."
    if expedicion.evento_actual is not None:
        return "Resuelve primero el evento pendiente."
    try:
        plan = planificar_accion(accion, expedicion.integrantes)
    except AccionInvalida as error:
        return str(error)
    requisitos = dict(plan.requisitos)
    faltan = faltantes(expedicion.recursos, requisitos)
    if faltan:
        return "Falta: " + ", ".join(f"{n} (mínimo {requisitos[n]})" for n in faltan) + "."
    return None


def efecto_de_opcion(evento: Evento, opcion: Opcion, tirada: float) -> Efecto:
    
    match (evento.tipo, opcion.clave):
        case ("tormenta", "avanzar"):
            return replace(opcion.efecto, clima="tormenta")
        case ("zona_peligrosa", "ruta_corta") if tirada < PROBABILIDAD_ACCIDENTE:
            return EFECTO_ACCIDENTE
        case ("emergencia", "ignorar"):
            return replace(opcion.efecto, integrantes=-1)
        case _:
            return opcion.efecto
