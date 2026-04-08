import os
import time
import requests
import urllib.parse
import hashlib
import json
import re
import zipfile
from utils.helpers import format_size, get_file_md5, detect_file_type, get_clean_name, detect_common_pattern, unwrap_link, is_probably_valid_hoster, F95ZoneResolver

def download_worker(iid, filename, download_rows, config, update_queue, 
                   stopped_iids, running_iids, force_rotate, 
                   get_text_func, stop_requested_check):
    """
    Motor de descarga multi-hoster (v3.16.3). Identificación por IID para robustez.
    """
    row_data = download_rows.get(iid)
    if not row_data: return
    
    link_list = row_data["links"]
    api_key = config.get("api_key", "").strip()
    
    # Calcular rutas
    base_dir = config.get("base_dir", "T:\\Descargas")
    sub_folder = row_data.get("subfolder", "General")
    target_dir = os.path.join(base_dir, sub_folder)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, filename)
    
    fatal_sys_err = ""
    host_success = False
    
    # EL GRAN BUCLE DEL ARRAY MULTI-HOSTER
    for link_idx, direct_raw_link in enumerate(link_list):
        direct_link = None
        if stop_requested_check() or iid in stopped_iids: return
        
        # Comprobar señal de rotación manual (v3.16 por IID)
        if iid in force_rotate and link_idx == 0:
            force_rotate.discard(iid)
            rotated = link_list[1:] + link_list[:1]
            row_data["links"] = rotated
            link_list = rotated
            direct_raw_link = link_list[0]
            update_queue.put(('log', iid, f"[{get_text_func('prefix_rotate')}] {get_text_func('log_rotate_ok')}. {urllib.parse.urlparse(direct_raw_link).netloc}"))
        
        force_rotate.discard(iid)
        
        try:
            host_domain = urllib.parse.urlparse(direct_raw_link).netloc
        except:
            host_domain = "UnknownHoster"
        
        update_queue.put(('log', iid, f"\n[----- {get_text_func('log_attempt')} {link_idx+1}/{len(link_list)} | Hoster: {host_domain} -----]"))
        update_queue.put(("status", iid, f"[{host_domain}] {get_text_func('st_rotating')}"))
        
        # RESOLVER f95zone.to
        if "f95zone.to" in direct_raw_link and "/masked/" in direct_raw_link:
            f95_user = config.get("f95_user", "").strip()
            f95_pass = config.get("f95_pass", "").strip()
            
            if f95_user and f95_pass:
                update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] (f95zone.to) (1/3) Procesando: {direct_raw_link}"))
                resolver = F95ZoneResolver()
                ok, msg = resolver.login(f95_user, f95_pass)
                if ok:
                    update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] (f95zone.to) (2/3) Desenmascarando URL definitiva..."))
                    final_url, msg_res = resolver.resolve(direct_raw_link)
                    if final_url:
                        direct_raw_link = final_url
                        host_domain = urllib.parse.urlparse(direct_raw_link).netloc
                        update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] (f95zone.to) (3/3) URL desenmascarada: {host_domain}"))
                    else:
                        update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] Error resolución f95: {msg_res}"))
                        update_queue.put(("status", iid, f"[{host_domain}] Error resolución f95"))
                        continue
                else:
                    update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] {get_text_func('log_f95_login_err')}: {msg}"))
                    update_queue.put(("status", iid, f"[{host_domain}] Error Login f95"))
                    continue
            else:
                update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] f95zone masked link sin credenciales configuradas"))
                update_queue.put(("status", iid, f"[{host_domain}] Config f95 necesaria"))
                continue

        # DESBLOQUEO Real-Debrid
        api_url = "https://api.real-debrid.com/rest/1.0/unrestrict/link"
        try:
            update_queue.put(('log', iid, f"[{get_text_func('prefix_req')}] {get_text_func('log_unrestricting')} -> {direct_raw_link}"))
            r = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}"}, data={"link": direct_raw_link}, timeout=15)
            if stop_requested_check() or iid in stopped_iids: return
            
            if r.status_code == 200:
                data = r.json()
                direct_link = data.get('download')
                row_data['filesize'] = data.get('filesize', 0)
                
                # Sincronización de nombre
                rd_filename = data.get('filename') or data.get('original_filename')
                if rd_filename and rd_filename != filename and len(rd_filename) > 3:
                    update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] Sincronizando nombre real: {rd_filename}"))
                    update_queue.put(('rename', iid, rd_filename))
                    filename = rd_filename
                    target_path = os.path.join(target_dir, filename)

                update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] {get_text_func('log_unrestrict_ok')} ({host_domain})"))
            else:
                # Fallback Reactivo
                unwrapped = unwrap_link(direct_raw_link)
                if unwrapped != direct_raw_link and is_probably_valid_hoster(unwrapped):
                    update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] {get_text_func('log_unmasking')} -> {unwrapped}"))
                    r = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}"}, data={"link": unwrapped}, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        direct_link = data.get('download')
                        update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] {get_text_func('log_unrestrict_ok')} (Unwrapped)"))
                    else:
                        err_txt = r.json().get('error', f'HTTP {r.status_code}')
                        update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] {err_txt}"))
                else:
                    update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] {get_text_func('log_unrestrict_fail')} ({r.status_code})"))
                    continue

        except Exception as e:
            update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] Error RD: {e}"))
            continue
            
        if not direct_link: continue
            
        # DESCARGA
        max_retries = 3
        host_success_in_download = False
        
        for attempt in range(max_retries):
            if stop_requested_check() or iid in stopped_iids: return
            if iid in force_rotate:
                force_rotate.discard(iid)
                break
            
            try:
                conn_text = get_text_func("log_connecting") if attempt == 0 else f"{get_text_func('log_reconnecting')} {attempt+1}/{max_retries}"
                update_queue.put(("status", iid, f"[{host_domain}] {conn_text}"))
                
                head_resp = requests.head(direct_link, timeout=15)
                head_resp.raise_for_status()
                
                total_size = int(head_resp.headers.get('content-length', 0))
                if total_size > 0: row_data['filesize'] = total_size
                    
                headers = {}
                existing_size = 0
                mode = 'wb'
                
                if os.path.exists(target_path):
                    existing_size = os.path.getsize(target_path)
                    if total_size > 0:
                        if existing_size == total_size:
                            update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] {get_text_func('log_cache_hit')}"))
                            update_queue.put(("progress_full", iid, total_size, total_size, 0, f"{get_text_func('st_completed')}"))
                            update_queue.put(("worker_done", iid))
                            return
                        elif existing_size < total_size:
                            update_queue.put(('log', iid, f"[{get_text_func('prefix_range')}] {get_text_func('log_range')} ({format_size(existing_size)})"))
                            headers['Range'] = f"bytes={existing_size}-"
                            mode = 'ab'
                        else:
                            os.remove(target_path)
                            existing_size = 0
                
                response = requests.get(direct_link, headers=headers, stream=True, timeout=15)
                response.raise_for_status()
                
                if response.status_code == 200 and existing_size > 0:
                    existing_size = 0
                    mode = 'wb'
                
                block_size = 1024 * 64
                downloaded = existing_size
                start_time = time.time()
                last_ui_update = start_time
                last_chunk_time = start_time
                
                with open(target_path, mode) as f:
                    for chunk in response.iter_content(block_size):
                        if stop_requested_check() or iid in stopped_iids or iid in force_rotate:
                            st_final = get_text_func("st_paused") if iid in stopped_iids else get_text_func("st_manual_stop")
                            update_queue.put(("progress_full", iid, downloaded, total_size or downloaded, 0, st_final))
                            update_queue.put(("worker_done", iid))
                            return
                        
                        if chunk:
                            # --- Lógica de Limitación de Ancho de Banda (v1.1.20260405) ---
                            limit_mb = config.get("speed_limit_mb", 0)
                            if limit_mb > 0:
                                active_count = config.get("_active_count", 1)
                                if active_count < 1: active_count = 1
                                target_bw = (limit_mb * 1024 * 1024) / active_count
                                expected_time = len(chunk) / target_bw
                                actual_time = time.time() - last_chunk_time
                                if expected_time > actual_time:
                                    time.sleep(expected_time - actual_time)

                            f.write(chunk)
                            downloaded += len(chunk)
                            last_chunk_time = time.time()
                            
                            now = time.time()
                            if now - last_ui_update > 0.8:
                                elapsed = now - start_time
                                speed = (downloaded - existing_size) / elapsed if elapsed > 0 else 0
                                update_queue.put(("progress_full", iid, downloaded, total_size or downloaded, speed, f"Activo [{host_domain}]"))
                                last_ui_update = now
                    else:
                        update_queue.put(('log', iid, f"[{get_text_func('prefix_sys')}] {get_text_func('log_final_ok')} ({host_domain})"))
                        update_queue.put(("progress_full", iid, total_size or downloaded, total_size or downloaded, 0, f"{get_text_func('st_completed')}"))
                        update_queue.put(("worker_done", iid))
                        host_success_in_download = True
                        break
            except Exception as e:
                if stop_requested_check() or iid in stopped_iids: return
                update_queue.put(('log', iid, f"[DROP] Error: {str(e)[:80]}"))
                time.sleep(2)
        
        if host_success_in_download:
            host_success = True
            break
            
    if not host_success:
        update_queue.put(("error", iid, get_text_func("log_all_hosters_down")))
        update_queue.put(("worker_done", iid))

def verify_worker(iid, filename, download_rows, config, update_queue, get_text_func, stop_requested_check):
    """Motor de verificación de integridad por IID."""
    if iid not in download_rows: return
    row_data = download_rows[iid]
    
    try:
        base_dir = config.get("base_dir", "C:\\Descargas")
        sub_folder = row_data.get("subfolder", "General")
        local_path = os.path.join(base_dir, sub_folder, filename)
        
        if not os.path.exists(local_path):
            update_queue.put(('verify_done', iid, " [!]", 'failed', get_text_func('st_not_found'), {"status": "NOT_FOUND"}))
            return

        update_queue.put(("verify_status", iid, f"{get_text_func('st_verifying')}..."))
        update_queue.put(('log', iid, f"[{get_text_func('prefix_verify')}] {get_text_func('log_verify_start')}..."))
        
        # MD5 con reporte de progreso (v3.16.33)
        hash_md5 = hashlib.md5()
        local_bytes = os.path.getsize(local_path)
        processed_bytes = 0
        last_progress_update = 0
        
        with open(local_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024*1024), b""):
                if stop_requested_check(): return
                hash_md5.update(chunk)
                processed_bytes += len(chunk)
                
                # Actualizar progreso en la tabla cada ~10MB para fluidez (v3.16.49)
                if processed_bytes - last_progress_update > 10 * 1024 * 1024:
                    last_progress_update = processed_bytes
                    pct = (processed_bytes / local_bytes) * 100 if local_bytes > 0 else 0
                    prefix = " (1/2)" if filename.lower().endswith(".zip") else ""
                    update_queue.put(("progress_full", iid, processed_bytes, local_bytes, 0, f"{get_text_func('st_verifying')}{prefix} ({int(pct)}%)"))
                
        final_md5 = hash_md5.hexdigest()
        mime, magic = detect_file_type(local_path)
        stored_remote = row_data.get('filesize', 0)
        
        # Comprobación de cordura (v3.16.54): si el tamaño remoto guardado es
        # absurdamente diferente al local (menos del 1% del local), usamos local_bytes.
        # Esto evita falsos "size mismatch" cuando session.json tiene datos corruptos.
        if stored_remote > 0 and local_bytes > 0:
            ratio = stored_remote / local_bytes
            if ratio < 0.01 or ratio > 100:
                update_queue.put(('log', iid, f"[WARN] Tamaño remoto guardado ({format_size(stored_remote)}) parece incorrecto vs local ({format_size(local_bytes)}). Usando tamaño local como referencia."))
                effective_remote = local_bytes
            else:
                effective_remote = stored_remote
        else:
            effective_remote = stored_remote or local_bytes
        
        size_match = (local_bytes == effective_remote)
        
        # Estructural ZIP con logs detallados (v3.16.55 - recolecta TODOS los errores)
        zip_error = None
        repair_ranges = []  # Lista de todos los rangos corruptos
        is_zip = ("ZIP" in magic or filename.lower().endswith(".zip"))
        
        if size_match and is_zip:
            update_queue.put(("verify_zip_status", iid, f"{get_text_func('st_verifying_zip')} (2/2)..."))
            try:
                with zipfile.ZipFile(local_path) as zf:
                    infolist = zf.infolist()
                    infolist.sort(key=lambda x: x.header_offset)
                    total_files = len(infolist)
                    
                    for i, zinfo in enumerate(infolist, 1):
                        if stop_requested_check(): return
                        
                        # Reporte visual de progreso (%) con Fase 2/2 (v3.16.49)
                        pct_zip = (i / total_files) * 100
                        update_queue.put(("progress_full", iid, i, total_files, 0, f"{get_text_func('st_verifying_zip')} (2/2) ({int(pct_zip)}%)"))
                        
                        # Log detallado en la consola cada 5 archivos para no saturar
                        if total_files < 20 or i % 5 == 0 or i == total_files:
                            update_queue.put(('log', iid, f"[{get_text_func('prefix_verify')}] {get_text_func('st_verifying_zip')}: {i}/{total_files} - {zinfo.filename}"))
                        
                        try:
                            zf.read(zinfo.filename)
                        except Exception as e_crc:
                            # Rango preciso del archivo corrupto dentro del ZIP
                            local_header_size = 30 + len(zinfo.filename.encode('utf-8')) + len(zinfo.extra)
                            start = zinfo.header_offset
                            end = zinfo.header_offset + local_header_size + zinfo.compress_size - 1
                            repair_ranges.append((start, end))
                            err_msg = f"CRC Error: {zinfo.filename} | Rango: {format_size(end - start + 1)} (offset {start} → {end})"
                            if not zip_error:
                                zip_error = f"CRC Error: {zinfo.filename}"  # primer error para el resumen
                            update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] {err_msg}"))
                            # NO hacemos break, seguimos buscando más errores
            except Exception as e:
                if not zip_error: zip_error = f"Zip Structure Error: {str(e)}"
        
        if repair_ranges:
            total_repair = sum(e - s + 1 for s, e in repair_ranges)
            update_queue.put(('log', iid, f"[{get_text_func('prefix_err')}] Total corrupción detectada: {len(repair_ranges)} archivo(s), {format_size(total_repair)} a reparar"))

        # Umbral de cordura (v3.16.58): si hay que reparar más del 80% del archivo,
        # la cirugía no tiene sentido — mejor re-descargar el archivo completo.
        if repair_ranges and local_bytes > 0:
            total_repair_bytes = sum(e - s + 1 for s, e in repair_ranges)
            ratio_repair = total_repair_bytes / local_bytes
            if ratio_repair > 0.80:
                update_queue.put(('log', iid, f"[WARN] Reparación quirúrgica requiere {format_size(total_repair_bytes)} ({int(ratio_repair*100)}% del archivo). Se recomienda re-descarga completa."))
                repair_ranges = []  # forzar botón de re-descarga en lugar de cirugía

        is_ok = size_match and (zip_error is None)
        report = {
            "status": "OK" if is_ok else "ERROR", 
            "status_msg": "OK" if is_ok else (zip_error or "CRC/Structure Error"),
            "md5": final_md5, 
            "mime_type": mime,
            "magic_desc": magic,
            "struct_ok": (zip_error is None),
            "repair_range": repair_ranges[0] if repair_ranges else None,  # compatibilidad modal
            "repair_ranges": repair_ranges,  # lista completa para reparación masiva
            "local_size_formatted": format_size(local_bytes),
            "local_size_bytes": local_bytes,
            "remote_size_formatted": format_size(effective_remote), 
            "remote_size_bytes": effective_remote,
            "size_match": size_match,
            "size_diff": abs(local_bytes - effective_remote),
            "path": local_path
        }
        
        tag = 'completed' if is_ok else 'failed'
        bar = "  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] 100% "
        update_queue.put(('verify_done', iid, bar, tag, "OK" if is_ok else "ERROR", report))
        
    except Exception as e:
        update_queue.put(('log', iid, f"Error Verif: {e}"))
    finally:
        row_data["is_verifying"] = False

def extract_multi_dlc_worker(paths, update_queue, get_text_func):
    """Motor de extracción masiva de enlaces DLC/TXT (v3.16.60 - Restaurado)."""
    all_links = []
    try:
        total = len(paths)
        update_queue.put(('show_loader', "Analizando ficheros DLC/Links...", total))
        
        for idx, path in enumerate(paths, 1):
            update_queue.put(('update_loader', idx, f"[{idx}/{total}] Procesando: {os.path.basename(path)}"))
            
            ext = path.lower().split(".")[-1]
            if ext == "txt":
                # Intentar varios encodings comunes en Windows (v3.16.60)
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(path, 'r', encoding=encoding) as f:
                            lines = [l.strip() for l in f if l.strip() and l.strip().startswith('http')]
                            all_links.extend(lines)
                        break
                    except: continue
            else:
                # Extracción DLC vía API (dcrypt.it)
                try:
                    with open(path, 'rb') as f:
                        response = requests.post('http://dcrypt.it/decrypt/upload', files={'dlcfile': f}, timeout=20)
                    if response.status_code == 200:
                        # Limpieza de HTML de la respuesta (Regex robusto)
                        match = re.search(r'<textarea>(.*?)</textarea>', response.text, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1).strip())
                            links = data.get('success', {}).get('links', [])
                            all_links.extend(links)
                except Exception as e:
                    print(f"[DEBUG] Error procesando DLC {path}: {e}")
            
            time.sleep(0.1)
        
        if not all_links:
            update_queue.put(('hide_loader', None))
            update_queue.put(('links_failed', "No se encontraron enlaces válidos en los archivos seleccionados."))
            return
        
        update_queue.put(('update_loader', total, "Agrupando archivos y detectando carpetas..."))
        grouped_data = group_links_by_name(all_links)

        update_queue.put(('hide_loader', None))
        update_queue.put(('multi_links_loaded', grouped_data))

    except Exception as e:
        update_queue.put(('hide_loader', None))
        update_queue.put(('links_failed', f"Error en procesamiento masivo: {e}"))

def group_links_by_name(all_links):
    """Agrupa enlaces por nombre real y detecta automáticamente subcarpetas lógicas (v3.16.60)."""
    grouped_data = {}
    temp_filenames = []
    
    # 1. Agrupar enlaces idénticos bajo el mismo nombre de archivo
    for l in all_links:
        name = get_clean_name(l)
        if name not in grouped_data:
            grouped_data[name] = {'links': [], 'folder': 'General'}
            temp_filenames.append(name)
        if l not in grouped_data[name]['links']:
            grouped_data[name]['links'].append(l)
    
    # 2. Detección Inteligente de Subcarpeta (Common Prefix Logic)
    if len(temp_filenames) > 1:
        temp_filenames.sort()
        for i in range(len(temp_filenames)):
            best_match = ""
            # Comparar con vecinos para encontrar prefijo común (Juego - Part1, Juego - Part2...)
            for j in [i-1, i+1]:
                if 0 <= j < len(temp_filenames):
                    common = os.path.commonprefix([temp_filenames[i], temp_filenames[j]])
                    common = common.strip(' .-_')
                    if len(common) > 5:
                        if len(common) > len(best_match): best_match = common
            
            if best_match:
                # Limpiar sufijos de partes/volúmenes del nombre de la carpeta
                best_match = re.sub(r'[\.\-_ ]?(part|vol|cd|dvd)\d*$', '', best_match, flags=re.I)
                best_match = re.sub(r'[\.\-_ ]\d{1,3}$', '', best_match)
                best_match = re.sub(r'[\.\-_ ](part|vol|cd|dvd)$', '', best_match, flags=re.I)
                grouped_data[temp_filenames[i]]['folder'] = best_match.strip(' .-_')
    
    return grouped_data

def extract_links_from_text_worker(text, update_queue, get_text_func):
    """Procesa texto pegado manualmente y lo añade a la cola (v3.16.61 - Optimizado sin modal)."""
    try:
        # Filtro de enlaces básicos
        all_links = [line.strip() for line in text.splitlines() if line.strip() and line.strip().startswith('http')]
        
        if not all_links:
            update_queue.put(('links_failed', "No se detectaron enlaces 'http' válidos en el texto."))
            return
            
        grouped_data = group_links_by_name(all_links)
        update_queue.put(('multi_links_loaded', grouped_data))
    except Exception as e:
        update_queue.put(('links_failed', f"Error en procesamiento manual: {e}"))

def resolve_filename_from_url(url, api_key=None):
    """Resuelve el nombre real usando RD (si hay Key) o Scraping de Títulos (v3.1.20260405)."""
    from utils.helpers import get_clean_name, is_probably_valid_hoster
    fallback_name = get_clean_name(url)
    
    # 1. Intentar vía Real-Debrid (Solo si hay Key y es un hoster válido)
    if api_key and is_probably_valid_hoster(url):
        try:
            import requests
            data = {'link': url}
            headers = {'Authorization': f'Bearer {api_key}'}
            resp = requests.post("https://api.real-debrid.com/rest/1.0/unrestrict/link", 
                                 data=data, headers=headers, timeout=8)
            if resp.status_code == 200:
                rd_data = resp.json()
                if 'filename' in rd_data:
                    return rd_data['filename']
        except:
            pass # Fallback al scraping si RD falla o no hay quota

    # 2. Intentar vía Scraping de Título (Cloudscraper)
    try:
        import cloudscraper
        from bs4 import BeautifulSoup
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.title.string if soup.title else ""
            if title:
                # Limpiar títulos comunes de hosters
                clean_title = title.strip()
                for junk in ["1fichier.com -", "Rapidgator.net -", "Download file", "Free Download"]:
                    clean_title = clean_title.replace(junk, "").strip()
                if len(clean_title) > 5:
                    return clean_title
    except:
        pass

    # 3. Fallback final: HEAD request o Nombre sucio de URL
    try:
        import requests
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, allow_redirects=True, timeout=5, headers=headers)
        cd = response.headers.get('Content-Disposition')
        if cd and 'filename=' in cd:
            import re
            fname = re.findall('filename="?([^"]+)"?', cd)
            if fname: return fname[0].strip()
        
        if response.url != url:
            return get_clean_name(response.url)
    except:
        pass
        
    return fallback_name
