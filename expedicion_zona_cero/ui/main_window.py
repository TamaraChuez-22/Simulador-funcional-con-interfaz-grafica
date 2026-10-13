#Capa visual: ventana principal.

from __future__ import annotations

from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from logic.actions import motivo_no_disponible
from logic.expedition_service import (
    consumo_proyectado,
    crear_expedicion,
    ejecutar_turno,
    resolver_evento,
    tirar_dado,
)
from logic.reports import calcular_puntuacion, exportar_reporte
from models.events import CATALOGO_EVENTOS, Accion
from models.expedition import INTEGRANTES_INICIALES, EstadoMision, Expedicion, ResultadoAccion

from .components import (
    MARGEN,
    BarraMensaje,
    Encabezado,
    PanelAcciones,
    PanelControles,
    PanelEvento,
    PanelHistorial,
    PanelRecursos,
    PanelTripulacion,
    aplicar_tema,
    configurar_fuentes,
)
from .presentacion import (
    ACCIONES_UI,
    calcular_geometria,
    describir_accion,
    nombre_expedicion,
    texto_objetivo,
)


class VentanaPrincipal(ttk.Window):
    
    def __init__(self) -> None:
        super().__init__(title="Expedición: Zona Cero", theme="bootstrap-dark")
        aplicar_tema(self.style)
        # Se guarda la referencia: si se pierde, Tk borra las fuentes con nombre.
        self._fuentes = configurar_fuentes(self, self.style)

        self._numero = 1
        self.expedicion: Expedicion = crear_expedicion(nombre_expedicion(self._numero))

        self._construir()
        self.actualizar_indicadores()
        self._ajustar_tamano()

    #UI
    def _ajustar_tamano(self) -> None:
    
        self.update_idletasks()
        req_ancho, req_alto = self.winfo_reqwidth(), self.winfo_reqheight()
        ancho, alto = calcular_geometria(
            req_ancho, req_alto, self.winfo_screenwidth(), self.winfo_screenheight()
        )
        self.minsize(req_ancho, req_alto)
        self.geometry(f"{ancho}x{alto}")

    def _construir(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._encabezado = Encabezado(self)
        self._encabezado.grid(row=0, column=0, sticky="ew")

        cuerpo = ttk.Frame(self, padding=(MARGEN + 8, 0, MARGEN + 8, 0))
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.columnconfigure(0, weight=0, minsize=300)
        cuerpo.columnconfigure(1, weight=3, minsize=460)
        cuerpo.columnconfigure(2, weight=2, minsize=340)
        cuerpo.rowconfigure(0, weight=1)

        izquierda = ttk.Frame(cuerpo)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, MARGEN))
        izquierda.columnconfigure(0, weight=1)
        self._recursos = PanelRecursos(izquierda)
        self._recursos.grid(row=0, column=0, sticky="ew")
        self._tripulacion = PanelTripulacion(izquierda, INTEGRANTES_INICIALES)
        self._tripulacion.grid(row=1, column=0, sticky="ew", pady=(MARGEN, 0))

        centro = self._centro = ttk.Frame(cuerpo)
        centro.grid(row=0, column=1, sticky="nsew", padx=(0, MARGEN))
        centro.columnconfigure(0, weight=1)
        centro.rowconfigure(0, weight=1)
        self._evento = PanelEvento(centro, self._on_decision)
        self._evento.grid(row=0, column=0, sticky="nsew")
        self._acciones = PanelAcciones(centro, ACCIONES_UI, self._on_accion)
        self._acciones.grid(row=1, column=0, sticky="ew", pady=(MARGEN, 0))

        self._historial = PanelHistorial(cuerpo)
        self._historial.grid(row=0, column=2, sticky="nsew")

        pie = ttk.Frame(self, padding=(MARGEN + 8, 6, MARGEN + 8, MARGEN))
        pie.grid(row=2, column=0, sticky="ew")
        pie.columnconfigure(0, weight=1)
        self._mensaje = BarraMensaje(pie)
        self._mensaje.grid(row=0, column=0, sticky="ew", padx=(0, MARGEN + 6))
        self._controles = PanelControles(pie, self._reiniciar, self._exportar)
        self._controles.grid(row=0, column=1, sticky="e")
        self._reservar_alto_eventos()

    def _reservar_alto_eventos(self) -> None:
        
        maximo = 0
        for evento in CATALOGO_EVENTOS:
            self._evento.mostrar(evento, "")
            self.update_idletasks()
            maximo = max(maximo, self._evento.winfo_reqheight())
        self._evento.mostrar(None, "")
        self._centro.rowconfigure(0, weight=1, minsize=maximo)

    def _on_accion(self, accion: Accion) -> None:
        self._aplicar(ejecutar_turno(self.expedicion, accion, tirar_dado()))

    def _on_decision(self, clave: str) -> None:
        self._aplicar(resolver_evento(self.expedicion, clave, tirar_dado()))

    def _aplicar(self, resultado: ResultadoAccion) -> None:
        antes = self.expedicion.estado
        self.expedicion = resultado.expedicion
        self.mostrar_mensaje(resultado.mensaje, resultado.nivel)
        self.actualizar_indicadores()
        if antes is EstadoMision.EN_CURSO and self.expedicion.estado is not antes:
            self._anunciar_fin()

    def _reiniciar(self) -> None:
        en_curso = self.expedicion.estado is EstadoMision.EN_CURSO
        if en_curso and not messagebox.askyesno(
            "Nueva expedición",
            "La expedición actual sigue en curso y se perderá.\n¿Iniciar una nueva?",
            parent=self,
        ):
            return
        self._numero += 1
        self.expedicion = crear_expedicion(
            nombre_expedicion(self._numero), self._controles.dificultad_elegida()
        )
        self.mostrar_mensaje(f"Nueva expedición lista: {self.expedicion.nombre}.", "success")
        self.actualizar_indicadores()

    def _exportar(self) -> None:
        nombre = self.expedicion.nombre.lower().replace(" ", "_")
        ruta = filedialog.asksaveasfilename(
            parent=self, title="Exportar reporte", defaultextension=".txt",
            initialfile=f"reporte_{nombre}.txt", filetypes=[("Texto", "*.txt")],
        )
        if not ruta:
            return
        try:
            destino = exportar_reporte(self.expedicion, ruta)
        except OSError as error:
            messagebox.showerror("No se pudo exportar", str(error), parent=self)
            self.mostrar_mensaje(f"No se pudo guardar el reporte: {error}", "error")
            return
        self.mostrar_mensaje(f"Reporte guardado en {destino}.", "success")

    
    def mostrar_mensaje(self, texto: str, nivel: str = "info") -> None:
        self._mensaje.mostrar(texto, nivel)

    def actualizar_indicadores(self) -> None:
        e = self.expedicion
        acciones = [accion for _etiqueta, accion in ACCIONES_UI]
        self._encabezado.actualizar(e)
        self._recursos.actualizar(e.recursos)
        self._tripulacion.actualizar(e, consumo_proyectado(e))
        self._evento.mostrar(e.evento_actual, texto_objetivo(e))
        self._acciones.actualizar(
            {accion: motivo_no_disponible(e, accion) for accion in acciones},
            {accion: describir_accion(accion, e.integrantes) for accion in acciones},
        )
        self._historial.mostrar(e.historial)

    def _anunciar_fin(self) -> None:
        """IMPURA: informa el resultado final y ofrece exportar el reporte."""
        e = self.expedicion
        completada = e.estado is EstadoMision.COMPLETADA
        titulo = "¡Misión completada!" if completada else "Misión fallida"
        cuerpo = (
            f"{e.nombre}: {e.estado.value.lower()}.\n"
            f"Progreso {e.progreso}/100 · Integrantes {e.integrantes} · "
            f"Puntuación {calcular_puntuacion(e)}\n\n¿Quieres exportar el reporte?"
        )
        if messagebox.askyesno(titulo, cuerpo, parent=self):
            self._exportar()
