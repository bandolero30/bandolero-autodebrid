import sys
import pytest
import threading
import http.server
import socketserver
from unittest.mock import MagicMock

# Mocking GUI dependencies to allow importing app_gui without side effects
class MockCTk(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def title(self, *args): pass
    def geometry(self, *args): pass
    def protocol(self, *args): pass
    def after(self, *args): pass
    def grid_columnconfigure(self, *args, **kwargs): pass
    def grid_rowconfigure(self, *args, **kwargs): pass

mock_ctk = MockCTk()
mock_ctk.CTk = MockCTk
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()
mock_ctk.FontManager = MagicMock()
mock_ctk.CTkFrame = MagicMock
mock_ctk.CTkTabview = MagicMock
mock_ctk.CTkLabel = MagicMock
mock_ctk.CTkButton = MagicMock
mock_ctk.CTkEntry = MagicMock
mock_ctk.CTkSlider = MagicMock
mock_ctk.CTkCheckBox = MagicMock
mock_ctk.CTkTextbox = MagicMock
mock_ctk.CTkScrollbar = MagicMock
mock_ctk.CTkFont = MagicMock

mock_tk = MagicMock()
mock_pil = MagicMock()

sys.modules["customtkinter"] = mock_ctk
sys.modules["tkinter"] = mock_tk
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ImageTk"] = MagicMock()
sys.modules["PIL.ImageDraw"] = MagicMock()
sys.modules["PIL.ImageFont"] = MagicMock()

# Mocking win32crypt since it might not be available in all test environments
mock_win32 = MagicMock()
mock_win32.CryptProtectData.return_value = b"encrypted_with_dpapi"
mock_win32.CryptUnprotectData.return_value = (None, b"decrypted_with_dpapi")
sys.modules["win32crypt"] = mock_win32

@pytest.fixture(scope="session")
def local_server():
    """Servidor HTTP real para pruebas de descarga inmutables."""
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    class SilentServer(socketserver.TCPServer):
        allow_reuse_address = True

    httpd = SilentServer(("", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{PORT}"
    httpd.shutdown()
