"""Pruebas de las funciones PURAS de la capa visual (no abren ninguna ventana)."""

from __future__ import annotations

import pytest

from logic.expedition_service import UMBRAL_ALERTA, crear_expedicion
from models.events import Accion, Efecto
from models.expedition import EstadoMision, Registro
from tests.helpers import expedicion_con
from ui.presentacion import (
    ACCIONES_UI,
    ALTO_IDEAL,
    ANCHO_IDEAL,
    CRITERIOS_HISTORIAL,
    MARGEN_ALTO_PANTALLA,
    PALETA,
    UMBRAL_BAJO,
    aplicar_filtro,
    calcular_geometria,
    color_nivel,
    describir_accion,
    elegir_fuente,
    estilo_barra,
    estilo_boton_accion,
    etiqueta_dia,
    etiqueta_estado,
    etiqueta_tag,
    formatear_registro,
    indicador_tripulacion,
    nivel_recurso,
    nombre_expedicion,
    resumen_efecto,
    texto_clima,
    texto_consumo,
    texto_dificultad,
    texto_objetivo,
    texto_recurso,
)


class TestRecursos:
    @pytest.mark.parametrize(
        "valor, nivel",
        [
            (100, "ok"),
            (UMBRAL_BAJO + 1, "ok"),
            (UMBRAL_BAJO, "bajo"),
            (UMBRAL_ALERTA + 1, "bajo"),
            (UMBRAL_ALERTA, "critico"),
            (0, "critico"),
        ],
    )
    def test_nivel_recurso(self, valor, nivel):
        assert nivel_recurso(valor) == nivel

    def test_estilo_barra_sigue_el_nivel(self):
        assert estilo_barra(90) == "primary"
        assert estilo_barra(30) == "warning"
        assert estilo_barra(5) == "danger"

    def test_color_nivel(self):
        assert color_nivel(90) == PALETA["texto"]
        assert color_nivel(30) == PALETA["naranja"]
        assert color_nivel(5) == PALETA["rojo"]

    def test_texto_recurso(self):
        assert texto_recurso(80) == "80/100"
        assert texto_recurso(0) == "0/100"


class TestEncabezado:
    def test_etiqueta_dia(self):
        assert etiqueta_dia(crear_expedicion()) == "DÍA 1 / 12"

    def test_etiqueta_dia_nunca_supera_el_limite(self):
        assert etiqueta_dia(expedicion_con(dia=13)) == "DÍA 12 / 12"

    @pytest.mark.parametrize(
        "estado, texto",
        [
            (EstadoMision.EN_CURSO, "EN CURSO"),
            (EstadoMision.COMPLETADA, "COMPLETADA"),
            (EstadoMision.FALLIDA, "FALLIDA"),
        ],
    )
    def test_etiqueta_estado_cubre_todos_los_estados(self, estado, texto):
        assert etiqueta_estado(estado)[0] == texto

    def test_etiqueta_estado_usa_estilos_distintos(self):
        estilos = {etiqueta_estado(estado)[1] for estado in EstadoMision}
        assert len(estilos) == len(EstadoMision)

    def test_texto_objetivo_menciona_la_meta_y_el_limite(self):
        texto = texto_objetivo(crear_expedicion())
        assert "100" in texto and "12" in texto

    def test_nombre_expedicion(self):
        assert nombre_expedicion(1) == "Expedición Alfa"
        assert nombre_expedicion(2) == "Expedición Beta"
        assert nombre_expedicion(8) == "Expedición Theta"

    def test_nombre_expedicion_da_la_vuelta_con_sufijo(self):
        assert nombre_expedicion(9) == "Expedición Alfa 2"
        assert nombre_expedicion(10) == "Expedición Beta 2"

    def test_nombre_expedicion_rechaza_numeros_invalidos(self):
        with pytest.raises(ValueError):
            nombre_expedicion(0)

    def test_nombres_consecutivos_son_distintos(self):
        nombres = [nombre_expedicion(n) for n in range(1, 30)]
        assert len(set(nombres)) == len(nombres)

    def test_texto_consumo(self):
        assert texto_consumo({"agua": 6, "alimentos": 4, "energia": 4}) == (
            "Agua -6   Alimentos -4   Energía -4"
        )


class TestTripulacion:
    @pytest.mark.parametrize(
        "integrantes, esperado",
        [(4, "●●●●"), (3, "●●●○"), (1, "●○○○"), (0, "○○○○")],
    )
    def test_indicador_tripulacion(self, integrantes, esperado):
        assert indicador_tripulacion(integrantes, 4) == esperado

    def test_indicador_tripulacion_con_valores_fuera_de_rango(self):
        assert indicador_tripulacion(9, 4) == "●●●●"
        assert indicador_tripulacion(-2, 4) == "○○○○"

    def test_clima_y_dificultad(self):
        assert texto_clima("despejado") == "Despejado"
        assert texto_clima("tormenta") == "TORMENTA"
        assert texto_clima("nieve") == "Nieve"
        assert texto_dificultad("normal") == "Normal"
        assert texto_dificultad("dificil") == "Difícil"


class TestEfectosYAcciones:
    def test_resumen_efecto(self):
        efecto = Efecto(agua=20, energia=-8, progreso=5)
        assert resumen_efecto(efecto) == "+20 agua, -8 energía, +5 progreso"

    def test_resumen_efecto_vacio(self):
        assert resumen_efecto(Efecto()) == ""

    def test_resumen_efecto_incluye_integrantes(self):
        assert resumen_efecto(Efecto(integrantes=-1)) == "-1 integrantes"

    def test_describir_accion_usa_los_numeros_reales_de_la_logica(self):
        texto = describir_accion(Accion("explorar"), 4)
        assert "16" in texto  # 4 integrantes x 4 puntos
        assert "+16 progreso" in texto

    def test_describir_accion_depende_de_los_integrantes(self):
        assert "+8 progreso" in describir_accion(Accion("explorar"), 2)

    def test_todas_las_acciones_del_panel_se_pueden_describir(self):
        for _etiqueta, accion in ACCIONES_UI:
            assert describir_accion(accion, 4)

    def test_las_acciones_del_panel_son_distintas(self):
        acciones = [accion for _etiqueta, accion in ACCIONES_UI]
        assert len(set(acciones)) == len(acciones)
        etiquetas = [etiqueta for etiqueta, _accion in ACCIONES_UI]
        assert len(set(etiquetas)) == len(etiquetas)

    def test_el_panel_cubre_las_cinco_acciones_del_dominio(self):
        tipos = {accion.tipo for _etiqueta, accion in ACCIONES_UI}
        assert tipos == {
            "explorar", "descansar", "consumir_recurso", "recolectar", "atender_emergencia",
        }

    def test_estilo_boton_accion(self):
        assert estilo_boton_accion(Accion("atender_emergencia")) == "warning-outline"
        assert estilo_boton_accion(Accion("explorar")) == "primary-outline"


class TestHistorial:
    HISTORIAL = (
        Registro(1, "accion", "explorar"),
        Registro(1, "turno", "fin del día"),
        Registro(2, "evento", "tormenta", critico=False),
        Registro(2, "decision", "refugiarse"),
        Registro(3, "evento", "avería", critico=True),
        Registro(3, "sistema", "Misión fallida.", critico=True),
    )

    def test_formatear_registro(self):
        assert formatear_registro(Registro(3, "accion", "explorar")) == "D03 ACCIÓN   explorar"

    def test_formatear_registro_marca_los_criticos(self):
        texto = formatear_registro(Registro(12, "evento", "avería", critico=True))
        assert texto.startswith("D12 EVENTO")
        assert "(!)" in texto

    def test_formatear_registro_con_tipo_desconocido(self):
        assert "RARO" in formatear_registro(Registro(1, "raro", "x"))

    def test_etiqueta_tag(self):
        assert etiqueta_tag(Registro(1, "accion", "x")) == "accion"
        assert etiqueta_tag(Registro(1, "accion", "x", critico=True)) == "critico"

    def test_todo_devuelve_todo(self):
        assert aplicar_filtro("Todo", self.HISTORIAL) == self.HISTORIAL

    def test_criticos(self):
        assert [r.descripcion for r in aplicar_filtro("Críticos", self.HISTORIAL)] == [
            "avería", "Misión fallida.",
        ]

    def test_acciones(self):
        assert [r.descripcion for r in aplicar_filtro("Acciones", self.HISTORIAL)] == ["explorar"]

    def test_eventos_y_decisiones(self):
        assert [r.tipo for r in aplicar_filtro("Eventos y decisiones", self.HISTORIAL)] == [
            "evento", "decision", "evento",
        ]

    def test_turnos(self):
        assert len(aplicar_filtro("Turnos", self.HISTORIAL)) == 1

    def test_filtro_desconocido_se_rechaza(self):
        with pytest.raises(ValueError):
            aplicar_filtro("Inventado", self.HISTORIAL)

    def test_filtrar_con_historial_vacio(self):
        for nombre in CRITERIOS_HISTORIAL:
            assert aplicar_filtro(nombre, ()) == ()

    def test_aplicar_filtro_no_modifica_el_historial(self):
        copia = tuple(self.HISTORIAL)
        for nombre in CRITERIOS_HISTORIAL:
            aplicar_filtro(nombre, self.HISTORIAL)
        assert self.HISTORIAL == copia


class TestFuentes:
    def test_elige_la_primera_preferida_disponible(self):
        assert elegir_fuente(["Segoe UI", "Arial"], ["Arial", "Segoe UI"], "X") == "Segoe UI"

    def test_salta_las_que_no_existen(self):
        assert elegir_fuente(["Segoe UI", "Inter", "Arial"], ["Arial"], "X") == "Arial"

    def test_ignora_mayusculas_y_devuelve_el_nombre_real(self):
        assert elegir_fuente(["segoe ui"], ["Segoe UI"], "X") == "Segoe UI"

    def test_usa_el_valor_por_defecto_si_no_hay_ninguna(self):
        assert elegir_fuente(["Segoe UI"], ["Courier"], "Fallback") == "Fallback"

    def test_sin_fuentes_disponibles(self):
        assert elegir_fuente(["Segoe UI"], [], "Fallback") == "Fallback"


class TestPaleta:
    def test_la_paleta_es_de_solo_lectura(self):
        with pytest.raises(TypeError):
            PALETA["oro"] = "#000000"

    def test_todos_los_colores_son_hexadecimales_validos(self):
        for nombre, color in PALETA.items():
            assert len(color) == 7 and color.startswith("#"), nombre
            int(color[1:], 16)


class TestGeometria:
    """El tamaño de la ventana depende de la pantalla y del contenido."""

    NATURAL = (1185, 582)  # tamaño natural medido en la ventana real

    def test_pantalla_grande_usa_el_tamano_ideal(self):
        assert calcular_geometria(*self.NATURAL, 1920, 1080) == (ANCHO_IDEAL, ALTO_IDEAL)

    def test_pantalla_de_720_deja_sitio_para_la_barra_de_tareas(self):
        ancho, alto = calcular_geometria(*self.NATURAL, 1280, 720)
        assert alto == 720 - MARGEN_ALTO_PANTALLA
        # Valor literal (no la constante): título (~32 px) + barra de tareas (~48 px).
        assert alto <= 720 - 80
        assert ancho <= 1280

    def test_pantalla_de_768(self):
        assert calcular_geometria(*self.NATURAL, 1366, 768) == (1280, 768 - MARGEN_ALTO_PANTALLA)

    def test_nunca_baja_del_tamano_natural_del_contenido(self):
        # Pantalla diminuta: es mejor una ventana completa que widgets cortados.
        assert calcular_geometria(*self.NATURAL, 800, 480) == self.NATURAL

    def test_nunca_supera_el_tamano_ideal(self):
        ancho, alto = calcular_geometria(*self.NATURAL, 7680, 4320)
        assert (ancho, alto) == (ANCHO_IDEAL, ALTO_IDEAL)

    def test_un_contenido_mayor_que_el_ideal_se_respeta(self):
        assert calcular_geometria(1400, 900, 1920, 1080) == (1400, 900)

    @pytest.mark.parametrize("pantalla", [(1280, 720), (1366, 768), (1920, 1080), (1024, 600)])
    def test_el_resultado_es_siempre_valido(self, pantalla):
        ancho, alto = calcular_geometria(*self.NATURAL, *pantalla)
        assert ancho >= self.NATURAL[0] and alto >= self.NATURAL[1]
