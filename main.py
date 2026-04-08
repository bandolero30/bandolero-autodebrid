import sys
import customtkinter as ctk
from ui.main_window import DownloaderApp

def main():
    """Punto de entrada simplificado con Splash Screen integrado (v1.1.20260406)."""

    # 1. Configuración global de apariencia
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # 2. Inicialización de la aplicación principal
    # El Splash Screen nativo de PyInstaller se gestiona ahora internamente en DownloaderApp
    app = DownloaderApp()
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.on_closing()

if __name__ == "__main__":
    main()

