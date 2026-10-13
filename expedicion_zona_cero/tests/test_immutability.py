"""Pruebas de inmutabilidad: las operaciones devuelven estados nuevos."""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, replace

import pytest

from logic.actions import procesar_accion
from logic.expedition_service import (
    asignar_evento,
    avanzar_turno,
    crear_expedicion,
    ejecutar_turno,
    resolver_evento,
)
from logic.resources import (
    CONSUMO_BASE,
    FACTOR_CLIMA,
    FACTOR_DIFICULTAD,
    agregar_registro,
    aplicar_a_recursos,
    aplicar_delta,
    aplicar_efecto,
)
from models.events import CATALOGO_EVENTOS, Accion, Efecto
from models.expedition import EstadoMision, Recursos, Registro
from tests.helpers import evento_por_tipo


class TestObjetosCongelados:
    def test_recursos_no_se_puede_modificar(self):
        r = Recursos(80, 80, 90, 100)
        with pytest.raises(FrozenInstanceError):
            r.agua = 10

    def test_expedicion_no_se_puede_modificar(self):
        e = crear_expedicion()
        with pytest.raises(FrozenInstanceError):
            e.progreso = 100
        with pytest.raises(FrozenInstanceError):
            e.estado = EstadoMision.COMPLETADA

    def test_registro_y_efecto_no_se_pueden_modificar(self):
        with pytest.raises(FrozenInstanceError):
            Registro(1, "accion", "x").dia = 5
        with pytest.raises(FrozenInstanceError):
            Efecto(agua=1).agua = 5

    def test_eventos_y_opciones_no_se_pueden_modificar(self):
        evento = CATALOGO_EVENTOS[0]
        with pytest.raises(FrozenInstanceError):
            evento.titulo = "otro"
        with pytest.raises(FrozenInstanceError):
            evento.opciones[0].efecto = Efecto()

    def test_el_historial_es_una_tupla_sin_append(self):
        e = ejecutar_turno(crear_expedicion(), Accion("explorar"), 0.99).expedicion
        assert isinstance(e.historial, tuple)
        with pytest.raises(AttributeError):
            e.historial.append(Registro(1, "accion", "intruso"))

    def test_las_opciones_de_un_evento_son_una_tupla(self):
        assert all(isinstance(ev.opciones, tuple) for ev in CATALOGO_EVENTOS)
        assert isinstance(CATALOGO_EVENTOS, tuple)

    def test_los_parametros_de_balance_son_de_solo_lectura(self):
        for mapa in (CONSUMO_BASE, FACTOR_CLIMA, FACTOR_DIFICULTAD):
            with pytest.raises(TypeError):
                mapa["agua"] = 999


class TestEstadoAnteriorConservado:
    def test_aplicar_delta(self):
        original = Recursos(50, 50, 50, 50)
        nuevo = aplicar_delta(original, agua=-10, salud=20)
        assert original == Recursos(50, 50, 50, 50)
        assert nuevo == Recursos(40, 50, 50, 70)
        assert nuevo is not original

    def test_aplicar_a_recursos(self):
        original = Recursos(80, 60, 40, 20)
        nuevo = aplicar_a_recursos(lambda n, v: v // 2, original)
        assert original == Recursos(80, 60, 40, 20)
        assert nuevo == Recursos(40, 30, 20, 10)

    def test_aplicar_efecto(self):
        original = crear_expedicion()
        nuevo = aplicar_efecto(original, Efecto(agua=-20, progreso=10, integrantes=-1))
        assert (original.recursos.agua, original.progreso, original.integrantes) == (80, 0, 4)
        assert (nuevo.recursos.agua, nuevo.progreso, nuevo.integrantes) == (60, 10, 3)

    def test_agregar_registro_crea_una_tupla_nueva(self):
        original = crear_expedicion()
        nuevo = agregar_registro(original, Registro(1, "accion", "x"))
        assert original.historial == ()
        assert len(nuevo.historial) == 1
        assert nuevo.historial is not original.historial

    def test_procesar_accion(self):
        original = crear_expedicion()
        r = procesar_accion(original, Accion("explorar"))
        assert r.expedicion is not original
        # el estado anterior conserva TODOS sus valores
        assert original.recursos == Recursos(80, 80, 90, 100)
        assert original.progreso == 0
        assert original.historial == ()
        # el nuevo contiene los cambios
        assert r.expedicion.recursos == Recursos(76, 80, 78, 100)
        assert r.expedicion.progreso == 16
        assert len(r.expedicion.historial) == 1

    def test_avanzar_turno(self):
        original = crear_expedicion()
        nuevo = avanzar_turno(original)
        assert original.dia == 1 and original.recursos == Recursos(80, 80, 90, 100)
        assert nuevo.dia == 2 and nuevo.recursos == Recursos(74, 76, 86, 100)

    def test_resolver_evento(self):
        original = asignar_evento(crear_expedicion(), evento_por_tipo("tormenta"))
        nuevo = resolver_evento(original, "avanzar", 0.5).expedicion
        assert original.evento_actual is not None and original.clima == "despejado"
        assert nuevo.evento_actual is None and nuevo.clima == "tormenta"

    def test_dataclasses_replace_no_toca_el_original(self):
        original = crear_expedicion()
        copia = replace(original, progreso=50)
        assert original.progreso == 0 and copia.progreso == 50


class TestHistorialDeEstados:
    def test_cada_decision_deja_un_estado_verificable(self):
        """Gracias a la inmutabilidad se puede revisar cómo cambió cada decisión."""
        estados = [crear_expedicion()]
        for accion in (Accion("explorar"), Accion("recolectar", "agua"), Accion("descansar")):
            estados.append(ejecutar_turno(estados[-1], accion, 0.99).expedicion)

        assert [e.dia for e in estados] == [1, 2, 3, 4]
        assert [e.progreso for e in estados] == [0, 16, 16, 16]
        # el pasado no cambió aunque se siguió jugando
        assert estados[0].historial == ()
        assert len(estados[1].historial) == 2   # acción + cierre de jornada
        assert len(estados[3].historial) == 6
        # y cada historial es un prefijo del siguiente
        for anterior, siguiente in zip(estados, estados[1:]):
            assert siguiente.historial[: len(anterior.historial)] == anterior.historial


class TestColeccionesCompartidas:
    def test_jugar_no_altera_el_catalogo_de_eventos(self):
        antes = copy.deepcopy(CATALOGO_EVENTOS)
        e = crear_expedicion()
        for tirada in (0.0, 0.2, 0.4, 0.6, 0.7):
            r = ejecutar_turno(e, Accion("descansar"), tirada)
            e = r.expedicion
            if e.evento_actual is not None:
                e = resolver_evento(e, e.evento_actual.opciones[0].clave, 0.1).expedicion
        assert CATALOGO_EVENTOS == antes

    def test_las_expediciones_no_comparten_el_historial(self):
        a = crear_expedicion()
        b = crear_expedicion()
        a2 = ejecutar_turno(a, Accion("explorar"), 0.99).expedicion
        assert b.historial == ()
        assert a.historial == ()
        assert len(a2.historial) == 2

    def test_dos_ramas_a_partir_del_mismo_estado_son_independientes(self):
        base = crear_expedicion()
        rama_a = ejecutar_turno(base, Accion("explorar"), 0.99).expedicion
        rama_b = ejecutar_turno(base, Accion("descansar"), 0.99).expedicion
        assert rama_a.progreso == 16 and rama_b.progreso == 0
        assert base.progreso == 0 and base.historial == ()
        assert rama_a.historial != rama_b.historial

    def test_un_estado_no_cambia_tras_jugar_una_partida_completa(self):
        inicial = crear_expedicion()
        foto = copy.deepcopy(inicial)
        e = inicial
        for _ in range(20):
            if e.estado is not EstadoMision.EN_CURSO:
                break
            if e.evento_actual is not None:
                e = resolver_evento(e, e.evento_actual.opciones[0].clave, 0.5).expedicion
                continue
            e = ejecutar_turno(e, Accion("descansar"), 0.3).expedicion
        assert inicial == foto


class TestValidacionEnLosEstadosNuevos:
    def test_las_transformaciones_nunca_producen_recursos_invalidos(self):
        e = crear_expedicion()
        extremos = Efecto(agua=-500, alimentos=500, energia=-500, salud=500, progreso=500)
        n = aplicar_efecto(e, extremos)
        r = n.recursos
        assert all(0 <= v <= 100 for v in (r.agua, r.alimentos, r.energia, r.salud))
        assert 0 <= n.progreso <= 100

    def test_los_integrantes_nunca_son_negativos(self):
        e = replace(crear_expedicion(), integrantes=1)
        assert aplicar_efecto(e, Efecto(integrantes=-5)).integrantes == 0

    def test_no_se_puede_construir_un_estado_nuevo_invalido(self):
        e = crear_expedicion()
        with pytest.raises(ValueError):
            replace(e, progreso=150)
        with pytest.raises(ValueError):
            replace(e, recursos=Recursos(agua=101, alimentos=0, energia=0, salud=0))
