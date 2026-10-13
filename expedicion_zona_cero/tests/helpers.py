"""Utilidades compartidas por los tests (no son tests)."""

from __future__ import annotations

from dataclasses import replace

from models.events import CATALOGO_EVENTOS, Evento
from models.expedition import Expedicion, Recursos
from logic.expedition_service import crear_expedicion


def evento_por_tipo(tipo: str) -> Evento:
    """Busca un evento del catálogo por su tipo."""
    return next(evento for evento in CATALOGO_EVENTOS if evento.tipo == tipo)


def expedicion_con(**cambios) -> Expedicion:
    """Expedición inicial con campos de primer nivel reemplazados."""
    return replace(crear_expedicion(), **cambios)


def expedicion_con_recursos(
    agua: int = 80, alimentos: int = 80, energia: int = 90, salud: int = 100, **cambios
) -> Expedicion:
    """Expedición inicial con recursos concretos (y otros cambios opcionales)."""
    recursos = Recursos(agua=agua, alimentos=alimentos, energia=energia, salud=salud)
    return replace(crear_expedicion(), recursos=recursos, **cambios)
