import os
import sys
import hashlib
import base64
import re
import urllib.parse
import cloudscraper
import requests
from bs4 import BeautifulSoup
try:
    import win32crypt
except (ImportError, Exception):
    try:
        from win32 import win32crypt
    except (ImportError, Exception):
        win32crypt = None

def resource_path(relative_path):
    """Obtiene la ruta absoluta para recursos, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_file_md5(file_path):
    """Calcula el hash MD5 de un archivo en bloques para ahorrar memoria."""
    if not os.path.exists(file_path): return "Error calculando MD5"
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return "Error calculando MD5"

def detect_file_type(file_path):
    """Detecta el tipo MIME y una descripción básica del archivo."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".7z": mime = "Archivo 7-Zip"
    elif ext == ".rar": mime = "Archivo RAR"
    elif ext == ".zip": mime = "Archivo ZIP / Office"
    elif ext == ".txt": mime = "Binario Desconocido"
    else:
        import mimetypes
        mime, _ = mimetypes.guess_type(file_path)
        if not mime: mime = "Binario Desconocido"
    
    desc = "Binario Desconocido"
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                head = f.read(10)
                if head.startswith(b"Rar!"): 
                    desc = "Archivo RAR (Rar Signature)"
                elif head.startswith(b"PK"): 
                    desc = "Archivo ZIP (Standard PK Header)"
                elif head.startswith(b"7z"): 
                    desc = "Archivo 7z"
                else:
                    if "compressed" in mime.lower() or "Zip" in mime: desc = "Archivo Comprimido"
                    elif "text" in mime.lower(): desc = "Documento de Texto"
                    elif "image" in mime.lower(): desc = "Imagen"
                    else: desc = "Archivo de Datos"
    except: pass
    
    return mime, desc

def format_size(bytes_val):
    """Formatea bytes a una cadena legible (KB, MB, GB...)."""
    try:
        bytes_val = float(bytes_val)
    except:
        return "0.00 B"
        
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:3.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:3.2f} PB"

def obfuscate_api_key(text):
    """Cifrado profesional mediante Windows DPAPI con Fallback XOR."""
    if not text: return ""
    try:
        if win32crypt:
            crypted_data = win32crypt.CryptProtectData(text.encode(), "BandoDL", None, None, None, 0)
            return base64.b64encode(crypted_data).decode()
        else:
            key = "BANDO_KEY_2024"
            xor_res = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
            return base64.b64encode(xor_res.encode()).decode()
    except Exception:
        return text

def deobfuscate_api_key(crypted):
    """Descifrado robusto con detección de formato."""
    if not crypted: return ""
    if win32crypt:
        try:
            decoded_bin = base64.b64decode(crypted)
            descr_data = win32crypt.CryptUnprotectData(decoded_bin, None, None, None, 0)
            return descr_data[1].decode()
        except:
            pass 
    try:
        key = "BANDO_KEY_2024"
        decoded_bin = base64.b64decode(crypted)
        try:
            decoded_str = decoded_bin.decode()
            res = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(decoded_str))
            if all(c.isalnum() or c in ".-_" for c in res[:5]):
                return res
        except:
            pass
    except:
        pass
    if isinstance(crypted, str) and crypted.startswith("mock_"):
        return crypted.replace("mock_", "")
    return crypted

def get_clean_name(link):
    """Extrae el nombre del archivo de un enlace."""
    match = re.search(r'([A-Za-z0-9_.-]+\.part[0-9]+\.rar|[A-Za-z0-9_.-]+\.rar|[A-Za-z0-9_.-]+\.iso)', link, re.IGNORECASE)
    if match: return match.group(1)
    parsed = urllib.parse.urlparse(link)
    base = os.path.basename(parsed.path)
    if ".html" in base: base = base.replace(".html", "")
    if ".htm" in base: base = base.replace(".htm", "")
    return base

def detect_common_pattern(filenames):
    """Analiza nombres para inferir carpeta raíz."""
    if not filenames: return "General"
    cleaned = []
    for f in filenames:
        base = f
        for ext in ['.rar', '.zip', '.7z', '.iso', '.exe', '.bin', '.001']:
            if base.lower().endswith(ext):
                base = base[:len(base)-len(ext)]
                break
        base = re.sub(r'[\.\-_ ]?(part|vol|cd|dvd)\d*$', '', base, flags=re.I)
        base = re.sub(r'[\.\-_ ]\d{1,3}$', '', base)
        base = re.sub(r'[\.\-_ ](part|vol|cd|dvd)$', '', base, flags=re.I)
        cleaned.append(base.strip(' .-_'))
    if not cleaned: return "General"
    prefix = os.path.commonprefix(cleaned).strip(' .-_')
    if len(prefix) < 4: return "General"
    return prefix

def is_probably_valid_hoster(link):
    """Verifica si una URL parece ser un hoster final."""
    if not link: return False
    if not link.startswith("http"): return False
    if "/masked/" in link: return False
    if "mega.nz" in link:
        return any(x in link for x in ["/file/", "/folder/", "#!", "#F!"]) or len(link.rstrip('/').split('/')[-1]) > 10
    if "mediafire.com" in link: return any(x in link for x in ["/file/", "/view/"])
    if "drive.google.com" in link: return "/d/" in link or "id=" in link
    if any(h in link for h in ["rapidgator.net", "uptobox.com", "1fichier.com", "pixeldrain.com", "gofile.io"]): return True
    return True

def unwrap_link(link):
    """Desenmascara enlaces indirectos simples."""
    if not link: return link
    if "/masked/" in link and "f95zone.to" in link: return link
    if "anonym.to/?" in link:
        parts = link.split("anonym.to/?")
        if len(parts) > 1: return parts[1]
    return link

class F95ZoneResolver:
    """Gestión de login y resolución en f95zone.to (v2.9)."""
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        self.is_logged_in = False
        self.base_url = "https://f95zone.to"

    def login(self, user, password):
        """Login en f95zone.to con manejo de anti-bot."""
        try:
            r = self.scraper.get(f"{self.base_url}/login/", timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            token = soup.find('input', {'name': '_xfToken'})['value'] if soup.find('input', {'name': '_xfToken'}) else ""
            
            login_data = {'login': user, 'password': password, 'remember': '1', '_xfToken': token, '_xfRedirect': f'{self.base_url}/'}
            headers = {'Referer': f"{self.base_url}/login/", 'Origin': self.base_url}
            
            rl = self.scraper.post(f"{self.base_url}/login/login", data=login_data, headers=headers, timeout=15, allow_redirects=True)
            if any(c.name == 'xf_user' for c in self.scraper.cookies):
                self.is_logged_in = True
                return True, "OK"
            
            err_box = BeautifulSoup(rl.text, 'html.parser').find('div', class_='blockMessage--error')
            err_msg = err_box.get_text(strip=True) if err_box else "Error desconocido"
            if 'two-step' in rl.text.lower(): err_msg = "Se requiere 2FA. Desactívalo temporalmente."
            return False, err_msg
        except Exception as e:
            return False, str(e)

    def resolve(self, masked_url):
        """Resuelve un enlace /masked/ a su URL final (v2.9 Clean Resolve)."""
        if not self.is_logged_in: return None, "Not logged in"
        try:
            print(f"[F95] Accediendo a: {masked_url}")
            r = self.scraper.get(masked_url, timeout=15, allow_redirects=True)
            soup = BeautifulSoup(r.text, 'html.parser')
            raw_text = r.text.replace('\\/', '/')
            
            # A. Token CSRF
            xf_token = ""
            token_match = re.search(r'name="_xfToken" value="([^"]+)"', r.text) or re.search(r'data-csrf="([^"]+)"', r.text)
            if token_match: 
                xf_token = token_match.group(1)
            else:
                # [NUEVO v2.11] Fallback: Obtener token de la HOME si no está en la página actual
                print("[F95] Token no hallado en página. Buscando en la home...")
                try:
                    rh = self.scraper.get(self.base_url, timeout=10)
                    tm = re.search(r'name="_xfToken" value="([^"]+)"', rh.text) or re.search(r'data-csrf="([^"]+)"', rh.text)
                    if tm:
                        xf_token = tm.group(1)
                        print(f"[F95] Token recuperado de la home: {xf_token[:10]}...")
                except: pass

            # B. Búsqueda Directa (Regex)
            patterns = [
                r'https?://mega\.nz/(?:file/)?[A-Za-z0-9%_-]+#[A-Za-z0-9%_-]+',
                r'https?://mega\.nz/#[!A-Za-z0-9%_-]+',
                r'https?://pixeldrain\.com/[ul]/[A-Za-z0-9%_-]+',
                r'https?://gofile\.io/d/[A-Za-z0-9%_-]+'
            ]
            for p in patterns:
                m = re.search(p, urllib.parse.unquote(raw_text))
                if m: return m.group(0), "Success"

            # C. AJAX POST (Simular botón Continue)
            if xf_token and ("masked-link" in raw_text or "Continue" in raw_text):
                print("[F95] Solicitando enlace vía AJAX...")
                try:
                    ajax_data = {'xhr': 1, 'download': 1, '_xfToken': xf_token, '_xfResponseType': 'json'}
                    ajax_headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': r.url}
                    res_ajax = self.scraper.post(r.url, data=ajax_data, headers=ajax_headers, timeout=10)
                    if res_ajax.status_code == 200:
                        json_data = res_ajax.json()
                        if json_data.get('status') == 'captcha': return None, "Captcha detectado (Resuelve en navegador)"
                        final = json_data.get('msg') or json_data.get('url') or json_data.get('redirect')
                        if final and final.startswith('http'): return final.replace('\\/', '/'), "Success"
                except: pass

            # D. Escaneo de Tags y Gateways
            for tag in soup.find_all(['a', 'button', 'input']):
                val = tag.get('href') or tag.get('data-url') or tag.get('value')
                if not val or val == "#": continue
                if val.startswith('/'): val = f"https://f95zone.to{val}"
                if "f95zone.to" not in val and is_probably_valid_hoster(val): return val, "Success"
                if any(x in val for x in ["leaving", "to=", "url="]):
                    try:
                        p = urllib.parse.parse_qs(urllib.parse.urlparse(val).query)
                        ext = p.get('url', [None])[0] or p.get('link', [None])[0] or p.get('to', [None])[0]
                        if ext and ext.startswith('http'): return ext, "Success"
                    except: pass
            
            # Final Fallback: Meta Refresh
            meta = soup.find('meta', attrs={'http-equiv': 'refresh'})
            if meta:
                content = meta.get('content', '')
                if 'url=' in content.lower():
                    url_part = content.split('url=', 1)[-1].strip().strip("'\"").replace('\\/', '/')
                    if url_part.startswith('/'): url_part = f"https://f95zone.to{url_part}"
                    return url_part, "Success"

            return None, "No se encontró el hoster"
        except Exception as e:
            return None, f"Excepción: {str(e)}"
