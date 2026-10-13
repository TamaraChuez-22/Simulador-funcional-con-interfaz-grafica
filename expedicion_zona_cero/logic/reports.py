#Capa lógica: historial, resúmenes y reportes.

from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Callable, Sequence

from models.expedition import EstadoMision, Expedicion, Registro


# Consultas sobre el historial

def filtrar_historial(
    criterio: Callable[[Registro], bool], historial: Sequence[Registro]
 ) -> tuple[Registro, ...]:

    return tuple(filter(criterio, historial))


def ordenar_historial(
    clave: Callable[[Registro], object],
    historial: Sequence[Registro],
    descendente: bool = False,
) -> tuple[Registro, ...]:
    return tuple(sorted(historial, key=clave, reverse=descendente))


def eventos_criticos(historial: Sequence[Registro]) -> tuple[Registro, ...]:
    return filtrar_historial(lambda registro: registro.critico, historial)


def historial_por_tipo(tipo: str, historial: Sequence[Registro]) -> tuple[Registro, ...]:
    return filtrar_historial(lambda registro: registro.tipo == tipo, historial)


def total_consumido(historial: Sequence[Registro]) -> int:
    
    return reduce(lambda acumulado, registro: acumulado + registro.consumido, historial, 0)


def total_recuperado(historial: Sequence[Registro]) -> int:
    """Puntos de recursos recuperados en toda la expedición. (PURA)"""
    return reduce(lambda acumulado, registro: acumulado + registro.recuperado, historial, 0)


def resumen_historial(historial: Sequence[Registro]) -> dict[str, int]:
    """Cifras clave del historial para el reporte. (PURA)"""
    return {
        "acciones": len(historial_por_tipo("accion", historial)),
        "eventos": len(historial_por_tipo("evento", historial)),
        "decisiones": len(historial_por_tipo("decision", historial)),
        "turnos": len(historial_por_tipo("turno", historial)),
        "criticos": len(eventos_criticos(historial)),
        "consumido": total_consumido(historial),
        "recuperado": total_recuperado(historial),
    }



# Puntuación y reporte

def calcular_puntuacion(expedicion: Expedicion) -> int:
   
    r = expedicion.recursos
    puntos = (
        expedicion.progreso * 10
        + expedicion.integrantes * 50
        + (r.agua + r.alimentos + r.energia + r.salud) * 2
    )
    if expedicion.estado is EstadoMision.COMPLETADA:
        puntos += max(0, expedicion.dia_limite - expedicion.dia) * 25
    elif expedicion.estado is EstadoMision.FALLIDA:
        puntos //= 2
    return puntos


def formatear_reporte(expedicion: Expedicion) -> str:
    r = expedicion.recursos
    resumen = resumen_historial(expedicion.historial)
    lineas = [
        f"REPORTE DE EXPEDICIÓN — {expedicion.nombre}",
        "=" * 56,
        f"Resultado: {expedicion.estado.value}",
        f"Día alcanzado: {min(expedicion.dia, expedicion.dia_limite)} de {expedicion.dia_limite}",
        f"Progreso: {expedicion.progreso}/100",
        f"Integrantes: {expedicion.integrantes}",
        f"Dificultad: {expedicion.dificultad}",
        f"Puntuación: {calcular_puntuacion(expedicion)}",
        "",
        "Recursos finales",
        f"  Agua: {r.agua}   Alimentos: {r.alimentos}   Energía: {r.energia}   Salud: {r.salud}",
        "",
        "Resumen",
        f"  Acciones: {resumen['acciones']}   Eventos: {resumen['eventos']}   "
        f"Decisiones: {resumen['decisiones']}   Turnos: {resumen['turnos']}",
        f"  Recursos consumidos: {resumen['consumido']}   "
        f"Recuperados: {resumen['recuperado']}   Críticos: {resumen['criticos']}",
        "",
        "Historial",
    ]
    ordenado = ordenar_historial(lambda registro: registro.dia, expedicion.historial)
    lineas.extend(
        f"  [Día {registro.dia:>2}] {registro.tipo.upper():<9} "
        f"{'(!) ' if registro.critico else ''}{registro.descripcion}"
        for registro in ordenado
    )
    return "\n".join(lineas) + "\n"


def exportar_reporte(expedicion: Expedicion, ruta: str | Path) -> Path:
    destino = Path(ruta)
    destino.write_text(formatear_reporte(expedicion), encoding="utf-8")
    return destino
