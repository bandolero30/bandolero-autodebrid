import os
import json
import pytest
import threading
import inspect
from unittest.mock import MagicMock
from ui.main_window import DownloaderApp
from ui.mixins.ui_mixin import UIMixin
from ui.mixins.download_mixin import DownloadMixin
from utils.helpers import format_size, obfuscate_api_key, deobfuscate_api_key, detect_file_type
from core.engine import download_worker, verify_worker, extract_multi_dlc_worker

@pytest.fixture
def mock_app():
    # Usamos una estructura de datos real para atributos críticos
    class MockApp(UIMixin, DownloadMixin):
        def __init__(self):
            self.iid_to_link = {}
            self.download_rows = {}
            self.pending_queue = []
            self.running_filenames = set()
            self.stopped_links = set()
            self.force_rotate = set()
            self.active_speeds = {}
            self.config = {"base_dir": "C:/Tests", "language": "es", "max_workers": 2, "api_key": "dummy_key"}
            self.is_downloading = False
            self.stop_requested = False
            self.active_downloads_count = 0
            self.logs_dict = {}
            self.sz = 12
            self.chk_all_state = True
            
            self.tree = MagicMock()
            self.update_queue = MagicMock()
            self.var_subfolder = MagicMock()
            self.var_subfolder.get.return_value = "TestSub"
            self.var_language = MagicMock()
            self.var_language.get.return_value = "es"
            self.dlc_path = MagicMock()
            self._selected_dlc_paths = ["file1.dlc"]
            self.session_file = "session.json"
            
            # Tkinter/CustomTkinter
            self.after = MagicMock()
            self.clipboard_clear = MagicMock()
            self.clipboard_append = MagicMock()
            self.btn_load = MagicMock()
            self.active_context_menu = None
            
            # Mocks de lógica interna
            self._update_action_buttons_ui = MagicMock()
            self._update_status_bar_ui = MagicMock()
            self.get_id_text = MagicMock(side_effect=lambda key: f"Translated_{key}")

        def save_session(self): pass
        def refresh_console(self, filename): pass

    return MockApp()

def test_worker_signature_consistency(mock_app, mocker):
    """
    PRUEBA CRÍTICA DE INTEGRACIÓN:
    Verifica que las llamadas desde los Mixins coinciden con las firmas de los Workers en Engine.
    Esto evita el error de 'missing positional arguments' que rompió la aplicación.
    """
    # 1. Test Download Worker Signature
    mock_app.download_rows = {"file1.txt": {"checked": True, "links": ["L1"], "iid": "iid1"}}
    spy_thread = mocker.patch("threading.Thread")
    mock_app.start_downloads()
    
    # Capturar la llamada a Thread(target=download_worker, args=(...))
    args, kwargs = spy_thread.call_args
    target_func = kwargs.get('target') or args[0]
    provided_args = kwargs.get('args') or args[1]
    
    assert target_func == download_worker
    # Validar que el número de argumentos coincide con la firma real
    real_sig = inspect.signature(download_worker)
    assert len(provided_args) == len(real_sig.parameters), f"Firma de download_worker incorrecta: enviamos {len(provided_args)} pero espera {len(real_sig.parameters)}"

    # 2. Test Verify Worker Signature
    spy_thread.reset_mock()
    mock_app.tree.selection.return_value = ["iid1"]
    mock_app.iid_to_link["iid1"] = "file1.txt"
    mock_app.verify_selected_file()
    
    args, kwargs = spy_thread.call_args
    target_func = kwargs.get('target') or args[0]
    provided_args = kwargs.get('args') or args[1]
    
    assert target_func == verify_worker
    real_sig = inspect.signature(verify_worker)
    assert len(provided_args) == len(real_sig.parameters), f"Firma de verify_worker incorrecta: enviamos {len(provided_args)} pero espera {len(real_sig.parameters)}"

    # 3. Test Extract DLC Worker Signature
    spy_thread.reset_mock()
    mock_app.load_dlc_links()
    
    args, kwargs = spy_thread.call_args
    target_func = kwargs.get('target') or args[0]
    provided_args = kwargs.get('args') or args[1]
    
    assert target_func == extract_multi_dlc_worker
    real_sig = inspect.signature(extract_multi_dlc_worker)
    assert len(provided_args) == len(real_sig.parameters), f"Firma de extract_multi_dlc_worker incorrecta: enviamos {len(provided_args)} pero espera {len(real_sig.parameters)}"

def test_remove_selected_link(mock_app):
    mock_app.tree.selection.return_value = ["iid1"]
    mock_app.iid_to_link["iid1"] = "file1.txt"
    mock_app.download_rows["file1.txt"] = {"iid": "iid1"}
    mock_app.tree.exists.return_value = True
    
    mock_app.remove_selected_link()
    
    assert "file1.txt" not in mock_app.download_rows
    assert "iid1" not in mock_app.iid_to_link
    mock_app.tree.delete.assert_called_once_with("iid1")

def test_rotate_selected_link(mock_app):
    mock_app.tree.selection.return_value = ["iid1"]
    mock_app.iid_to_link["iid1"] = "file1.txt"
    # Necesita al menos 2 enlaces para rotar
    mock_app.download_rows["file1.txt"] = {"links": ["L1", "L2"], "iid": "iid1"}
    
    mock_app.rotate_selected_link()
    
    assert "file1.txt" in mock_app.force_rotate
    mock_app.tree.set.assert_called() # Verifica que actualiza el estado a 'Rotating'

def test_verify_worker_logic(mock_app, mocker):
    """Verifica que el motor de integridad no falla si el tamaño remoto es 0."""
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.getsize", return_value=100)
    mocker.patch("time.sleep")
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"0" * 100))
    mocker.patch("mimetypes.guess_type", return_value=("plain/text", None))
    
    download_rows = {"file1.txt": {"iid": "iid1", "filesize": 0}}
    config = {"base_dir": "C:/Tests"}
    update_queue = MagicMock()
    get_id_text = lambda key: f"Trans_{key}"
    
    # Ejecutamos el motor directamente
    verify_worker("file1.txt", download_rows, config, update_queue, get_id_text, lambda: False)
    
    # Verificar mensajes en la cola
    args = update_queue.put.call_args_list
    msg_types = [a[0][0][0] for a in args]
    assert 'verify_done' in msg_types
