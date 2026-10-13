"""Pruebas de la capa lógica: recursos, acciones, eventos, turnos y reportes."""

from __future__ import annotations

from dataclasses import replace

import pytest

from logic.actions import (
    AccionInvalida,
    efecto_de_opcion,
    motivo_no_disponible,
    planificar_accion,
    procesar_accion,
)
from logic.expedition_service import (
    actualizar_estado,
    asignar_evento,
    avanzar_turno,
    consumo_proyectado,
    crear_expedicion,
    ejecutar_turno,
    elegir_evento,
    evaluar_estado,
    nivel_de_alerta,
    resolver_evento,
    tirar_dado,
)
from logic.reports import (
    calcular_puntuacion,
    eventos_criticos,
    exportar_reporte,
    filtrar_historial,
    formatear_reporte,
    historial_por_tipo,
    ordenar_historial,
    resumen_historial,
    total_consumido,
    total_recuperado,
)
from logic.resources import (
    CONSUMO_BASE,
    aplicar_a_recursos,
    aplicar_delta,
    calcular_consumo,
    consumo_total_funcional,
    consumo_total_imperativo,
    crear_modificador_consumo,
    faltantes,
    limitar,
    penalizacion_por_agotamiento,
    resumir_efecto,
)
from models.events import (
    CATALOGO_EVENTOS,
    EFECTO_ACCIDENTE,
    Accion,
    Efecto,
)
from models.expedition import (
    EstadoMision,
    Recursos,
    Registro,
)
from tests.helpers import evento_por_tipo, expedicion_con, expedicion_con_recursos


# ==========================================================================
# Cálculo de recursos, límites y valores inválidos
# ==========================================================================
class TestRecursosYLimites:
    @pytest.mark.parametrize(
        "entrada, esperado", [(-5, 0), (0, 0), (50, 50), (100, 100), (250, 100)]
    )
    def test_limitar(self, entrada, esperado):
        assert limitar(entrada) == esperado

    def test_aplicar_delta_suma_y_resta(self):
        r = aplicar_delta(Recursos(50, 50, 50, 50), agua=-10, energia=20)
        assert r == Recursos(agua=40, alimentos=50, energia=70, salud=50)

    def test_aplicar_delta_nunca_baja_de_cero(self):
        r = aplicar_delta(Recursos(5, 5, 5, 5), agua=-50, alimentos=-6, salud=-5)
        assert (r.agua, r.alimentos, r.energia, r.salud) == (0, 0, 5, 0)

    def test_aplicar_delta_nunca_supera_cien(self):
        r = aplicar_delta(Recursos(95, 95, 95, 95), agua=50, salud=6)
        assert (r.agua, r.salud) == (100, 100)

    @pytest.mark.parametrize("valor", [-1, 101, 1000])
    def test_recursos_rechaza_valores_fuera_de_rango(self, valor):
        with pytest.raises(ValueError):
            Recursos(agua=valor, alimentos=50, energia=50, salud=50)

    @pytest.mark.parametrize("valor", [5.5, "10", None, True])
    def test_recursos_rechaza_tipos_invalidos(self, valor):
        with pytest.raises(TypeError):
            Recursos(agua=valor, alimentos=50, energia=50, salud=50)

    def test_expedicion_rechaza_estados_imposibles(self):
        base = crear_expedicion()
        with pytest.raises(ValueError):
            replace(base, progreso=101)
        with pytest.raises(ValueError):
            replace(base, progreso=-1)
        with pytest.raises(ValueError):
            replace(base, integrantes=-1)
        with pytest.raises(ValueError):
            replace(base, dia=0)
        with pytest.raises(ValueError):
            replace(base, clima="nevada")
        with pytest.raises(ValueError):
            replace(base, dificultad="imposible")

    def test_expedicion_exige_historial_inmutable(self):
        with pytest.raises(TypeError):
            replace(crear_expedicion(), historial=[])

    def test_aplicar_a_recursos_es_orden_superior(self):
        r = Recursos(80, 60, 40, 20)
        mitad = aplicar_a_recursos(lambda nombre, valor: valor // 2, r)
        assert mitad == Recursos(40, 30, 20, 10)

    def test_aplicar_a_recursos_recibe_el_nombre_del_recurso(self):
        r = Recursos(80, 80, 80, 80)
        solo_agua = aplicar_a_recursos(
            lambda nombre, valor: valor - 10 if nombre == "agua" else valor, r
        )
        assert solo_agua == Recursos(70, 80, 80, 80)

    def test_aplicar_a_recursos_limita_el_resultado(self):
        r = Recursos(10, 10, 10, 10)
        assert aplicar_a_recursos(lambda n, v: v + 500, r) == Recursos(100, 100, 100, 100)
        assert aplicar_a_recursos(lambda n, v: v - 500, r) == Recursos(0, 0, 0, 0)


class TestConsumo:
    def test_consumo_base_con_factor_uno(self):
        assert calcular_consumo(crear_modificador_consumo(1.0)) == dict(CONSUMO_BASE)

    def test_consumo_con_tormenta(self):
        assert calcular_consumo(crear_modificador_consumo(1.5)) == {
            "agua": 9, "alimentos": 6, "energia": 6,
        }

    def test_consumo_dificil(self):
        assert calcular_consumo(crear_modificador_consumo(1.25)) == {
            "agua": 8, "alimentos": 5, "energia": 5,
        }

    def test_calcular_consumo_acepta_cualquier_funcion(self):
        assert calcular_consumo(lambda base: base * 2) == {
            "agua": 12, "alimentos": 8, "energia": 8,
        }

    def test_resumir_efecto(self):
        consumido, recuperado = resumir_efecto(Efecto(agua=-10, energia=15, salud=5, progreso=9))
        assert (consumido, recuperado) == (10, 20)


class TestPenalizacion:
    def test_sin_agotamiento(self):
        assert penalizacion_por_agotamiento(Recursos(1, 1, 0, 50)) == 0

    def test_sin_agua(self):
        assert penalizacion_por_agotamiento(Recursos(0, 10, 10, 50)) == 15

    def test_sin_agua_ni_comida(self):
        assert penalizacion_por_agotamiento(Recursos(0, 0, 10, 50)) == 30


# ==========================================================================
# map / filter / reduce y comparación funcional vs imperativa
# ==========================================================================
class TestFilterReduce:
    CONSUMOS = [
        {"agua": 6, "alimentos": 4, "energia": 4},
        {"agua": 9, "alimentos": 6, "energia": 6},
        {"agua": 8, "alimentos": 5, "energia": 5},
    ]

    def test_imperativo_y_funcional_dan_el_mismo_total(self):
        assert consumo_total_imperativo(self.CONSUMOS) == 53
        assert consumo_total_funcional(self.CONSUMOS) == 53

    def test_ambos_enfoques_coinciden_con_lista_vacia(self):
        assert consumo_total_imperativo([]) == 0
        assert consumo_total_funcional([]) == 0

    def test_ambos_enfoques_coinciden_con_datos_variados(self):
        datos = [{"agua": i, "alimentos": 2 * i, "energia": 0} for i in range(20)]
        assert consumo_total_imperativo(datos) == consumo_total_funcional(datos)

    def test_los_enfoques_no_modifican_la_entrada(self):
        copia = [dict(c) for c in self.CONSUMOS]
        consumo_total_imperativo(self.CONSUMOS)
        consumo_total_funcional(self.CONSUMOS)
        assert self.CONSUMOS == copia

    def test_faltantes_devuelve_los_recursos_que_no_alcanzan(self):
        r = Recursos(agua=3, alimentos=80, energia=5, salud=100)
        assert faltantes(r, {"energia": 12, "agua": 4, "alimentos": 10}) == ("energia", "agua")

    def test_faltantes_vacio_si_todo_alcanza(self):
        assert faltantes(Recursos(50, 50, 50, 50), {"agua": 50, "energia": 10}) == ()

    def test_total_consumido_y_recuperado_con_reduce(self):
        historial = (
            Registro(1, "accion", "a", consumido=16, recuperado=0),
            Registro(1, "turno", "b", consumido=14),
            Registro(2, "accion", "c", consumido=4, recuperado=35),
        )
        assert total_consumido(historial) == 34
        assert total_recuperado(historial) == 35
        assert total_consumido(()) == 0


class TestFiltrosDeHistorial:
    HISTORIAL = (
        Registro(3, "accion", "explorar"),
        Registro(1, "evento", "tormenta", critico=False),
        Registro(2, "evento", "averia", critico=True),
        Registro(2, "decision", "reparar", critico=True),
        Registro(1, "turno", "fin de dia"),
    )

    def test_filtrar_historial_recibe_un_criterio(self):
        resultado = filtrar_historial(lambda r: r.dia == 2, self.HISTORIAL)
        assert [r.descripcion for r in resultado] == ["averia", "reparar"]
        assert isinstance(resultado, tuple)

    def test_eventos_criticos(self):
        assert [r.descripcion for r in eventos_criticos(self.HISTORIAL)] == ["averia", "reparar"]

    def test_historial_por_tipo(self):
        assert len(historial_por_tipo("evento", self.HISTORIAL)) == 2
        assert historial_por_tipo("inexistente", self.HISTORIAL) == ()

    def test_ordenar_historial(self):
        asc = ordenar_historial(lambda r: r.dia, self.HISTORIAL)
        desc = ordenar_historial(lambda r: r.dia, self.HISTORIAL, descendente=True)
        assert [r.dia for r in asc] == [1, 1, 2, 2, 3]
        assert [r.dia for r in desc] == [3, 2, 2, 1, 1]

    def test_ordenar_no_altera_el_original(self):
        original = tuple(self.HISTORIAL)
        ordenar_historial(lambda r: r.dia, self.HISTORIAL)
        assert self.HISTORIAL == original

    def test_resumen_historial(self):
        resumen = resumen_historial(self.HISTORIAL)
        assert resumen["acciones"] == 1
        assert resumen["eventos"] == 2
        assert resumen["decisiones"] == 1
        assert resumen["turnos"] == 1
        assert resumen["criticos"] == 2


# ==========================================================================
# match/case: procesamiento de acciones
# ==========================================================================
class TestProcesarAcciones:
    def test_explorar(self):
        e = crear_expedicion()
        r = procesar_accion(e, Accion("explorar"))
        assert r.valido
        n = r.expedicion
        assert n.progreso == 16  # 4 integrantes x 4
        assert n.recursos.energia == 78
        assert n.recursos.agua == 76
        assert n.recursos.alimentos == 80
        assert n.historial[-1].tipo == "accion"
        assert n.historial[-1].consumido == 16
        assert n.historial[-1].recuperado == 0

    def test_explorar_depende_de_los_integrantes(self):
        r = procesar_accion(expedicion_con(integrantes=2), Accion("explorar"))
        assert r.expedicion.progreso == 8

    def test_explorar_sin_energia_se_rechaza(self):
        e = expedicion_con_recursos(energia=11)
        r = procesar_accion(e, Accion("explorar"))
        assert not r.valido
        assert r.nivel == "warning"
        assert "energia" in r.mensaje
        assert r.expedicion is e

    def test_explorar_con_energia_justa_se_permite(self):
        e = expedicion_con_recursos(energia=12)
        assert procesar_accion(e, Accion("explorar")).valido

    def test_descansar(self):
        e = expedicion_con_recursos(energia=40, salud=90, alimentos=50)
        n = procesar_accion(e, Accion("descansar")).expedicion
        assert (n.recursos.energia, n.recursos.salud, n.recursos.alimentos) == (70, 95, 46)

    def test_descansar_siempre_esta_disponible(self):
        """Evita bloqueos: aun sin comida ni energía existe una acción válida."""
        e = expedicion_con_recursos(agua=0, alimentos=0, energia=0, salud=50)
        r = procesar_accion(e, Accion("descansar"))
        assert r.valido
        assert r.expedicion.recursos.energia == 30
        assert r.expedicion.recursos.alimentos == 0  # nunca negativo

    def test_consumir_agua_recupera_salud(self):
        e = expedicion_con_recursos(agua=70, salud=50)
        n = procesar_accion(e, Accion("consumir_recurso", "agua")).expedicion
        assert (n.recursos.agua, n.recursos.salud) == (60, 56)

    def test_consumir_alimentos_recupera_energia(self):
        e = expedicion_con_recursos(alimentos=50, energia=20)
        n = procesar_accion(e, Accion("consumir_recurso", "alimentos")).expedicion
        assert (n.recursos.alimentos, n.recursos.energia) == (40, 35)

    @pytest.mark.parametrize("parametro", ["energia", "oro", None, ""])
    def test_consumir_recurso_invalido(self, parametro):
        e = crear_expedicion()
        r = procesar_accion(e, Accion("consumir_recurso", parametro))
        assert not r.valido
        assert r.nivel == "error"
        assert r.expedicion is e

    def test_consumir_agua_sin_suficiente_se_rechaza(self):
        e = expedicion_con_recursos(agua=9)
        r = procesar_accion(e, Accion("consumir_recurso", "agua"))
        assert not r.valido and r.expedicion is e

    @pytest.mark.parametrize("recurso", ["agua", "alimentos"])
    def test_recolectar(self, recurso):
        e = expedicion_con_recursos(agua=10, alimentos=10, energia=50)
        n = procesar_accion(e, Accion("recolectar", recurso)).expedicion
        assert getattr(n.recursos, recurso) == 40
        assert n.recursos.energia == 42

    def test_recolectar_se_limita_a_cien(self):
        e = expedicion_con_recursos(agua=90, energia=50)
        n = procesar_accion(e, Accion("recolectar", "agua")).expedicion
        assert n.recursos.agua == 100

    @pytest.mark.parametrize("parametro", ["oro", "energia", None])
    def test_recolectar_invalido(self, parametro):
        e = crear_expedicion()
        r = procesar_accion(e, Accion("recolectar", parametro))
        assert not r.valido and r.expedicion is e

    def test_recolectar_sin_energia_se_rechaza(self):
        e = expedicion_con_recursos(energia=7)
        assert not procesar_accion(e, Accion("recolectar", "agua")).valido

    def test_atender_emergencia(self):
        e = expedicion_con_recursos(agua=50, alimentos=50, energia=50, salud=40)
        n = procesar_accion(e, Accion("atender_emergencia")).expedicion
        assert (n.recursos.agua, n.recursos.alimentos) == (40, 45)
        assert (n.recursos.energia, n.recursos.salud) == (40, 65)

    def test_atender_emergencia_sin_recursos(self):
        e = expedicion_con_recursos(agua=5, alimentos=50, energia=50)
        r = procesar_accion(e, Accion("atender_emergencia"))
        assert not r.valido
        assert "agua" in r.mensaje

    @pytest.mark.parametrize("tipo", ["volar", "", "EXPLORAR", "Explorar"])
    def test_accion_desconocida(self, tipo):
        e = crear_expedicion()
        r = procesar_accion(e, Accion(tipo))
        assert not r.valido
        assert r.nivel == "error"
        assert r.expedicion is e

    def test_no_se_actua_con_la_mision_terminada(self):
        for estado in (EstadoMision.COMPLETADA, EstadoMision.FALLIDA):
            e = expedicion_con(estado=estado)
            r = procesar_accion(e, Accion("explorar"))
            assert not r.valido and r.expedicion is e

    def test_planificar_accion_lanza_para_acciones_desconocidas(self):
        with pytest.raises(AccionInvalida):
            planificar_accion(Accion("teletransportar"), 4)

    def test_accion_rechazada_no_agrega_historial(self):
        e = crear_expedicion()
        r = procesar_accion(e, Accion("volar"))
        assert r.expedicion.historial == ()


# ==========================================================================
# match/case: eventos
# ==========================================================================
class TestEventos:
    def test_catalogo_tiene_los_eventos_pedidos(self):
        tipos = {e.tipo for e in CATALOGO_EVENTOS}
        assert tipos == {
            "tormenta", "provisiones", "averia", "zona_peligrosa", "descanso", "emergencia",
        }

    def test_todo_evento_tiene_opciones_con_consecuencias(self):
        for evento in CATALOGO_EVENTOS:
            assert len(evento.opciones) >= 2
            for opcion in evento.opciones:
                assert opcion.efecto != Efecto(), f"{evento.tipo}/{opcion.clave} no hace nada"

    def test_elegir_evento_extremos(self):
        assert elegir_evento(CATALOGO_EVENTOS, 0.0) is CATALOGO_EVENTOS[0]
        assert elegir_evento(CATALOGO_EVENTOS, 0.7499) is CATALOGO_EVENTOS[-1]

    def test_elegir_evento_sin_evento_en_dias_tranquilos(self):
        assert elegir_evento(CATALOGO_EVENTOS, 0.75) is None
        assert elegir_evento(CATALOGO_EVENTOS, 0.999) is None

    def test_elegir_evento_alcanza_todos_los_eventos(self):
        n = len(CATALOGO_EVENTOS)
        for i in range(n):
            tirada = (i + 0.5) / n * 0.75
            assert elegir_evento(CATALOGO_EVENTOS, tirada) is CATALOGO_EVENTOS[i]

    @pytest.mark.parametrize("tirada", [-0.1, 1.0, 2.0])
    def test_elegir_evento_rechaza_tiradas_invalidas(self, tirada):
        with pytest.raises(ValueError):
            elegir_evento(CATALOGO_EVENTOS, tirada)

    def test_elegir_evento_con_catalogo_vacio(self):
        assert elegir_evento((), 0.1) is None

    def test_tirar_dado_esta_en_rango(self):
        for _ in range(100):
            assert 0.0 <= tirar_dado() < 1.0

    def test_asignar_evento(self):
        evento = evento_por_tipo("averia")
        n = asignar_evento(crear_expedicion(), evento)
        assert n.evento_actual is evento
        assert n.historial[-1].tipo == "evento"
        assert n.historial[-1].critico is True

    # ---- efecto_de_opcion (match/case sobre (tipo, clave)) ----
    def test_tormenta_avanzar_cambia_el_clima(self):
        ev = evento_por_tipo("tormenta")
        efecto = efecto_de_opcion(ev, ev.opciones[1], 0.5)
        assert efecto.clima == "tormenta"
        assert efecto.progreso == 6

    def test_tormenta_refugiarse_no_cambia_el_clima(self):
        ev = evento_por_tipo("tormenta")
        efecto = efecto_de_opcion(ev, ev.opciones[0], 0.5)
        assert efecto.clima is None
        assert efecto is ev.opciones[0].efecto

    def test_ruta_corta_con_accidente(self):
        ev = evento_por_tipo("zona_peligrosa")
        corta = next(o for o in ev.opciones if o.clave == "ruta_corta")
        assert efecto_de_opcion(ev, corta, 0.0) is EFECTO_ACCIDENTE
        assert efecto_de_opcion(ev, corta, 0.399) is EFECTO_ACCIDENTE

    def test_ruta_corta_sin_accidente(self):
        ev = evento_por_tipo("zona_peligrosa")
        corta = next(o for o in ev.opciones if o.clave == "ruta_corta")
        assert efecto_de_opcion(ev, corta, 0.4).progreso == 18
        assert efecto_de_opcion(ev, corta, 0.99).progreso == 18

    def test_ruta_larga_nunca_tiene_accidente(self):
        ev = evento_por_tipo("zona_peligrosa")
        larga = next(o for o in ev.opciones if o.clave == "ruta_larga")
        assert efecto_de_opcion(ev, larga, 0.0) is larga.efecto

    def test_ignorar_emergencia_pierde_un_integrante(self):
        ev = evento_por_tipo("emergencia")
        ignorar = next(o for o in ev.opciones if o.clave == "ignorar")
        assert efecto_de_opcion(ev, ignorar, 0.5).integrantes == -1

    def test_evento_sin_regla_especial_usa_el_efecto_base(self):
        ev = evento_por_tipo("provisiones")
        for opcion in ev.opciones:
            assert efecto_de_opcion(ev, opcion, 0.5) is opcion.efecto

    # ---- resolver_evento ----
    def test_resolver_sin_evento_pendiente(self):
        e = crear_expedicion()
        r = resolver_evento(e, "avanzar", 0.5)
        assert not r.valido and r.expedicion is e

    def test_resolver_con_opcion_desconocida(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("tormenta"))
        r = resolver_evento(e, "bailar", 0.5)
        assert not r.valido and r.expedicion is e
        assert e.evento_actual is not None

    def test_resolver_tormenta_avanzar(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("tormenta"))
        n = resolver_evento(e, "avanzar", 0.5).expedicion
        assert n.evento_actual is None
        assert n.clima == "tormenta"
        assert n.progreso == 6
        assert n.recursos.energia == 82
        assert n.historial[-1].tipo == "decision"

    def test_resolver_provisiones_aumenta_recursos(self):
        e = expedicion_con_recursos(agua=40, alimentos=40, energia=60)
        e = asignar_evento(e, evento_por_tipo("provisiones"))
        n = resolver_evento(e, "tomar_todo", 0.5).expedicion
        assert (n.recursos.agua, n.recursos.alimentos, n.recursos.energia) == (60, 60, 52)

    def test_resolver_emergencia_ignorada(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("emergencia"))
        r = resolver_evento(e, "ignorar", 0.5)
        assert r.expedicion.integrantes == 3
        assert r.expedicion.recursos.salud == 85
        assert "integrante" in r.mensaje

    def test_resolver_emergencia_atendida(self):
        e = expedicion_con_recursos(salud=50)
        e = asignar_evento(e, evento_por_tipo("emergencia"))
        n = resolver_evento(e, "atender", 0.5).expedicion
        assert n.integrantes == 4
        assert n.recursos.salud == 65
        assert (n.recursos.agua, n.recursos.alimentos) == (70, 74)

    def test_perder_al_ultimo_integrante_termina_la_mision(self):
        e = expedicion_con(integrantes=1)
        e = asignar_evento(e, evento_por_tipo("emergencia"))
        n = resolver_evento(e, "ignorar", 0.5).expedicion
        assert n.integrantes == 0
        assert n.estado is EstadoMision.FALLIDA

    def test_zona_peligrosa_ruta_corta_accidente(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("zona_peligrosa"))
        r = resolver_evento(e, "ruta_corta", 0.0)
        assert r.expedicion.recursos.salud == 75
        assert r.expedicion.progreso == 0
        assert "accidente" in r.mensaje

    def test_zona_peligrosa_ruta_corta_exitosa(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("zona_peligrosa"))
        r = resolver_evento(e, "ruta_corta", 0.9)
        assert r.expedicion.progreso == 18
        assert "accidente" not in r.mensaje

    def test_un_evento_puede_cerrar_la_mision(self):
        e = expedicion_con_recursos(salud=10)
        e = asignar_evento(e, evento_por_tipo("zona_peligrosa"))
        n = resolver_evento(e, "ruta_corta", 0.0).expedicion
        assert n.recursos.salud == 0
        assert n.estado is EstadoMision.FALLIDA
        assert n.historial[-1].tipo == "sistema"

    def test_no_se_resuelven_eventos_con_la_mision_terminada(self):
        e = expedicion_con(estado=EstadoMision.FALLIDA, evento_actual=evento_por_tipo("averia"))
        assert not resolver_evento(e, "reparar", 0.5).valido


# ==========================================================================
# Condiciones de éxito y fracaso
# ==========================================================================
class TestEstadoDeLaMision:
    def test_en_curso_al_inicio(self):
        assert evaluar_estado(crear_expedicion()) is EstadoMision.EN_CURSO

    def test_completada_al_llegar_a_la_meta(self):
        assert evaluar_estado(expedicion_con(progreso=100)) is EstadoMision.COMPLETADA

    def test_fallida_sin_salud(self):
        assert evaluar_estado(expedicion_con_recursos(salud=0)) is EstadoMision.FALLIDA

    def test_fallida_sin_integrantes(self):
        assert evaluar_estado(expedicion_con(integrantes=0)) is EstadoMision.FALLIDA

    def test_fallida_al_agotar_los_dias(self):
        assert evaluar_estado(expedicion_con(dia=13, progreso=60)) is EstadoMision.FALLIDA

    def test_el_ultimo_dia_aun_cuenta(self):
        assert evaluar_estado(expedicion_con(dia=12, progreso=60)) is EstadoMision.EN_CURSO

    def test_la_meta_no_salva_a_un_equipo_sin_salud(self):
        e = expedicion_con_recursos(salud=0, progreso=100)
        assert evaluar_estado(e) is EstadoMision.FALLIDA

    def test_la_meta_no_cuenta_sin_integrantes(self):
        assert evaluar_estado(expedicion_con(progreso=100, integrantes=0)) is EstadoMision.FALLIDA

    def test_llegar_a_la_meta_en_el_ultimo_dia_cuenta(self):
        assert evaluar_estado(expedicion_con(dia=13, progreso=100)) is EstadoMision.COMPLETADA

    def test_actualizar_estado_registra_el_cambio_una_sola_vez(self):
        e = expedicion_con(progreso=100)
        n = actualizar_estado(e)
        assert n.estado is EstadoMision.COMPLETADA
        assert n.historial[-1].tipo == "sistema"
        assert actualizar_estado(n) is n  # sin cambios: mismo objeto

    @pytest.mark.parametrize(
        "cambios, nivel",
        [
            ({}, "info"),
            ({"recursos": Recursos(80, 80, 20, 100)}, "warning"),
            ({"recursos": Recursos(80, 80, 90, 15)}, "warning"),
            ({"estado": EstadoMision.COMPLETADA}, "success"),
            ({"estado": EstadoMision.FALLIDA}, "error"),
        ],
    )
    def test_nivel_de_alerta(self, cambios, nivel):
        assert nivel_de_alerta(expedicion_con(**cambios)) == nivel


# ==========================================================================
# Turnos
# ==========================================================================
class TestAvanzarTurno:
    def test_consumo_normal(self):
        n = avanzar_turno(crear_expedicion())
        assert (n.recursos.agua, n.recursos.alimentos, n.recursos.energia) == (74, 76, 86)
        assert n.recursos.salud == 100
        assert n.dia == 2
        assert n.historial[-1].tipo == "turno"
        assert n.historial[-1].consumido == 14

    def test_consumo_con_tormenta_y_reinicio_del_clima(self):
        n = avanzar_turno(expedicion_con(clima="tormenta"))
        assert (n.recursos.agua, n.recursos.alimentos, n.recursos.energia) == (71, 74, 84)
        assert n.clima == "despejado"

    def test_consumo_en_dificultad_alta(self):
        n = avanzar_turno(expedicion_con(dificultad="dificil"))
        assert (n.recursos.agua, n.recursos.alimentos, n.recursos.energia) == (72, 75, 85)

    def test_tormenta_y_dificultad_se_multiplican(self):
        n = avanzar_turno(expedicion_con(clima="tormenta", dificultad="dificil"))
        # factor 1.5 * 1.25 = 1.875 -> agua 11, alimentos 8 (7.5), energia 8 (7.5)
        assert (n.recursos.agua, n.recursos.alimentos, n.recursos.energia) == (69, 72, 82)

    def test_sin_agua_penaliza_la_salud(self):
        n = avanzar_turno(expedicion_con_recursos(agua=3))
        assert n.recursos.agua == 0
        assert n.recursos.salud == 85
        assert n.historial[-1].critico is True

    def test_sin_agua_ni_comida_penaliza_el_doble(self):
        n = avanzar_turno(expedicion_con_recursos(agua=2, alimentos=1))
        assert n.recursos.salud == 70

    def test_la_penalizacion_puede_matar_a_la_expedicion(self):
        n = avanzar_turno(expedicion_con_recursos(agua=0, salud=10))
        assert n.recursos.salud == 0
        assert n.estado is EstadoMision.FALLIDA

    def test_agotar_los_dias_sin_llegar_a_la_meta_es_fracaso(self):
        n = avanzar_turno(expedicion_con(dia=12, progreso=50))
        assert n.dia == 13
        assert n.estado is EstadoMision.FALLIDA
        assert n.historial[-1].tipo == "sistema"


class TestEjecutarTurno:
    def test_turno_normal(self):
        r = ejecutar_turno(crear_expedicion(), Accion("explorar"), 0.99)
        assert r.valido
        n = r.expedicion
        assert n.dia == 2
        assert n.progreso == 16
        assert n.evento_actual is None
        # explorar (-12 energía, -4 agua) + consumo (-4 energía, -6 agua)
        assert (n.recursos.energia, n.recursos.agua) == (74, 70)

    def test_accion_invalida_no_consume_el_turno(self):
        e = crear_expedicion()
        r = ejecutar_turno(e, Accion("volar"), 0.0)
        assert not r.valido
        assert r.expedicion is e
        assert e.dia == 1

    def test_accion_sin_recursos_no_consume_el_turno(self):
        e = expedicion_con_recursos(energia=5)
        r = ejecutar_turno(e, Accion("explorar"), 0.0)
        assert not r.valido and r.expedicion.dia == 1

    def test_el_turno_puede_traer_un_evento(self):
        r = ejecutar_turno(crear_expedicion(), Accion("descansar"), 0.0)
        assert r.expedicion.evento_actual is CATALOGO_EVENTOS[0]
        assert "Evento" in r.mensaje

    def test_un_evento_pendiente_bloquea_las_acciones(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("averia"))
        r = ejecutar_turno(e, Accion("explorar"), 0.99)
        assert not r.valido
        assert r.nivel == "warning"
        assert r.expedicion is e

    def test_al_resolver_el_evento_se_puede_seguir(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("descanso"))
        e = resolver_evento(e, "seguir", 0.5).expedicion
        assert ejecutar_turno(e, Accion("explorar"), 0.99).valido

    def test_completar_la_mision_no_consume_la_jornada(self):
        e = expedicion_con(progreso=90)
        r = ejecutar_turno(e, Accion("explorar"), 0.0)
        n = r.expedicion
        assert n.progreso == 100
        assert n.estado is EstadoMision.COMPLETADA
        assert n.dia == 1  # no se cerró la jornada
        assert n.evento_actual is None  # y no se sortea un evento
        assert r.nivel == "success"

    def test_completar_la_mision_evita_penalizaciones_del_turno(self):
        e = expedicion_con_recursos(agua=4, salud=10, progreso=90)
        n = ejecutar_turno(e, Accion("explorar"), 0.99).expedicion
        assert n.estado is EstadoMision.COMPLETADA
        assert n.recursos.salud == 10

    def test_despues_de_terminar_no_hay_mas_acciones(self):
        e = ejecutar_turno(expedicion_con(progreso=90), Accion("explorar"), 0.9).expedicion
        assert not ejecutar_turno(e, Accion("descansar"), 0.9).valido

    def test_fracaso_por_dias_se_reporta_en_el_mensaje(self):
        e = expedicion_con(dia=12, progreso=10)
        r = ejecutar_turno(e, Accion("descansar"), 0.99)
        assert r.expedicion.estado is EstadoMision.FALLIDA
        assert "fallida" in r.mensaje
        assert r.nivel == "error"
        assert r.expedicion.evento_actual is None

    def test_partida_completa_determinista(self):
        """7 exploraciones seguidas con energía repuesta llegan a la meta."""
        e = expedicion_con_recursos(agua=100, alimentos=100, energia=100)
        turnos = 0
        while e.estado is EstadoMision.EN_CURSO and turnos < 50:
            accion = Accion("descansar") if e.recursos.energia < 30 else Accion("explorar")
            r = ejecutar_turno(e, accion, 0.99)  # 0.99: nunca hay eventos
            assert r.valido
            e = r.expedicion
            turnos += 1
        assert e.estado is EstadoMision.COMPLETADA
        assert e.progreso == 100
        assert e.dia <= e.dia_limite


# ==========================================================================
# Reinicio
# ==========================================================================
class TestReinicio:
    def test_expedicion_nueva_parte_de_un_estado_valido(self):
        e = crear_expedicion()
        assert e.dia == 1 and e.progreso == 0 and e.integrantes == 4
        assert e.estado is EstadoMision.EN_CURSO
        assert e.historial == () and e.evento_actual is None
        assert e.recursos == Recursos(agua=80, alimentos=80, energia=90, salud=100)

    def test_reiniciar_no_conserva_datos_de_la_partida_anterior(self):
        vieja = ejecutar_turno(crear_expedicion(), Accion("explorar"), 0.0).expedicion
        assert vieja.historial  # la partida anterior tiene datos
        nueva = crear_expedicion()
        assert nueva.historial == ()
        assert nueva.progreso == 0
        assert nueva is not vieja

    def test_dos_expediciones_no_comparten_objetos(self):
        a, b = crear_expedicion(), crear_expedicion()
        assert a == b and a is not b
        assert a.recursos is not b.recursos

    def test_la_dificultad_se_conserva_al_crear(self):
        assert crear_expedicion(dificultad="dificil").dificultad == "dificil"

    def test_el_nombre_se_conserva_al_crear(self):
        assert crear_expedicion(nombre="Delta").nombre == "Delta"


# ==========================================================================
# Puntuación y reportes
# ==========================================================================
class TestReportes:
    def test_puntuacion_inicial(self):
        # 0*10 + 4*50 + (80+80+90+100)*2
        assert calcular_puntuacion(crear_expedicion()) == 900

    def test_puntuacion_de_mision_completada_incluye_bono_de_dias(self):
        e = expedicion_con(progreso=100, estado=EstadoMision.COMPLETADA, dia=5)
        # 1000 + 200 + 700 + (12-5)*25
        assert calcular_puntuacion(e) == 2075

    def test_puntuacion_de_mision_fallida_se_reduce_a_la_mitad(self):
        assert calcular_puntuacion(expedicion_con(estado=EstadoMision.FALLIDA)) == 450

    def test_formatear_reporte_contiene_los_datos_clave(self):
        e = ejecutar_turno(crear_expedicion(), Accion("explorar"), 0.99).expedicion
        texto = formatear_reporte(e)
        assert "Expedición Alfa" in texto
        assert "En curso" in texto
        assert "Progreso: 16/100" in texto
        assert "Exploraron la zona" in texto

    def test_formatear_reporte_no_modifica_la_expedicion(self):
        e = ejecutar_turno(crear_expedicion(), Accion("explorar"), 0.99).expedicion
        copia = replace(e)
        formatear_reporte(e)
        assert e == copia

    def test_el_reporte_nunca_muestra_un_dia_superior_al_limite(self):
        e = expedicion_con(dia=13, estado=EstadoMision.FALLIDA)
        assert "Día alcanzado: 12 de 12" in formatear_reporte(e)

    def test_exportar_reporte_escribe_el_archivo(self, tmp_path):
        e = ejecutar_turno(crear_expedicion(), Accion("explorar"), 0.99).expedicion
        destino = tmp_path / "reporte.txt"
        resultado = exportar_reporte(e, destino)
        assert resultado == destino
        assert destino.read_text(encoding="utf-8") == formatear_reporte(e)

    def test_exportar_reporte_acepta_rutas_como_texto(self, tmp_path):
        ruta = str(tmp_path / "otro.txt")
        exportar_reporte(crear_expedicion(), ruta)
        assert "Expedición Alfa" in open(ruta, encoding="utf-8").read()


# ==========================================================================
# Apoyo a la interfaz: disponibilidad de acciones y consumo previsto
# ==========================================================================
class TestApoyoParaLaInterfaz:
    def test_accion_disponible_devuelve_none(self):
        assert motivo_no_disponible(crear_expedicion(), Accion("explorar")) is None

    def test_descansar_esta_disponible_aun_sin_recursos(self):
        e = expedicion_con_recursos(agua=0, alimentos=0, energia=0, salud=50)
        assert motivo_no_disponible(e, Accion("descansar")) is None

    def test_explica_los_recursos_que_faltan(self):
        e = expedicion_con_recursos(energia=5)
        motivo = motivo_no_disponible(e, Accion("explorar"))
        assert motivo is not None and "energia" in motivo

    def test_acciones_invalidas_tienen_motivo(self):
        assert motivo_no_disponible(crear_expedicion(), Accion("volar")) is not None
        assert motivo_no_disponible(crear_expedicion(), Accion("recolectar", "oro")) is not None

    def test_con_evento_pendiente_ninguna_accion_esta_disponible(self):
        e = asignar_evento(crear_expedicion(), evento_por_tipo("averia"))
        assert "evento" in motivo_no_disponible(e, Accion("descansar"))

    def test_con_la_mision_terminada_ninguna_accion_esta_disponible(self):
        e = expedicion_con(estado=EstadoMision.FALLIDA)
        assert "terminó" in motivo_no_disponible(e, Accion("descansar"))

    @pytest.mark.parametrize(
        "accion",
        [Accion("explorar"), Accion("descansar"), Accion("recolectar", "agua"),
         Accion("atender_emergencia"), Accion("consumir_recurso", "agua"), Accion("volar")],
    )
    def test_motivo_coincide_con_procesar_accion(self, accion):
        """La interfaz y la lógica nunca deben contradecirse."""
        for e in (crear_expedicion(), expedicion_con_recursos(agua=3, energia=5)):
            motivo = motivo_no_disponible(e, accion)
            assert (motivo is None) == procesar_accion(e, accion).valido

    def test_consumo_proyectado_normal(self):
        assert consumo_proyectado(crear_expedicion()) == {"agua": 6, "alimentos": 4, "energia": 4}

    def test_consumo_proyectado_con_tormenta(self):
        assert consumo_proyectado(expedicion_con(clima="tormenta")) == {
            "agua": 9, "alimentos": 6, "energia": 6,
        }

    def test_consumo_proyectado_coincide_con_lo_que_consume_el_turno(self):
        e = expedicion_con(clima="tormenta", dificultad="dificil")
        previsto = consumo_proyectado(e)
        n = avanzar_turno(e)
        assert e.recursos.agua - n.recursos.agua == previsto["agua"]
        assert e.recursos.alimentos - n.recursos.alimentos == previsto["alimentos"]
        assert e.recursos.energia - n.recursos.energia == previsto["energia"]
