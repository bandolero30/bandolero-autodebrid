import os
import json

def save_session(session_file, session_data):
    """Guarda los datos de sesión serializados en disco (v22.0)."""
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error guardando sesión persistente: {e}")
        return False

def load_session(session_file):
    """Carga los datos de sesión desde disco si el archivo existe."""
    if not os.path.exists(session_file):
        return None
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando sesión persistente: {e}")
        return None
