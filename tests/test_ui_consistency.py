import pytest
from ui.main_window import DownloaderApp

def test_app_consistency_methods():
    """
    Este test asegura que la clase DownloaderApp (v1.1.20260401) contenga todos los métodos
    requeridos por sus componentes modulares. 
    Usamos inspección de clase para evitar instanciar la GUI en el entorno de tests.
    """
    # Obtenemos todos los atributos disponibles en la clase (incluyendo mixins)
    class_members = dir(DownloaderApp)
    
    # Lista de métodos críticos que los componentes llaman vía self.app
    required_methods = [
        "get_id_text",
        "browse_dlc",
        "load_dlc_links",
        "start_all_downloads",
        "start_selected_downloads",
        "stop_downloads",
        "stop_selected_downloads",
        "toggle_console",
        "show_context_menu",
        "on_tree_click",
        "on_click_save_config", # El que faltaba
        "browse_base_dir",     # El que originó el crash
        "apply_folder_to_selected",
        "_on_lang_change",
        "_sort_column",
        "_on_tree_select",
        "_on_tree_motion",
        "_hide_file_tooltip"
    ]
    
    for method in required_methods:
        assert method in class_members, f"CRITICAL: DownloaderApp no implementa '{method}', requerido por componentes UI."

def test_app_inheritance_integrity():
    """Verifica que DownloaderApp herede de todos los Mixins necesarios."""
    from ui.mixins.persistence_mixin import PersistenceMixin
    from ui.mixins.download_mixin import DownloadMixin
    from ui.mixins.ui_mixin import UIMixin
    
    assert issubclass(DownloaderApp, PersistenceMixin)
    assert issubclass(DownloaderApp, DownloadMixin)
    assert issubclass(DownloaderApp, UIMixin)
