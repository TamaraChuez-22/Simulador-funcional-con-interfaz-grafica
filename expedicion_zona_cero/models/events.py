#Capa de datos: efectos, opciones, eventos y acciones.

#Todas las estructuras son ``dataclass(frozen=True)``: una vez creadas no se
#pueden modificar. Las colecciones se guardan como ``tuple`` (y no como
#``list``) porque congelar una dataclass solo protege el primer nivel: una
#lista dentro de ella seguiría siendo mutable.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Efecto:

    agua: int = 0
    alimentos: int = 0
    energia: int = 0
    salud: int = 0
    progreso: int = 0
    integrantes: int = 0
    clima: str | None = None


@dataclass(frozen=True)
class Opcion:

    clave: str
    etiqueta: str
    efecto: Efecto
    descripcion: str = ""


@dataclass(frozen=True)
class Evento:

    tipo: str
    titulo: str
    descripcion: str
    opciones: tuple[Opcion, ...]
    critico: bool = False


@dataclass(frozen=True)
class Accion:

    tipo: str
    parametro: str | None = None


# Reglas de azar de los eventos (el azar real lo genera la capa de servicio;
# aquí solo viven los umbrales).

PROBABILIDAD_EVENTO = 0.75      # probabilidad de que un día traiga un evento
PROBABILIDAD_ACCIDENTE = 0.40   # riesgo de la ruta corta en la zona peligrosa
EFECTO_ACCIDENTE = Efecto(salud=-25, energia=-10)



# Catálogo de eventos

CATALOGO_EVENTOS: tuple[Evento, ...] = (
    Evento(
        tipo="tormenta",
        titulo="Tormenta eléctrica",
        descripcion=(
            "El cielo se cierra y empiezan a caer rayos cerca del campamento. "
            "Avanzar bajo la tormenta rinde, pero dispara el consumo del día."
        ),
        opciones=(
            Opcion(
                "refugiarse", "Refugiarse y esperar",
                Efecto(alimentos=-4, agua=-2),
                "Pierdes tiempo, pero el consumo del día no aumenta.",
            ),
            Opcion(
                "avanzar", "Avanzar bajo la tormenta",
                Efecto(progreso=6, energia=-8),
                "Ganas terreno, pero el consumo del día se multiplica.",
            ),
        ),
    ),
    Evento(
        tipo="provisiones",
        titulo="Hallazgo de provisiones",
        descripcion=(
            "Entre los escombros de un campamento abandonado hay cajas "
            "selladas con agua y comida. Cargarlas cansa al equipo."
        ),
        opciones=(
            Opcion(
                "tomar_todo", "Cargar todo",
                Efecto(agua=20, alimentos=20, energia=-8),
                "Mucho botín, mucho cansancio.",
            ),
            Opcion(
                "solo_agua", "Llevar solo agua",
                Efecto(agua=25, energia=-3),
            ),
            Opcion(
                "solo_comida", "Llevar solo comida",
                Efecto(alimentos=25, energia=-3),
            ),
        ),
    ),
    Evento(
        tipo="averia",
        titulo="Avería del equipo",
        descripcion=(
            "El generador portátil falla y los equipos de navegación se "
            "apagan. Hay que decidir cómo responder."
        ),
        opciones=(
            Opcion(
                "reparar", "Repararlo con calma",
                Efecto(energia=-15),
                "Cuesta energía, pero queda bien.",
            ),
            Opcion(
                "improvisar", "Improvisar una reparación",
                Efecto(energia=-5, salud=-10),
                "Rápido, pero alguien se lastima con los cables.",
            ),
            Opcion(
                "abandonar", "Abandonar el equipo",
                Efecto(agua=-10, alimentos=-10),
                "Se pierden suministros que viajaban en el generador.",
            ),
        ),
        critico=True,
    ),
    Evento(
        tipo="zona_peligrosa",
        titulo="Zona peligrosa",
        descripcion=(
            "El camino se bifurca: la ruta corta cruza un terreno inestable "
            "y la ruta larga rodea la zona con seguridad."
        ),
        opciones=(
            Opcion(
                "ruta_corta", "Tomar la ruta corta",
                Efecto(progreso=18, energia=-5),
                "Gran avance, pero hay riesgo de accidente.",
            ),
            Opcion(
                "ruta_larga", "Tomar la ruta larga",
                Efecto(progreso=8, agua=-6, alimentos=-4),
                "Avance moderado, sin riesgo.",
            ),
        ),
        critico=True,
    ),
    Evento(
        tipo="descanso",
        titulo="Refugio tranquilo",
        descripcion=(
            "El equipo encuentra una cueva seca y protegida. Es un buen "
            "lugar para recuperar fuerzas."
        ),
        opciones=(
            Opcion(
                "acampar", "Acampar un rato",
                Efecto(energia=20, alimentos=-3),
            ),
            Opcion(
                "seguir", "Seguir adelante",
                Efecto(progreso=4, energia=-4),
            ),
        ),
    ),
    Evento(
        tipo="emergencia",
        titulo="Emergencia médica",
        descripcion=(
            "Un integrante se desploma con fiebre alta. Si no se le atiende "
            "ahora, la expedición podría perderlo."
        ),
        opciones=(
            Opcion(
                "atender", "Atenderlo con los suministros",
                Efecto(agua=-10, alimentos=-6, salud=15),
                "Gasta recursos, pero salva al integrante.",
            ),
            Opcion(
                "ignorar", "Seguir sin atenderlo",
                Efecto(salud=-15),
                "No gastas recursos, pero pierdes a un integrante.",
            ),
        ),
        critico=True,
    ),
)
