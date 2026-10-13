"""Capa lógica: reglas de recursos."""

from __future__ import annotations

from dataclasses import replace
from functools import reduce
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from models.events import Efecto
from models.expedition import (
    LIMITE_MAX,
    LIMITE_MIN,
    META_PROGRESO,
    NOMBRES_RECURSOS,
    Expedicion,
    Recursos,
    Registro,
)

# Parámetros de balance. MappingProxyType da una vista de solo lectura

CONSUMO_BASE: Mapping[str, int] = MappingProxyType(
    {"agua": 6, "alimentos": 4, "energia": 4}
)
FACTOR_CLIMA: Mapping[str, float] = MappingProxyType(
    {"despejado": 1.0, "tormenta": 1.5}
)
FACTOR_DIFICULTAD: Mapping[str, float] = MappingProxyType(
    {"normal": 1.0, "dificil": 1.25}
)
PENALIZACION_SALUD = 15  # salud perdida por turno por cada recurso vital en 0


# Límites y transformaciones de recursos

def limitar(valor: int) -> int:
    """Mantiene un valor dentro del rango válido [0, 100]. (PURA)"""
    return max(LIMITE_MIN, min(LIMITE_MAX, valor))


def aplicar_delta(
    recursos: Recursos,
    *,
    agua: int = 0,
    alimentos: int = 0,
    energia: int = 0,
    salud: int = 0,
) -> Recursos:
    #Devuelve NUEVOS recursos sumando los cambios indicados. (PURA)

    #El resultado se limita a [0, 100], por lo que nunca puede ser negativo.
    return Recursos(
        agua=limitar(recursos.agua + agua),
        alimentos=limitar(recursos.alimentos + alimentos),
        energia=limitar(recursos.energia + energia),
        salud=limitar(recursos.salud + salud),
    )


def aplicar_a_recursos(
    transformacion: Callable[[str, int], int], recursos: Recursos
) -> Recursos:
   
    nuevos = {
        nombre: limitar(transformacion(nombre, getattr(recursos, nombre)))
        for nombre in NOMBRES_RECURSOS
    }
    return Recursos(**nuevos)


# Consumo por turno: closure + función de orden superior

def crear_modificador_consumo(factor: float) -> Callable[[int], int]:
    if factor < 0:
        raise ValueError("El factor de consumo no puede ser negativo")

    def modificador(consumo_base: int) -> int:
        return max(0, int(consumo_base * factor + 0.5))  # redondeo half-up

    return modificador


def calcular_consumo(
    modificador: Callable[[int], int],
    base: Mapping[str, int] = CONSUMO_BASE,
) -> dict[str, int]:
   
    return {nombre: modificador(valor) for nombre, valor in base.items()}


# Comparación imperativa vs funcional (mismo problema, dos estilos)

def consumo_total_imperativo(consumos: Sequence[Mapping[str, int]]) -> int:
    """Suma todo el consumo de una serie de turnos con bucles y acumulador."""
    total = 0
    for consumo_turno in consumos:
        for valor in consumo_turno.values():
            total += valor
    return total


def consumo_total_funcional(consumos: Sequence[Mapping[str, int]]) -> int:
    """Mismo cálculo con ``reduce``: sin variables mutables intermedias."""
    return reduce(lambda acumulado, turno: acumulado + sum(turno.values()), consumos, 0)


# Validación de requisitos

def faltantes(recursos: Recursos, requisitos: Mapping[str, int]) -> tuple[str, ...]:
    
    return tuple(
        filter(lambda nombre: getattr(recursos, nombre) < requisitos[nombre], requisitos)
    )


def penalizacion_por_agotamiento(recursos: Recursos) -> int:
    """Salud que se pierde por turno si falta agua y/o alimentos. (PURA)"""
    agotados = tuple(
        filter(lambda nombre: getattr(recursos, nombre) == 0, ("agua", "alimentos"))
    )
    return len(agotados) * PENALIZACION_SALUD


# Efectos sobre la expedición (siempre devuelven un estado nuevo)

def resumir_efecto(efecto: Efecto) -> tuple[int, int]:
    """Devuelve ``(consumido, recuperado)`` en puntos de recursos. (PURA)"""
    valores = (efecto.agua, efecto.alimentos, efecto.energia, efecto.salud)
    consumido = sum(-valor for valor in valores if valor < 0)
    recuperado = sum(valor for valor in valores if valor > 0)
    return consumido, recuperado


def aplicar_efecto(expedicion: Expedicion, efecto: Efecto) -> Expedicion:
    
    recursos = aplicar_delta(
        expedicion.recursos,
        agua=efecto.agua,
        alimentos=efecto.alimentos,
        energia=efecto.energia,
        salud=efecto.salud,
    )
    return replace(
        expedicion,
        recursos=recursos,
        progreso=max(0, min(META_PROGRESO, expedicion.progreso + efecto.progreso)),
        integrantes=max(0, expedicion.integrantes + efecto.integrantes),
        clima=efecto.clima if efecto.clima is not None else expedicion.clima,
    )


def agregar_registro(expedicion: Expedicion, registro: Registro) -> Expedicion:
   
    return replace(expedicion, historial=expedicion.historial + (registro,))
