#Capa lógica: servicio de la expedición (turnos, eventos y estado de la misión).


from __future__ import annotations

import random
from dataclasses import replace
from typing import Sequence

from models.events import (
    CATALOGO_EVENTOS,
    EFECTO_ACCIDENTE,
    PROBABILIDAD_EVENTO,
    Accion,
    Evento,
)
from models.expedition import (
    META_PROGRESO,
    EstadoMision,
    Expedicion,
    Recursos,
    Registro,
    ResultadoAccion,
)

from .actions import efecto_de_opcion, procesar_accion
from .resources import (
    FACTOR_CLIMA,
    FACTOR_DIFICULTAD,
    agregar_registro,
    aplicar_delta,
    aplicar_efecto,
    calcular_consumo,
    crear_modificador_consumo,
    penalizacion_por_agotamiento,
    resumir_efecto,
)

UMBRAL_ALERTA = 20  # un recurso por debajo de esto dispara una advertencia


# Creación y reinicio
def crear_expedicion(
    nombre: str = "Expedición Alfa", dificultad: str = "normal"
) -> Expedicion:

    return Expedicion(
        nombre=nombre,
        recursos=Recursos(agua=80, alimentos=80, energia=90, salud=100),
        dificultad=dificultad,
    )


def tirar_dado() -> float:
    #Número aleatorio en [0, 1). (IMPURA: depende del estado del generador.)
    return random.random()


def elegir_evento(catalogo: Sequence[Evento], tirada: float) -> Evento | None:
   
    if not 0.0 <= tirada < 1.0:
        raise ValueError("La tirada debe estar en el intervalo [0, 1)")
    if not catalogo or tirada >= PROBABILIDAD_EVENTO:
        return None
    indice = int(tirada / PROBABILIDAD_EVENTO * len(catalogo))
    return catalogo[indice]


def asignar_evento(expedicion: Expedicion, evento: Evento) -> Expedicion:
    nuevo = replace(expedicion, evento_actual=evento)
    return agregar_registro(
        nuevo,
        Registro(
            expedicion.dia, "evento", f"{evento.titulo}: {evento.descripcion}",
            critico=evento.critico,
        ),
    )


# Condiciones de la misión

def evaluar_estado(expedicion: Expedicion) -> EstadoMision:
    
    if expedicion.integrantes <= 0 or expedicion.recursos.salud <= 0:
        return EstadoMision.FALLIDA
    if expedicion.progreso >= META_PROGRESO:
        return EstadoMision.COMPLETADA
    if expedicion.dia > expedicion.dia_limite:
        return EstadoMision.FALLIDA
    return EstadoMision.EN_CURSO


def actualizar_estado(expedicion: Expedicion) -> Expedicion:
    """Recalcula el estado de la misión y lo registra si cambió. (PURA)"""
    nuevo_estado = evaluar_estado(expedicion)
    if nuevo_estado is expedicion.estado:
        return expedicion
    cerrado = replace(expedicion, estado=nuevo_estado)
    return agregar_registro(
        cerrado,
        Registro(
            expedicion.dia, "sistema",
            f"Misión {nuevo_estado.value.lower()}.", critico=True,
        ),
    )


def nivel_de_alerta(expedicion: Expedicion) -> str:
    """Nivel de aviso para la interfaz según la situación del equipo. (PURA)"""
    if expedicion.estado is EstadoMision.FALLIDA:
        return "error"
    if expedicion.estado is EstadoMision.COMPLETADA:
        return "success"
    r = expedicion.recursos
    if min(r.agua, r.alimentos, r.energia, r.salud) <= UMBRAL_ALERTA:
        return "warning"
    return "info"


# Turnos y eventos

def consumo_proyectado(expedicion: Expedicion) -> dict[str, int]:
    
    factor = FACTOR_CLIMA[expedicion.clima] * FACTOR_DIFICULTAD[expedicion.dificultad]
    return calcular_consumo(crear_modificador_consumo(factor))


def avanzar_turno(expedicion: Expedicion) -> Expedicion:
   
    consumo = consumo_proyectado(expedicion)

    recursos = aplicar_delta(
        expedicion.recursos,
        agua=-consumo["agua"],
        alimentos=-consumo["alimentos"],
        energia=-consumo["energia"],
    )
    penalizacion = penalizacion_por_agotamiento(recursos)
    recursos = aplicar_delta(recursos, salud=-penalizacion)

    detalle = (
        f"Fin del día {expedicion.dia}: consumo de agua {consumo['agua']}, "
        f"alimentos {consumo['alimentos']} y energía {consumo['energia']}"
        f" (clima: {expedicion.clima})."
    )
    if penalizacion:
        detalle += f" Sin suministros vitales: la salud baja {penalizacion}."

    avanzado = replace(
        expedicion,
        recursos=recursos,
        dia=expedicion.dia + 1,
        clima="despejado",
    )
    avanzado = agregar_registro(
        avanzado,
        Registro(
            expedicion.dia, "turno", detalle,
            consumido=sum(consumo.values()) + penalizacion,
            critico=penalizacion > 0,
        ),
    )
    return actualizar_estado(avanzado)


def resolver_evento(
    expedicion: Expedicion, clave_opcion: str, tirada: float
) -> ResultadoAccion:
    """Aplica la decisión elegida para el evento pendiente. (PURA)"""
    if expedicion.estado is not EstadoMision.EN_CURSO:
        return ResultadoAccion(expedicion, "La misión ya terminó.", False, "error")
    evento = expedicion.evento_actual
    if evento is None:
        return ResultadoAccion(expedicion, "No hay ningún evento pendiente.", False, "warning")

    opcion = next(filter(lambda o: o.clave == clave_opcion, evento.opciones), None)
    if opcion is None:
        return ResultadoAccion(
            expedicion, f"Opción desconocida: {clave_opcion!r}.", False, "error"
        )

    efecto = efecto_de_opcion(evento, opcion, tirada)
    consumido, recuperado = resumir_efecto(efecto)
    nuevo = replace(aplicar_efecto(expedicion, efecto), evento_actual=None)
    nuevo = agregar_registro(
        nuevo,
        Registro(
            expedicion.dia, "decision", f"{evento.titulo}: {opcion.etiqueta}.",
            consumido, recuperado, evento.critico,
        ),
    )
    nuevo = actualizar_estado(nuevo)

    mensaje = f"{evento.titulo}: {opcion.etiqueta}."
    if efecto.integrantes < 0:
        mensaje += " El equipo perdió un integrante."
    if efecto is EFECTO_ACCIDENTE:
        mensaje += " ¡Hubo un accidente!"
    return ResultadoAccion(nuevo, mensaje, True, nivel_de_alerta(nuevo))


def ejecutar_turno(
    expedicion: Expedicion, accion: Accion, tirada_evento: float
) -> ResultadoAccion:
    
    if expedicion.evento_actual is not None:
        return ResultadoAccion(
            expedicion, "Resuelve primero el evento pendiente.", False, "warning"
        )
    resultado = procesar_accion(expedicion, accion)
    if not resultado.valido:
        return resultado

    # Si la acción ya cumplió (o arruinó) la misión, no se consume la jornada.
    actual = actualizar_estado(resultado.expedicion)
    if actual.estado is EstadoMision.EN_CURSO:
        actual = avanzar_turno(actual)
    if actual.estado is EstadoMision.EN_CURSO:
        evento = elegir_evento(CATALOGO_EVENTOS, tirada_evento)
        if evento is not None:
            actual = asignar_evento(actual, evento)

    mensaje = resultado.mensaje
    if actual.evento_actual is not None:
        mensaje += f" ¡Evento: {actual.evento_actual.titulo}!"
    if actual.estado is not EstadoMision.EN_CURSO:
        mensaje += f" Misión {actual.estado.value.lower()}."
    return ResultadoAccion(actual, mensaje, True, nivel_de_alerta(actual))
