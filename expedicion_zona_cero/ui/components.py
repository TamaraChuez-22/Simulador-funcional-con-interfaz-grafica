"""Capa visual: tema y widgets reutilizables.

Los widgets de este módulo solo DIBUJAN lo que se les entrega: no calculan
reglas del juego. Los métodos ``actualizar``/``mostrar`` son IMPUROS porque
modifican widgets (efecto secundario sobre la interfaz).
"""

from __future__ import annotations

import tkinter as tk
from functools import partial
from tkinter import font as tkfont
from typing import Callable, Mapping, Sequence

import ttkbootstrap as ttk
from ttkbootstrap.style import ThemeDefinition

from models.events import Accion, Evento
from models.expedition import (
    LIMITE_MAX,
    META_PROGRESO,
    NOMBRES_RECURSOS,
    Expedicion,
    Recursos,
    Registro,
)

from .presentacion import (
    CRITERIOS_HISTORIAL,
    DIFICULTADES_UI,
    NOMBRES_VISIBLES,
    PALETA,
    aplicar_filtro,
    color_nivel,
    elegir_fuente,
    estilo_barra,
    estilo_boton_accion,
    etiqueta_dia,
    etiqueta_estado,
    etiqueta_progreso,
    etiqueta_tag,
    formatear_registro,
    indicador_tripulacion,
    resumen_efecto,
    texto_clima,
    texto_consumo,
    texto_dificultad,
    texto_recurso,
)

NOMBRE_TEMA = "zona_cero"
MARGEN = 10  # espaciado base entre paneles
ANCHO_BOTON_DECISION = 230  # ancho fijo (px) del botón de cada decisión de un evento
ANCHO_TEXTO_INICIAL = 480  # ancho de ajuste del texto antes de conocer el real

COLORES_TEMA = {
    "primary": PALETA["oro"],
    "secondary": "#2A3144",
    "success": PALETA["verde"],
    "info": PALETA["turquesa"],
    "warning": PALETA["naranja"],
    "danger": PALETA["rojo"],
    "light": "#C9D1E3",
    "dark": PALETA["panel"],
    "bg": PALETA["fondo"],
    "fg": PALETA["texto"],
    "selectbg": "#2A3144",
    "selectfg": PALETA["oro_claro"],
    "border": PALETA["borde"],
    "inputfg": PALETA["texto"],
    "inputbg": PALETA["campo"],
    "active": "#1B2233",
}

FUENTES_SANS = ("Segoe UI", "Inter", "Helvetica Neue", "Arial", "DejaVu Sans")


# --------------------------------------------------------------------------
# Tema y fuentes (IMPURAS: configuran el motor de estilos de Tk)
# --------------------------------------------------------------------------
def aplicar_tema(estilo: ttk.Style) -> None:
    """Registra y activa el tema oscuro + oro eléctrico."""
    estilo.register_theme(ThemeDefinition(NOMBRE_TEMA, COLORES_TEMA, mode="dark"))
    estilo.theme_use(NOMBRE_TEMA)


def _fuente(raiz: tk.Misc, nombre: str, **opciones) -> tkfont.Font:
    """Crea una fuente con nombre o, si ya existe en este intérprete, la actualiza."""
    try:
        existente = tkfont.nametofont(nombre, root=raiz)
    except tk.TclError:
        return tkfont.Font(root=raiz, name=nombre, **opciones)
    existente.configure(**opciones)
    return existente


def configurar_fuentes(raiz: tk.Misc, estilo: ttk.Style) -> dict[str, tkfont.Font]:
    """Crea las fuentes con nombre ``ZC.*`` y las asigna a los estilos base.

    IMPORTANTE: devuelve las fuentes y quien llama DEBE conservarlas. Tkinter
    borra una fuente con nombre en cuanto el objeto ``Font`` que la creó es
    recogido por el recolector de basura, y los widgets volverían a la fuente
    por defecto sin avisar.
    """
    defecto = tkfont.nametofont("TkDefaultFont", root=raiz).actual("family")
    familia = elegir_fuente(FUENTES_SANS, tkfont.families(raiz), defecto)
    definiciones = {
        "ZC.Logo": {"size": 22, "weight": "bold"},
        "ZC.Panel": {"size": 9, "weight": "bold"},
        "ZC.Titulo": {"size": 14, "weight": "bold"},
        "ZC.Valor": {"size": 15, "weight": "bold"},
        "ZC.Etiqueta": {"size": 9, "weight": "bold"},
        "ZC.Normal": {"size": 10},
        "ZC.Pequena": {"size": 9},
        "ZC.Boton": {"size": 10, "weight": "bold"},
    }
    fuentes = {
        nombre: _fuente(raiz, nombre, family=familia, **opciones)
        for nombre, opciones in definiciones.items()
    }
    for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
        tkfont.nametofont(nombre, root=raiz).configure(family=familia, size=10)
    estilo.configure("TLabelframe.Label", font="ZC.Panel", foreground=PALETA["oro"])
    estilo.configure("TButton", font="ZC.Boton", padding=(14, 9))
    estilo.configure("TCombobox", padding=6)
    return fuentes


# --------------------------------------------------------------------------
# Encabezado
# --------------------------------------------------------------------------
class Encabezado(ttk.Frame):
    """Logotipo textual, expedición activa, día, estado y progreso de la misión."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(24, 8, 24, 2))
        self.columnconfigure(1, weight=1)

        logo = ttk.Frame(self)
        logo.grid(row=0, column=0, sticky="w")
        ttk.Label(
            logo, text="E X P E D I C I Ó N", font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).pack(anchor="w")
        ttk.Label(
            logo, text="ZONA CERO", font="ZC.Logo", foreground=PALETA["oro"]
        ).pack(anchor="w")

        datos = ttk.Frame(self)
        datos.grid(row=0, column=2, sticky="e")
        self._nombre = ttk.Label(datos, font="ZC.Titulo")
        self._nombre.grid(row=0, column=0, columnspan=2, sticky="e")
        self._dia = ttk.Label(datos, font="ZC.Valor", foreground=PALETA["oro"])
        self._dia.grid(row=1, column=0, sticky="e", padx=(0, 14), pady=(4, 0))
        self._estado = ttk.Label(datos, font="ZC.Etiqueta", padding=(12, 4), anchor="center")
        self._estado.grid(row=1, column=1, sticky="e", pady=(4, 0))

        avance = ttk.Frame(self)
        avance.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        avance.columnconfigure(1, weight=1)
        self._texto_progreso = ttk.Label(
            avance, font="ZC.Etiqueta", foreground=PALETA["tenue"], width=16
        )
        self._texto_progreso.grid(row=0, column=0, sticky="w")
        self._barra = ttk.Progressbar(avance, maximum=META_PROGRESO, bootstyle="info")
        self._barra.grid(row=0, column=1, sticky="ew")

    def actualizar(self, expedicion: Expedicion) -> None:
        texto, estilo = etiqueta_estado(expedicion.estado)
        self._nombre.configure(text=expedicion.nombre)
        self._dia.configure(text=etiqueta_dia(expedicion))
        self._estado.configure(text=texto, bootstyle=estilo)
        self._texto_progreso.configure(text=etiqueta_progreso(expedicion.progreso))
        self._barra.configure(value=expedicion.progreso)


# --------------------------------------------------------------------------
# Recursos
# --------------------------------------------------------------------------
class TarjetaRecurso(ttk.Frame):
    """Nombre, valor numérico y barra de un recurso."""

    def __init__(self, master: tk.Misc, etiqueta: str) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        ttk.Label(
            self, text=etiqueta, font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).grid(row=0, column=0, sticky="w")
        self._valor = ttk.Label(self, font="ZC.Valor")
        self._valor.grid(row=0, column=1, sticky="e")
        self._barra = ttk.Progressbar(self, maximum=LIMITE_MAX, bootstyle="primary")
        self._barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

    def actualizar(self, valor: int) -> None:
        self._valor.configure(text=texto_recurso(valor), foreground=color_nivel(valor))
        self._barra.configure(value=valor, bootstyle=estilo_barra(valor))


class PanelRecursos(ttk.Labelframe):
    """Agua, alimentos, energía y salud."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, text="RECURSOS", padding=10)
        self.columnconfigure(0, weight=1)
        self._tarjetas: dict[str, TarjetaRecurso] = {}
        for fila, nombre in enumerate(NOMBRES_RECURSOS):
            tarjeta = TarjetaRecurso(self, NOMBRES_VISIBLES[nombre])
            tarjeta.grid(row=fila, column=0, sticky="ew", pady=(0 if fila == 0 else 6, 0))
            self._tarjetas[nombre] = tarjeta

    def actualizar(self, recursos: Recursos) -> None:
        for nombre, tarjeta in self._tarjetas.items():
            tarjeta.actualizar(getattr(recursos, nombre))


# --------------------------------------------------------------------------
# Tripulación
# --------------------------------------------------------------------------
class PanelTripulacion(ttk.Labelframe):
    """Integrantes disponibles, clima, dificultad y consumo previsto."""

    def __init__(self, master: tk.Misc, total: int) -> None:
        super().__init__(master, text="TRIPULACIÓN", padding=10)
        self._total = total
        self.columnconfigure(1, weight=1)

        # Fila 0: etiqueta, puntos de la tripulación y cuenta, todo en una línea.
        ttk.Label(
            self, text="INTEGRANTES", font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).grid(row=0, column=0, sticky="w")
        self._puntos = ttk.Label(self, font="ZC.Titulo", foreground=PALETA["oro"])
        self._puntos.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self._cuenta = ttk.Label(self, font="ZC.Valor")
        self._cuenta.grid(row=0, column=2, sticky="e")

        ttk.Label(
            self, text="CLIMA", font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._clima = ttk.Label(self, font="ZC.Normal")
        self._clima.grid(row=1, column=1, columnspan=2, sticky="e", pady=(4, 0))

        ttk.Label(
            self, text="DIFICULTAD", font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).grid(row=2, column=0, sticky="w", pady=(4, 0))
        self._dificultad = ttk.Label(self, font="ZC.Normal")
        self._dificultad.grid(row=2, column=1, columnspan=2, sticky="e", pady=(4, 0))

        ttk.Separator(self).grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(
            self, text="CONSUMO AL CERRAR LA JORNADA", font="ZC.Etiqueta",
            foreground=PALETA["tenue"],
        ).grid(row=4, column=0, columnspan=3, sticky="w")
        self._consumo = ttk.Label(self, font="ZC.Pequena", wraplength=250, justify="left")
        self._consumo.grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 0))

    def actualizar(self, expedicion: Expedicion, consumo: Mapping[str, int]) -> None:
        sin_bajas = expedicion.integrantes == self._total
        self._cuenta.configure(
            text=f"{expedicion.integrantes}/{self._total}",
            foreground=PALETA["texto"] if sin_bajas else PALETA["naranja"],
        )
        self._puntos.configure(text=indicador_tripulacion(expedicion.integrantes, self._total))
        tormenta = expedicion.clima == "tormenta"
        self._clima.configure(
            text=texto_clima(expedicion.clima),
            foreground=PALETA["naranja"] if tormenta else PALETA["texto"],
        )
        self._dificultad.configure(text=texto_dificultad(expedicion.dificultad))
        self._consumo.configure(text=texto_consumo(consumo))


# --------------------------------------------------------------------------
# Eventos y decisiones
# --------------------------------------------------------------------------
class PanelEvento(ttk.Labelframe):
    """Muestra el evento pendiente y las decisiones disponibles."""

    def __init__(self, master: tk.Misc, on_decidir: Callable[[str], None]) -> None:
        super().__init__(master, text="EVENTO Y DECISIONES", padding=10)
        self._on_decidir = on_decidir
        self._ancho_texto = ANCHO_TEXTO_INICIAL
        self.columnconfigure(0, weight=1)

        cabecera = ttk.Frame(self)
        cabecera.grid(row=0, column=0, sticky="ew")
        self._titulo = ttk.Label(cabecera, font="ZC.Titulo")
        self._titulo.pack(side="left")
        self._aviso = ttk.Label(
            cabecera, font="ZC.Etiqueta", foreground=PALETA["naranja"], padding=(12, 0, 0, 0)
        )
        self._aviso.pack(side="left")
        self._descripcion = ttk.Label(
            self, font="ZC.Normal", justify="left", wraplength=self._ancho_texto
        )
        self._descripcion.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._opciones = ttk.Frame(self)
        self._opciones.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._opciones.columnconfigure(0, weight=1)
        self._detalles: list[ttk.Label] = []

        self.bind("<Configure>", self._ajustar_texto)
        self.mostrar(None, "")

    def _ajustar_texto(self, evento: tk.Event) -> None:
        self._ancho_texto = max(200, evento.width - 60)
        self._descripcion.configure(wraplength=self._ancho_texto)
        for detalle in self._detalles:
            detalle.configure(wraplength=self._ancho_detalle())

    def _ancho_detalle(self) -> int:
        """Ancho para el texto que acompaña a cada botón (va a su derecha)."""
        return max(120, self._ancho_texto - ANCHO_BOTON_DECISION - 16)

    def mostrar(self, evento: Evento | None, objetivo: str) -> None:
        for hijo in self._opciones.winfo_children():
            hijo.destroy()
        self._detalles.clear()
        if evento is None:
            self._aviso.configure(text="")
            self._titulo.configure(text="Sin eventos pendientes", foreground=PALETA["tenue"])
            self._descripcion.configure(
                text="El camino está tranquilo. Elige una acción para continuar: "
                "cada acción consume la jornada y puede traer un evento al amanecer."
                + (f"\n\n{objetivo}" if objetivo else "")
            )
            return

        self._aviso.configure(text="EVENTO CRÍTICO" if evento.critico else "EVENTO")
        self._titulo.configure(text=evento.titulo, foreground=PALETA["oro"])
        self._descripcion.configure(text=evento.descripcion)
        for fila, opcion in enumerate(evento.opciones):
            # Botón a la izquierda (ancho fijo) y su explicación a la derecha:
            # ocupa menos alto que apilarlos, y el alto cuenta en pantallas bajas.
            marco = ttk.Frame(self._opciones)
            marco.grid(row=fila, column=0, sticky="ew", pady=2)
            marco.columnconfigure(0, minsize=ANCHO_BOTON_DECISION)
            marco.columnconfigure(1, weight=1)
            ttk.Button(
                marco, text=opcion.etiqueta, bootstyle="primary", padding=(8, 6),
                command=partial(self._on_decidir, opcion.clave),
            ).grid(row=0, column=0, sticky="ew")
            detalle = "  ".join(filter(None, (opcion.descripcion, resumen_efecto(opcion.efecto))))
            etiqueta = ttk.Label(
                marco, text=detalle, font="ZC.Pequena", foreground=PALETA["tenue"],
                wraplength=self._ancho_detalle(), justify="left",
            )
            etiqueta.grid(row=0, column=1, sticky="w", padx=(12, 0))
            self._detalles.append(etiqueta)


# --------------------------------------------------------------------------
# Acciones del turno
# --------------------------------------------------------------------------
class PanelAcciones(ttk.Labelframe):
    """Botones de las acciones principales; se deshabilitan según las reglas."""

    def __init__(
        self,
        master: tk.Misc,
        acciones: Sequence[tuple[str, Accion]],
        on_accion: Callable[[Accion], None],
    ) -> None:
        super().__init__(master, text="ACCIONES DE LA JORNADA", padding=10)
        self._botones: dict[Accion, ttk.Button] = {}
        self._ayudas: dict[Accion, ttk.ToolTip] = {}
        columnas = 3
        for columna in range(columnas):
            self.columnconfigure(columna, weight=1, uniform="acciones")
        total = len(acciones)
        for indice, (etiqueta, accion) in enumerate(acciones):
            columna = indice % columnas
            # El último botón ocupa lo que queda de su fila (la emergencia, destacada).
            ancho = columnas - columna if indice == total - 1 else 1
            boton = ttk.Button(
                self, text=etiqueta, bootstyle=estilo_boton_accion(accion), padding=(6, 5),
                command=partial(on_accion, accion),
            )
            boton.grid(
                row=indice // columnas, column=columna, columnspan=ancho,
                sticky="ew", padx=3, pady=3,
            )
            self._botones[accion] = boton
            self._ayudas[accion] = ttk.ToolTip(boton, text=etiqueta, wraplength=320)

    def actualizar(
        self, motivos: Mapping[Accion, str | None], descripciones: Mapping[Accion, str]
    ) -> None:
        """``motivos[accion]`` es ``None`` si está disponible, o la razón si no."""
        for accion, boton in self._botones.items():
            motivo = motivos[accion]
            boton.configure(state="normal" if motivo is None else "disabled")
            self._ayudas[accion].configure(text=motivo or descripciones[accion])


# --------------------------------------------------------------------------
# Historial
# --------------------------------------------------------------------------
class PanelHistorial(ttk.Labelframe):
    """Historial de la expedición con filtros funcionales."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, text="HISTORIAL", padding=14)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._historial: tuple[Registro, ...] = ()

        barra = ttk.Frame(self)
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        barra.columnconfigure(1, weight=1)
        ttk.Label(
            barra, text="FILTRO", font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).grid(row=0, column=0, padx=(0, 8))
        self._filtro = tk.StringVar(value="Todo")
        selector = ttk.Combobox(
            barra, textvariable=self._filtro, values=tuple(CRITERIOS_HISTORIAL),
            state="readonly",
        )
        selector.grid(row=0, column=1, sticky="ew")
        selector.bind("<<ComboboxSelected>>", lambda _evento: self._dibujar())
        self._contador = ttk.Label(barra, font="ZC.Pequena", foreground=PALETA["tenue"])
        self._contador.grid(row=0, column=2, padx=(8, 0))

        self._texto = tk.Text(
            self, wrap="word", width=1, height=1, state="disabled", relief="flat",
            borderwidth=0, highlightthickness=0, padx=10, pady=8, font="ZC.Pequena",
            cursor="arrow",
            background=PALETA["campo"], foreground=PALETA["texto"],
            selectbackground="#2A3144", spacing1=2, spacing3=4,
        )
        self._texto.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self._texto.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self._texto.configure(yscrollcommand=scroll.set)

        estilos = {
            "accion": {"foreground": PALETA["texto"]},
            "evento": {"foreground": PALETA["naranja"]},
            "decision": {"foreground": PALETA["oro_claro"]},
            "turno": {"foreground": PALETA["tenue"]},
            "sistema": {"foreground": PALETA["oro"], "font": ("TkDefaultFont", 9, "bold")},
            "critico": {"foreground": PALETA["rojo"]},
        }
        for nombre, opciones in estilos.items():
            self._texto.tag_configure(nombre, lmargin2=22, **opciones)

    def mostrar(self, historial: tuple[Registro, ...]) -> None:
        self._historial = historial
        self._dibujar()

    def _dibujar(self) -> None:
        visibles = aplicar_filtro(self._filtro.get(), self._historial)
        self._texto.configure(state="normal")
        self._texto.delete("1.0", "end")
        for registro in visibles:
            self._texto.insert("end", formatear_registro(registro) + "\n", etiqueta_tag(registro))
        self._texto.configure(state="disabled")
        self._texto.see("end")
        self._contador.configure(text=f"{len(visibles)}/{len(self._historial)}")


# --------------------------------------------------------------------------
# Mensajes y controles
# --------------------------------------------------------------------------
class BarraMensaje(ttk.Frame):
    """Franja de mensajes de confirmación, advertencia y error.

    Tiene altura fija para dos líneas: los mensajes largos se ajustan al ancho
    sin que el resto de la ventana cambie de tamaño.
    """

    ESTILOS = {
        "info": "@secondary",
        "success": "@success",
        "warning": "@warning",
        "error": "@danger",
    }

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, height=52)
        self.pack_propagate(False)
        self._etiqueta = ttk.Label(self, font="ZC.Normal", padding=(14, 6), anchor="w")
        self._etiqueta.pack(fill="both", expand=True)
        self.bind("<Configure>", self._ajustar)
        self.mostrar("Listo para partir. Elige una acción para comenzar.", "info")

    def _ajustar(self, evento: tk.Event) -> None:
        self._etiqueta.configure(wraplength=max(200, evento.width - 32))

    def mostrar(self, texto: str, nivel: str = "info") -> None:
        self._etiqueta.configure(
            text=texto, bootstyle=self.ESTILOS.get(nivel, self.ESTILOS["info"])
        )


class PanelControles(ttk.Frame):
    """Nueva expedición, exportar reporte y dificultad de la próxima partida."""

    def __init__(
        self,
        master: tk.Misc,
        on_reiniciar: Callable[[], None],
        on_exportar: Callable[[], None],
    ) -> None:
        super().__init__(master)
        ttk.Label(
            self, text="PRÓXIMA DIFICULTAD", font="ZC.Etiqueta", foreground=PALETA["tenue"]
        ).grid(row=0, column=0, padx=(0, 8))
        self._dificultad = tk.StringVar(value="Normal")
        ttk.Combobox(
            self, textvariable=self._dificultad, values=tuple(DIFICULTADES_UI),
            state="readonly", width=9,
        ).grid(row=0, column=1, padx=(0, 16))
        ttk.Button(
            self, text="Exportar reporte", bootstyle="info-outline", command=on_exportar
        ).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(
            self, text="Nueva expedición", bootstyle="danger", command=on_reiniciar
        ).grid(row=0, column=3)

    def dificultad_elegida(self) -> str:
        return DIFICULTADES_UI.get(self._dificultad.get(), "normal")
