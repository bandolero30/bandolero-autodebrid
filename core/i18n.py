import os
import json
from utils.helpers import resource_path

class Translator:
    """Clase singleton para la gestión de internacionalización (v22.0)."""
    _instance = None
    _lang_data = {}
    _current_lang = "es"

    @classmethod
    def initialize(cls):
        """Carga recursivamente todos los idiomas de la carpeta locales."""
        cls._lang_data = {}
        locales_path = resource_path("locales")
        
        if not os.path.exists(locales_path):
            os.makedirs(locales_path, exist_ok=True)
            
        for filename in os.listdir(locales_path):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                try:
                    with open(os.path.join(locales_path, filename), "r", encoding="utf-8") as f:
                        cls._lang_data[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error cargando idioma {lang_code}: {e}")
        
        # Garantía mínima de existencia de datos
        if not cls._lang_data:
            cls._lang_data = {"es": {"_lang_name": "Español (Sistema)"}}

    @classmethod
    def set_language(cls, lang_code):
        """Cambia el idioma activo del motor de traducción."""
        if lang_code in cls._lang_data:
            cls._current_lang = lang_code
            return True
        return False

    @classmethod
    def get(cls, key):
        """Obtiene una traducción por su clave. Devuelve la clave si no existe."""
        lang_dict = cls._lang_data.get(cls._current_lang, {})
        # Buscar en el idioma actual, si no existe probar en 'es' (fallback), si no devolver key.
        val = lang_dict.get(key)
        if val is None:
            val = cls._lang_data.get("es", {}).get(key, key)
        return val

    @classmethod
    def get_supported_languages(cls):
        """Devuelve un diccionario de código -> nombre_idioma."""
        return {code: data.get("_lang_name", code) for code, data in cls._lang_data.items()}

    @classmethod
    def get_current_lang(cls):
        """Devuelve el código del idioma actual."""
        return cls._current_lang

# Inicialización automática al cargar el módulo core
Translator.initialize()
