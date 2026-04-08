import os
import sys
import json
import customtkinter as ctk
import ctypes
from utils.helpers import resource_path, obfuscate_api_key, deobfuscate_api_key


# CONFIGURACIÓN DE VERSIÓN GLOBAL (v1.1.20260408 Modular)
__version__ = "1.1.20260408"

# Determinar ruta base absoluta para evitar fallos de ubicación en Windows/Modular
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Si core/config.py está en j:\ws\descarga_elamigo\core\config.py, subimos un nivel
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_PATH, "config.json")
SESSION_FILE = os.path.join(BASE_PATH, "session.json")

# 🎨 Sistema de Carga de Fuentes Montserrat (v1.1.20260401 Modular)
def _load_global_fonts():
    """Registra Montserrat en el sistema y en CTK para disponibilidad inmediata."""
    fonts_to_load = [
        resource_path("fonts/Montserrat-Regular.ttf"),
        resource_path("fonts/Montserrat-Bold.ttf")
    ]
    for fpath in fonts_to_load:
        if os.path.exists(fpath):
            # 1. Registro en CustomTkinter
            ctk.FontManager.load_font(fpath)
            # 2. Registro en Windows GDI (API nativa) para fallback infalible
            if sys.platform == "win32":
                ctypes.windll.gdi32.AddFontResourceExW(fpath, 0x10, 0)
    print("[DEBUG] Fuentes Montserrat cargadas al núcleo.")

# Ejecutar carga inmediatamente al importar este módulo base
_load_global_fonts()

FONT_FAMILY = "Montserrat"
FONT_FALLBACK = ("Montserrat", "Microsoft YaHei", "SimSun", "Segoe UI")


DEFAULT_CONFIG = {
    "api_key": "",
    "base_dir": r"T:\Descargas",
    "max_workers": 3,
    "auto_retry": True,
    "font_size": 13,
    "tree_font_size": 14,
    "retry_delay": 10,
    "language": "es",
    "f95_user": "",
    "f95_pass": ""
}

def load_config():
    """Carga y desofusca la configuración desde disco."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                # Desofuscar API Key si existe (Seguridad Windows v22.0)
                if "api_key" in data:
                    data["api_key"] = deobfuscate_api_key(data["api_key"])
                if "f95_user" in data:
                    data["f95_user"] = deobfuscate_api_key(data["f95_user"])
                if "f95_pass" in data:
                    data["f95_pass"] = deobfuscate_api_key(data["f95_pass"])
                config.update(data)
        except Exception as e:
            print(f"Error cargando configuración modular: {e}")
    return config

def save_config(config_dict):
    """Ofusca y guarda la configuración en disco."""
    temp_config = config_dict.copy()
    if "api_key" in temp_config:
        temp_config["api_key"] = obfuscate_api_key(temp_config["api_key"])
    if "f95_user" in temp_config:
        temp_config["f95_user"] = obfuscate_api_key(temp_config["f95_user"])
    if "f95_pass" in temp_config:
        temp_config["f95_pass"] = obfuscate_api_key(temp_config["f95_pass"])
    
    try:
        print(f"[DEBUG] Guardando configuración en: {CONFIG_FILE}")
        with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
            json.dump(temp_config, f, indent=4)
        print(f"[DEBUG] Contenido guardado con éxito (API Key ofuscada)")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo escribir en {CONFIG_FILE}: {e}")
        return False
