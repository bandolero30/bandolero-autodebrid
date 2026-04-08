import os
import hashlib
import pytest
from utils.helpers import resource_path, get_file_md5, detect_file_type

def test_resource_path():
    # Test that it returns an absolute path
    path = resource_path("test.txt")
    assert os.path.isabs(path)

def test_get_file_md5(tmp_path):
    # Create a temporary file with known content
    content = b"Bandolero Test MD5"
    expected_md5 = hashlib.md5(content).hexdigest()
    
    file_p = tmp_path / "test_file.bin"
    file_p.write_bytes(content)
    
    result = get_file_md5(str(file_p))
    assert result == expected_md5

def test_get_file_md5_error():
    # Test error handling with non-existent file
    result = get_file_md5("non_existent_file_path_12345.bin")
    assert result == "Error calculando MD5"

def test_detect_file_type_rar(tmp_path):
    # RAR header: Rar!\x1a\x07
    file_p = tmp_path / "test.rar"
    file_p.write_bytes(b"Rar!\x1a\x07rest_of_file")
    
    mime, desc = detect_file_type(str(file_p))
    assert mime == "Archivo RAR"
    assert "Rar Signature" in desc

def test_detect_file_type_zip(tmp_path):
    # ZIP header: PK\x03\x04
    file_p = tmp_path / "test.zip"
    file_p.write_bytes(b"PK\x03\x04rest_of_file")
    
    mime, desc = detect_file_type(str(file_p))
    assert mime == "Archivo ZIP / Office"
    assert "Standard PK Header" in desc

def test_detect_file_type_unknown(tmp_path):
    file_p = tmp_path / "test.txt"
    file_p.write_bytes(b"Hello World")
    
    mime, desc = detect_file_type(str(file_p))
    assert mime == "Binario Desconocido"
