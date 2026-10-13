#Capa de datos: estado de la expedición.


from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum

from .events import Evento


# Constantes del dominio

LIMITE_MIN = 0
LIMITE_MAX = 100
META_PROGRESO = 100
INTEGRANTES_INICIALES = 4
NOMBRES_RECURSOS = ("agua", "alimentos", "energia", "salud")
CLIMAS = ("despejado", "tormenta")
DIFICULTADES = ("normal", "dificil")


class EstadoMision(Enum):
    """Estado global de la misión."""

    EN_CURSO = "En curso"
    COMPLETADA = "Completada"
    FALLIDA = "Fallida"


@dataclass(frozen=True)
class Recursos:

    agua: int
    alimentos: int
    energia: int
    salud: int

    def __post_init__(self) -> None:
        for campo in fields(self):
            valor = getattr(self, campo.name)
            if isinstance(valor, bool) or not isinstance(valor, int):
                raise TypeError(f"{campo.name} debe ser un entero, no {valor!r}")
            if not LIMITE_MIN <= valor <= LIMITE_MAX:
                raise ValueError(
                    f"{campo.name} debe estar entre {LIMITE_MIN} y {LIMITE_MAX}, "
                    f"recibido {valor}"
                )


@dataclass(frozen=True)
class Registro:

    dia: int
    tipo: str          # "accion" | "evento" | "decision" | "turno" | "sistema"
    descripcion: str
    consumido: int = 0
    recuperado: int = 0
    critico: bool = False


@dataclass(frozen=True)
class Expedicion:
    """Estado completo (e inmutable) de una expedición."""

    nombre: str
    recursos: Recursos
    dia: int = 1
    dia_limite: int = 12
    integrantes: int = INTEGRANTES_INICIALES
    progreso: int = 0
    estado: EstadoMision = EstadoMision.EN_CURSO
    clima: str = "despejado"
    dificultad: str = "normal"
    evento_actual: Evento | None = None
    historial: tuple[Registro, ...] = ()

    def __post_init__(self) -> None:
        if self.dia < 1:
            raise ValueError("El día debe ser al menos 1")
        if self.dia_limite < 1:
            raise ValueError("El límite de días debe ser al menos 1")
        if self.integrantes < 0:
            raise ValueError("Los integrantes no pueden ser negativos")
        if not LIMITE_MIN <= self.progreso <= META_PROGRESO:
            raise ValueError(f"El progreso debe estar entre 0 y {META_PROGRESO}")
        if self.clima not in CLIMAS:
            raise ValueError(f"Clima desconocido: {self.clima!r}")
        if self.dificultad not in DIFICULTADES:
            raise ValueError(f"Dificultad desconocida: {self.dificultad!r}")
        if not isinstance(self.historial, tuple):
            raise TypeError("El historial debe ser una tupla (inmutable)")


@dataclass(frozen=True)
class ResultadoAccion:


    expedicion: Expedicion
    mensaje: str
    valido: bool = True
    nivel: str = "info"
