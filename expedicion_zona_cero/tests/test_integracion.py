"""Pruebas de integración (Fase 5): las tres capas funcionando juntas.

Un "bot" juega partidas completas a través de los callbacks reales de la ventana
(UI -> lógica -> modelo -> UI). Los dados son un generador con semilla fija, así
que cada partida es reproducible. Se omite sola si no hay Tkinter o pantalla.
"""

from __future__ import annotations

import random

import pytest

tk = pytest.importorskip("tkinter")
pytest.importorskip("ttkbootstrap")

from logic.actions import motivo_no_disponible  # noqa: E402
from models.events import Accion  # noqa: E402
from models.expedition import LIMITE_MAX, LIMITE_MIN, EstadoMision  # noqa: E402
from ui.presentacion import ACCIONES_UI  # noqa: E402

SEMILLAS = range(40)
MAX_PASOS = 200  # tope de seguridad: una partida real dura como mucho ~12 días


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
    monkeypatch.setattr(mw.messagebox, "askyesno", lambda *a, **k: False)
    monkeypatch.setattr(mw.messagebox, "showerror", lambda *a, **k: None)
    _ventana._numero = 1
    _ventana.expedicion = mw.crear_expedicion()
    _ventana.actualizar_indicadores()
    return _ventana


def jugar(v, mw, monkeypatch, semilla: int) -> list[str]:
    """Juega una partida completa con un bot sencillo. Devuelve el orden de pasos."""
    azar = random.Random(semilla)
    monkeypatch.setattr(mw, "tirar_dado", azar.random)
    pasos: list[str] = []
    for _ in range(MAX_PASOS):
        e = v.expedicion
        if e.estado is not EstadoMision.EN_CURSO:
            return pasos
        if e.evento_actual is not None:
            opcion = azar.choice(e.evento_actual.opciones)
            v._on_decision(opcion.clave)
            pasos.append(f"decision:{opcion.clave}")
        else:
            disponibles = [
                accion
                for _etiqueta, accion in ACCIONES_UI
                if motivo_no_disponible(e, accion) is None
            ]
            assert disponibles, f"semilla {semilla}: sin acciones válidas en el día {e.dia}"
            # Prefiere explorar si se puede; si no, cualquier acción disponible.
            elegida = Accion("explorar") if Accion("explorar") in disponibles else azar.choice(disponibles)
            v._on_accion(elegida)
            pasos.append(f"accion:{elegida.tipo}")
        # Invariantes que deben cumplirse SIEMPRE, también a mitad de partida.
        r = v.expedicion.recursos
        for valor in (r.agua, r.alimentos, r.energia, r.salud):
            assert LIMITE_MIN <= valor <= LIMITE_MAX
        assert 0 <= v.expedicion.progreso <= LIMITE_MAX
    pytest.fail(f"semilla {semilla}: la partida no terminó en {MAX_PASOS} pasos")


class TestPartidasCompletas:
    @pytest.mark.parametrize("semilla", SEMILLAS)
    def test_toda_partida_termina_en_un_estado_final_coherente(self, v, mw, monkeypatch, semilla):
        jugar(v, mw, monkeypatch, semilla)
        e = v.expedicion
        assert e.estado in (EstadoMision.COMPLETADA, EstadoMision.FALLIDA)
        assert e.evento_actual is None or e.estado is not EstadoMision.EN_CURSO
        assert len(e.historial) > 0
        if e.estado is EstadoMision.COMPLETADA:
            assert e.progreso == LIMITE_MAX
        # Con la misión terminada, la interfaz bloquea todas las acciones.
        assert all(str(b.cget("state")) == "disabled" for b in v._acciones._botones.values())

    def test_las_partidas_son_reproducibles_con_la_misma_semilla(self, v, mw, monkeypatch):
        primera = jugar(v, mw, monkeypatch, 7)
        final_1 = v.expedicion
        v.expedicion = mw.crear_expedicion()
        segunda = jugar(v, mw, monkeypatch, 7)
        assert primera == segunda
        assert v.expedicion.historial == final_1.historial

    def test_el_bot_logra_ambos_resultados(self, v, mw, monkeypatch):
        """Si solo hubiera un resultado posible, el balance del juego estaría roto."""
        resultados = set()
        for semilla in SEMILLAS:
            v.expedicion = mw.crear_expedicion()
            jugar(v, mw, monkeypatch, semilla)
            resultados.add(v.expedicion.estado)
        assert resultados == {EstadoMision.COMPLETADA, EstadoMision.FALLIDA}


class TestFlujoCompleto:
    def test_jugar_exportar_y_reiniciar(self, v, mw, monkeypatch, tmp_path):
        jugar(v, mw, monkeypatch, 3)
        final = v.expedicion
        destino = tmp_path / "reporte.txt"
        monkeypatch.setattr(mw.filedialog, "asksaveasfilename", lambda **k: str(destino))
        v._exportar()
        contenido = destino.read_text(encoding="utf-8")
        assert final.nombre in contenido
        assert f"Resultado: {final.estado.value}" in contenido
        assert f"Progreso: {final.progreso}/100" in contenido
        assert contenido.count("[Día") == len(final.historial)  # una línea por registro

        v._reiniciar()
        assert v.expedicion is not final
        assert v.expedicion.estado is EstadoMision.EN_CURSO
        assert v.expedicion.historial == ()
        assert v.expedicion.nombre != final.nombre
        assert all(str(b.cget("state")) in ("normal", "disabled") for b in v._acciones._botones.values())

    def test_el_punto_de_entrada_importa_sin_abrir_ventana(self):
        import main

        assert callable(main.main)
