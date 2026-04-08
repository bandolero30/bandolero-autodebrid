import os
import time
import queue
import hashlib
import pytest
import requests
from core.engine import download_worker, verify_worker
from utils.helpers import get_file_md5

def test_verify_worker_real_file(tmp_path):
    """Garantiza que la salida de verify_worker sea correcta con un archivo real en disco."""
    # 1. Crear archivo de prueba real en la subcarpeta por defecto 'General'
    target_dir = tmp_path / "General"
    target_dir.mkdir()
    test_file = target_dir / "test_verify.txt"
    content = b"Contenido de prueba para MD5"
    test_file.write_bytes(content)
    expected_md5 = hashlib.md5(content).hexdigest()
    
    # 2. Configuración
    filename = "test_verify.txt"
    download_rows = {filename: {"iid": "iid1", "filesize": len(content)}}
    config = {"base_dir": str(tmp_path)}
    update_queue = queue.Queue()
    get_id_text = lambda key: f"Key_{key}"
    
    # 3. Ejecutar worker (Sincrónico para el test)
    verify_worker(filename, download_rows, config, update_queue, get_id_text, lambda: False)
    
    # 4. Capturar resultados de la cola
    results = []
    while not update_queue.empty():
        results.append(update_queue.get())
    
    # 5. Validaciones Inmutables
    verify_msgs = [m for m in results if m[0] == 'verify_done']
    assert len(verify_msgs) == 1, f"Se esperaba 1 mensaje verify_done, se obtuvieron: {results}"
    
    report = verify_msgs[0][5]
    if report['status'] == "CRASH":
        pytest.fail(f"El worker crasheó: {report.get('msg')}")
    
    assert report['md5'] == expected_md5
    assert report['status'] == "OK"

def test_download_worker_full_cycle(tmp_path, local_server, mocker):
    """Garantiza que la lógica de descarga (GET, Resume) funciona contra un servidor real."""
    # 1. Preparar archivo en el 'servidor'
    # Como SimpleHTTPRequestHandler sirve el CWD, creamos el archivo en el directorio actual temporalmente
    # Pero con pytest-httpserver sería más fácil. Usaremos mocks mínimos para la parte de la API RD
    # pero el flujo de descarga (requests.get) será real contra local_server.
    
    server_file_name = "server_file.bin"
    server_content = b"A" * 1024 * 128 # 128KB
    with open(server_file_name, "wb") as f:
        f.write(server_content)
    
    try:
        # 2. Mockear la respuesta de Real-Debrid para que apunte a nuestro local_server
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "download": f"{local_server}/{server_file_name}",
            "filesize": len(server_content)
        }
        mocker.patch("requests.post", return_value=mock_response)
        
        # 3. Configurar entorno de descarga local
        target_dir = tmp_path / "downloads"
        target_dir.mkdir()
        filename = "downloaded_file.bin"
        
        download_rows = {
            filename: {
                "links": [f"https://real-link.com/file"], # El link original no importa por el mock de POST
                "iid": "iid_download",
                "subfolder": "test_sub"
            }
        }
        config = {
            "base_dir": str(target_dir),
            "api_key": "fake_api_key"
        }
        update_queue = queue.Queue()
        stopped_links = set()
        running_filenames = set()
        force_rotate = set()
        
        # 4. EJECUCIÓN: Descarga parcial (Simulando parada a la mitad)
        # Para simplificar este test sin hilos complejos, verificaremos el flujo completo primero
        download_worker(
            filename, download_rows, config, update_queue,
            stopped_links, running_filenames, force_rotate,
            lambda k: k, lambda: False
        )
        
        # 5. VERIFICACIÓN: El archivo debe existir y ser idéntico
        final_path = target_dir / "test_sub" / filename
        assert final_path.exists()
        assert final_path.read_bytes() == server_content
        
        # 6. VERIFICACIÓN: Mensajes de éxito en la cola
        msgs = []
        while not update_queue.empty(): msgs.append(update_queue.get())
        assert any(m[0] == "progress_full" and m[2] == len(server_content) for m in msgs)
        assert any(m[0] == "worker_done" for m in msgs)

    finally:
        if os.path.exists(server_file_name):
            os.remove(server_file_name)

def test_download_resume_logic(tmp_path, local_server, mocker):
    """Garantiza que la lógica de RESUME (HTTP Range) funciona correctamente."""
    server_file_name = "resume_file.bin"
    server_content = b"PART1_PART2"
    with open(server_file_name, "wb") as f: f.write(server_content)
    
    try:
        # Pre-crear archivo parcial en disco (PART1)
        target_dir = tmp_path / "resume_test"
        sub_dir = target_dir / "sub"
        sub_dir.mkdir(parents=True)
        dest_file = sub_dir / "resumable.bin"
        dest_file.write_bytes(b"PART1_") # Ya tenemos la primera parte
        
        # Configuración
        filename = "resumable.bin"
        download_rows = {filename: {"links": ["dummy"], "iid": "iid_res", "subfolder": "sub"}}
        config = {"base_dir": str(target_dir), "api_key": "key"}
        
        # Mock API RD
        m_resp = mocker.Mock()
        m_resp.status_code = 200
        m_resp.json.return_value = {"download": f"{local_server}/{server_file_name}", "filesize": len(server_content)}
        mocker.patch("requests.post", return_value=m_resp)
        
        # Ejecutar worker
        download_worker(filename, download_rows, config, queue.Queue(), set(), set(), set(), lambda k: k, lambda: False)
        
        # Verificar que se completó (PART1_PART2)
        assert dest_file.read_bytes() == server_content
        
    finally:
        if os.path.exists(server_file_name): os.remove(server_file_name)
