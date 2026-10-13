#Punto de entrada de Expedición: Zona Cero.

#Uso (desde la carpeta del proyecto):

    #python main.py


from __future__ import annotations

import sys


def main() -> int:
    try:
        from ui.main_window import VentanaPrincipal
    except ModuleNotFoundError as error:
        if error.name == "tkinter":
            print("Esta instalación de Python no incluye Tkinter.", file=sys.stderr)
            print("Reinstala Python y marca la opción «tcl/tk and IDLE».", file=sys.stderr)
        else:
            # Normalmente ttkbootstrap: se explica cómo instalarlo.
            print(f"Falta una dependencia: {error.name}.", file=sys.stderr)
            print("Instálala con:  python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    VentanaPrincipal().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
