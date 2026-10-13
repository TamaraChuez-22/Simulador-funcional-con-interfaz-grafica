#Pruebas de humo de la interfaz: abren la ventana (oculta) y usan sus callbacks.



from __future__ import annotations

import pytest

tk = pytest.importorskip("tkinter")
pytest.importorskip("ttkbootstrap")

from dataclasses import replace  # noqa: E402

from logic.expedition_service import asignar_evento, crear_expedicion  # noqa: E402
from models.events import CATALOGO_EVENTOS, Accion  # noqa: E402
from models.expedition import EstadoMision, Recursos  # noqa: E402
from tests.helpers import evento_por_tipo  # noqa: E402


@pytest.fixture(scope="module")
def mw():
    from ui import main_window

    return main_window


@pytest.fixture(scope="module")
def _ventana(mw):
    try:
        ventana = mw.VentanaPrincipal()
    except tk.TclError as error:
        pytest.skip(f"No hay pantalla disponible: {error}")
    ventana.withdraw()
    yield ventana
    ventana.destroy()


@pytest.fixture
def v(mw, _ventana, monkeypatch):
    """Ventana en estado inicial, sin diálogos bloqueantes y sin eventos al azar."""
    dialogos = {"preguntas": [], "errores": []}

    def preguntar(titulo, mensaje, **kwargs):
        dialogos["preguntas"].append((titulo, mensaje))
        return dialogos.get("respuesta", False)

    monkeypatch.setattr(mw.messagebox, "askyesno", preguntar)
    monkeypatch.setattr(mw.messagebox, "showerror", lambda *a, **k: dialogos["errores"].append(a))
    monkeypatch.setattr(mw, "tirar_dado", lambda: 0.99)  # 0.99 = nunca hay evento
    _ventana._numero = 1
    _ventana.expedicion = crear_expedicion()
    _ventana.mostrar_mensaje("", "info")
    _ventana.actualizar_indicadores()
    _ventana.dialogos = dialogos
    return _ventana


def texto(widget) -> str:
    return str(widget.cget("text"))


def estado(boton) -> str:
    return str(boton.cget("state"))


def estilo(widget) -> str:
    return str(widget.cget("style"))


class TestEstadoInicial:
    def test_el_encabezado_muestra_la_expedicion(self, v):
        assert texto(v._encabezado._nombre) == "Expedición Alfa"
        assert texto(v._encabezado._dia) == "DÍA 1 / 12"
        assert texto(v._encabezado._estado) == "EN CURSO"

    def test_los_indicadores_reflejan_los_recursos(self, v):
        valores = {n: texto(t._valor) for n, t in v._recursos._tarjetas.items()}
        assert valores == {
            "agua": "80/100", "alimentos": "80/100", "energia": "90/100", "salud": "100/100",
        }

    def test_la_tripulacion_esta_completa(self, v):
        assert texto(v._tripulacion._cuenta) == "4/4"
        assert texto(v._tripulacion._puntos) == "●●●●"

    def test_todas_las_acciones_estan_disponibles(self, v):
        assert all(estado(b) == "normal" for b in v._acciones._botones.values())

    def test_el_historial_empieza_vacio(self, v):
        assert texto(v._historial._contador) == "0/0"


class TestAcciones:
    def test_explorar_actualiza_el_estado_y_los_indicadores(self, v):
        v._on_accion(Accion("explorar"))
        assert v.expedicion.dia == 2 and v.expedicion.progreso == 16
        assert texto(v._encabezado._dia) == "DÍA 2 / 12"
        assert texto(v._encabezado._texto_progreso).endswith("16/100")
        assert texto(v._recursos._tarjetas["agua"]._valor) == "70/100"
        assert texto(v._historial._contador) == "2/2"

    def test_cada_accion_cambia_el_estado_inmutable(self, v):
        antes = v.expedicion
        v._on_accion(Accion("descansar"))
        assert v.expedicion is not antes
        assert antes.dia == 1 and antes.historial == ()  # el estado anterior no cambió

    def test_una_accion_rechazada_no_avanza_el_dia(self, v):
        v.expedicion = replace(v.expedicion, recursos=Recursos(80, 80, 5, 100))
        v._on_accion(Accion("explorar"))
        assert v.expedicion.dia == 1
        assert "energia" in texto(v._mensaje._etiqueta)

    def test_los_botones_se_deshabilitan_segun_los_recursos(self, v):
        v.expedicion = replace(v.expedicion, recursos=Recursos(80, 80, 5, 100))
        v.actualizar_indicadores()
        botones = v._acciones._botones
        assert estado(botones[Accion("explorar")]) == "disabled"
        assert estado(botones[Accion("descansar")]) == "normal"

    def test_los_recursos_bajos_cambian_de_color(self, v):
        v.expedicion = replace(v.expedicion, recursos=Recursos(15, 35, 90, 100))
        v.actualizar_indicadores()
        tarjetas = v._recursos._tarjetas
        assert estilo(tarjetas["agua"]._barra) == "danger.Horizontal.TProgressbar"
        assert estilo(tarjetas["alimentos"]._barra) == "warning.Horizontal.TProgressbar"
        assert estilo(tarjetas["energia"]._barra) == "primary.Horizontal.TProgressbar"


class TestTamanoDeLaVentana:
    """La ventana debe caber en pantallas de 1366x768 (con barra de tareas)."""

    ALTO_APROVECHABLE_768 = 768 - 48 - 32  # sin barra de tareas ni de título

    def test_el_alto_minimo_cabe_en_una_pantalla_de_768(self, v):
        assert v.minsize()[1] <= self.ALTO_APROVECHABLE_768
        assert v.minsize()[0] <= 1366 - 40

    def test_el_minimo_nunca_supera_el_tamano_natural(self, v):
        v.update_idletasks()
        assert v.minsize()[0] <= v.winfo_reqwidth()

    def test_la_fila_del_evento_reserva_alto_para_cualquier_evento(self, v):
        """El evento más exigente cabe sin cortarse y sin cambiar el tamaño."""
        reservado = int(v._centro.grid_rowconfigure(0)["minsize"])
        for evento in CATALOGO_EVENTOS:
            v.expedicion = asignar_evento(crear_expedicion(), evento)
            v.actualizar_indicadores()
            v.update_idletasks()
            assert v._evento.winfo_reqheight() <= reservado, evento.tipo

    def test_las_acciones_siguen_visibles_pero_bloqueadas_durante_un_evento(self, v):
        assert v._acciones.winfo_manager() == "grid"
        v.expedicion = asignar_evento(v.expedicion, evento_por_tipo("averia"))
        v.actualizar_indicadores()
        assert v._acciones.winfo_manager() == "grid"  # siguen visibles
        assert all(estado(b) == "disabled" for b in v._acciones._botones.values())
        v._on_decision("reparar")
        assert v._acciones.winfo_manager() == "grid"
        assert all(estado(b) == "normal" for b in v._acciones._botones.values())


class TestEventos:
    def test_un_evento_muestra_sus_decisiones_y_bloquea_las_acciones(self, v):
        v.expedicion = asignar_evento(v.expedicion, evento_por_tipo("provisiones"))
        v.actualizar_indicadores()
        assert len(v._evento._opciones.winfo_children()) == 3
        assert texto(v._evento._titulo) == "Hallazgo de provisiones"
        assert all(estado(b) == "disabled" for b in v._acciones._botones.values())

    def test_decidir_resuelve_el_evento(self, v):
        v.expedicion = asignar_evento(v.expedicion, evento_por_tipo("provisiones"))
        v.actualizar_indicadores()
        v._on_decision("solo_agua")
        assert v.expedicion.evento_actual is None
        assert v.expedicion.recursos.agua == 100
        assert not v._evento._opciones.winfo_children()
        assert all(estado(b) == "normal" for b in v._acciones._botones.values())

    def test_una_opcion_desconocida_no_cambia_nada(self, v):
        v.expedicion = asignar_evento(v.expedicion, evento_por_tipo("averia"))
        v.actualizar_indicadores()
        antes = v.expedicion
        v._on_decision("inventada")
        assert v.expedicion is antes

    def test_un_evento_puede_llegar_tras_una_accion(self, v, mw, monkeypatch):
        monkeypatch.setattr(mw, "tirar_dado", lambda: 0.0)  # 0.0 = primer evento
        v._on_accion(Accion("descansar"))
        assert v.expedicion.evento_actual is CATALOGO_EVENTOS[0]
        assert texto(v._evento._titulo) == CATALOGO_EVENTOS[0].titulo

    def test_cada_evento_del_catalogo_se_puede_mostrar_y_resolver(self, v):
        for evento in CATALOGO_EVENTOS:
            v.expedicion = asignar_evento(crear_expedicion(), evento)
            v.actualizar_indicadores()
            assert len(v._evento._opciones.winfo_children()) == len(evento.opciones)
            v._on_decision(evento.opciones[0].clave)
            assert v.expedicion.evento_actual is None


class TestFinDeMision:
    def test_completar_la_mision_bloquea_las_acciones_y_ofrece_el_reporte(self, v):
        v.expedicion = replace(v.expedicion, progreso=90)
        v._on_accion(Accion("explorar"))
        assert v.expedicion.estado is EstadoMision.COMPLETADA
        assert texto(v._encabezado._estado) == "COMPLETADA"
        assert all(estado(b) == "disabled" for b in v._acciones._botones.values())
        assert len(v.dialogos["preguntas"]) == 1
        assert "completada" in v.dialogos["preguntas"][0][1]

    def test_fracasar_se_anuncia_una_sola_vez(self, v):
        v.expedicion = replace(v.expedicion, dia=12, progreso=10)
        v._on_accion(Accion("descansar"))
        assert v.expedicion.estado is EstadoMision.FALLIDA
        v._on_accion(Accion("descansar"))  # ya terminó: no debe anunciar de nuevo
        assert len(v.dialogos["preguntas"]) == 1

    def test_el_reporte_se_exporta_si_el_usuario_acepta(self, v, mw, monkeypatch, tmp_path):
        destino = tmp_path / "final.txt"
        monkeypatch.setattr(mw.filedialog, "asksaveasfilename", lambda **k: str(destino))
        v.dialogos["respuesta"] = True
        v.expedicion = replace(v.expedicion, progreso=90)
        v._on_accion(Accion("explorar"))
        assert destino.exists()
        assert "Completada" in destino.read_text(encoding="utf-8")


class TestReinicioYExportacion:
    def test_reiniciar_con_la_mision_en_curso_pide_confirmacion(self, v):
        v._on_accion(Accion("explorar"))
        v.dialogos["respuesta"] = False
        v._reiniciar()
        assert v.expedicion.dia == 2  # no se reinició
        assert len(v.dialogos["preguntas"]) == 1

    def test_reiniciar_confirmado_parte_de_un_estado_limpio(self, v):
        for _ in range(3):
            v._on_accion(Accion("explorar"))
        v.dialogos["respuesta"] = True
        v._reiniciar()
        e = v.expedicion
        assert e.nombre == "Expedición Beta"
        assert e.dia == 1 and e.progreso == 0 and e.historial == ()
        assert e.recursos == Recursos(80, 80, 90, 100)
        assert texto(v._encabezado._nombre) == "Expedición Beta"
        assert texto(v._historial._contador) == "0/0"

    def test_reiniciar_tras_terminar_no_pregunta(self, v):
        v.expedicion = replace(v.expedicion, estado=EstadoMision.FALLIDA)
        v._reiniciar()
        assert v.dialogos["preguntas"] == []
        assert v.expedicion.estado is EstadoMision.EN_CURSO

    def test_reiniciar_usa_la_dificultad_elegida(self, v):
        v._controles._dificultad.set("Difícil")
        v.expedicion = replace(v.expedicion, estado=EstadoMision.FALLIDA)
        v._reiniciar()
        assert v.expedicion.dificultad == "dificil"
        assert texto(v._tripulacion._dificultad) == "Difícil"
        v._controles._dificultad.set("Normal")

    def test_exportar_escribe_el_archivo(self, v, mw, monkeypatch, tmp_path):
        destino = tmp_path / "reporte.txt"
        monkeypatch.setattr(mw.filedialog, "asksaveasfilename", lambda **k: str(destino))
        v._on_accion(Accion("explorar"))
        v._exportar()
        assert "Expedición Alfa" in destino.read_text(encoding="utf-8")
        assert "Reporte guardado" in texto(v._mensaje._etiqueta)

    def test_cancelar_la_exportacion_no_hace_nada(self, v, mw, monkeypatch):
        monkeypatch.setattr(mw.filedialog, "asksaveasfilename", lambda **k: "")
        v._exportar()
        assert "Reporte guardado" not in texto(v._mensaje._etiqueta)

    def test_un_error_al_guardar_se_informa(self, v, mw, monkeypatch, tmp_path):
        inexistente = tmp_path / "no_existe" / "reporte.txt"
        monkeypatch.setattr(mw.filedialog, "asksaveasfilename", lambda **k: str(inexistente))
        v._exportar()
        assert len(v.dialogos["errores"]) == 1
        assert "No se pudo guardar" in texto(v._mensaje._etiqueta)


class TestHistorialYFiltros:
    def test_el_filtro_reduce_lo_que_se_muestra(self, v):
        for _ in range(3):
            v._on_accion(Accion("explorar"))
        assert texto(v._historial._contador) == "6/6"
        v._historial._filtro.set("Acciones")
        v._historial._dibujar()
        assert texto(v._historial._contador) == "3/6"
        v._historial._filtro.set("Críticos")
        v._historial._dibujar()
        assert texto(v._historial._contador) == "0/6"
        v._historial._filtro.set("Todo")

    def test_el_texto_del_historial_es_de_solo_lectura(self, v):
        assert str(v._historial._texto.cget("state")) == "disabled"


class TestMensajes:
    @pytest.mark.parametrize(
        "nivel, estilo_esperado",
        [
            ("info", "@secondary.TLabel"),
            ("success", "@success.TLabel"),
            ("warning", "@warning.TLabel"),
            ("error", "@danger.TLabel"),
        ],
    )
    def test_cada_nivel_tiene_su_estilo(self, v, nivel, estilo_esperado):
        v.mostrar_mensaje("hola", nivel)
        assert estilo(v._mensaje._etiqueta) == estilo_esperado
        assert texto(v._mensaje._etiqueta) == "hola"

    def test_un_nivel_desconocido_usa_el_estilo_neutro(self, v):
        v.mostrar_mensaje("hola", "raro")
        assert estilo(v._mensaje._etiqueta) == "@secondary.TLabel"
