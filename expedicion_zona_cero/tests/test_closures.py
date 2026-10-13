#Pruebas del closure ``crear_modificador_consumo``.

from __future__ import annotations

import pytest

from logic.expedition_service import avanzar_turno
from logic.resources import CONSUMO_BASE, calcular_consumo, crear_modificador_consumo
from tests.helpers import expedicion_con


class TestEsUnClosureReal:
    def test_devuelve_una_funcion(self):
        assert callable(crear_modificador_consumo(1.5))

    def test_captura_la_variable_factor(self):
        modificador = crear_modificador_consumo(1.5)
        assert modificador.__code__.co_freevars == ("factor",)
        assert modificador.__closure__ is not None
        assert modificador.__closure__[0].cell_contents == 1.5

    def test_cada_closure_guarda_su_propio_valor(self):
        doble = crear_modificador_consumo(2.0)
        mitad = crear_modificador_consumo(0.5)
        assert doble.__closure__[0].cell_contents == 2.0
        assert mitad.__closure__[0].cell_contents == 0.5

    def test_el_closure_tiene_nombre_propio_y_no_es_una_lambda(self):
        """Es una función con nombre (``def``), por la razón explicada en el código."""
        modificador = crear_modificador_consumo(1.5)
        assert modificador.__name__ == "modificador"
        assert modificador.__name__ != "<lambda>"

    def test_una_funcion_anidada_sin_variables_libres_no_es_closure(self):
        """Contraste: anidar una función no basta para tener un closure."""

        def fabrica():
            def interna(x):
                return x * 2  # solo usa su parámetro

            return interna

        assert fabrica().__closure__ is None
        assert crear_modificador_consumo(2.0).__closure__ is not None


class TestComportamiento:
    @pytest.mark.parametrize(
        "factor, base, esperado",
        [
            (1.0, 10, 10),
            (1.5, 10, 15),
            (2.0, 7, 14),
            (0.5, 10, 5),
            (0.0, 10, 0),
            (1.5, 5, 8),    # 7.5 se redondea hacia arriba
            (1.5, 3, 5),    # 4.5 se redondea hacia arriba
            (1.25, 6, 8),   # 7.5 se redondea hacia arriba
            (1.0, 0, 0),
        ],
    )
    def test_escala_el_consumo(self, factor, base, esperado):
        assert crear_modificador_consumo(factor)(base) == esperado

    def test_el_factor_se_conserva_despues_de_la_fabrica(self):
        modificador = crear_modificador_consumo(3.0)
        resultados = [modificador(n) for n in (1, 2, 3, 4)]
        assert resultados == [3, 6, 9, 12]
        assert modificador(5) == 15  # sigue recordando el 3.0

    def test_los_closures_son_independientes(self):
        doble = crear_modificador_consumo(2.0)
        mitad = crear_modificador_consumo(0.5)
        assert (doble(10), mitad(10)) == (20, 5)
        crear_modificador_consumo(100.0)  # crear otro no afecta a los anteriores
        assert (doble(10), mitad(10)) == (20, 5)

    def test_el_resultado_nunca_es_negativo(self):
        assert crear_modificador_consumo(1.0)(-5) == 0

    def test_factor_negativo_es_rechazado(self):
        with pytest.raises(ValueError):
            crear_modificador_consumo(-0.1)


class TestParticipaEnElSimulador:
    def test_calcular_consumo_usa_el_closure(self):
        modificador = crear_modificador_consumo(1.5)
        assert calcular_consumo(modificador) == {"agua": 9, "alimentos": 6, "energia": 6}

    def test_avanzar_turno_en_tormenta_consume_lo_calculado_por_el_closure(self):
        inicial = expedicion_con(clima="tormenta")
        esperado = calcular_consumo(crear_modificador_consumo(1.5))
        nuevo = avanzar_turno(inicial)
        assert inicial.recursos.agua - nuevo.recursos.agua == esperado["agua"]
        assert inicial.recursos.alimentos - nuevo.recursos.alimentos == esperado["alimentos"]
        assert inicial.recursos.energia - nuevo.recursos.energia == esperado["energia"]

    def test_la_tormenta_consume_mas_que_un_dia_despejado(self):
        despejado = avanzar_turno(expedicion_con(clima="despejado"))
        tormenta = avanzar_turno(expedicion_con(clima="tormenta"))
        assert tormenta.recursos.agua < despejado.recursos.agua
        assert tormenta.recursos.alimentos < despejado.recursos.alimentos
        assert tormenta.recursos.energia < despejado.recursos.energia

    def test_el_modificador_no_altera_el_consumo_base_compartido(self):
        antes = dict(CONSUMO_BASE)
        calcular_consumo(crear_modificador_consumo(5.0))
        assert dict(CONSUMO_BASE) == antes
