import os
import time
import requests
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from core.engine import download_worker, verify_worker
from core.config import SESSION_FILE
from utils.helpers import format_size
from ui.components.modals import ProcessingModal, VerificationWindow, PremiumMessageModal

class DownloadMixin:
    """Mixin para gestionar la lógica de descargas, colas y workers (v1.1.20260402)."""

    def start_all_downloads(self):
        """Inicia el motor para TODOS los archivos de la lista (v3.16.31)."""
        self.start_downloads(start_all=True)

    def start_selected_downloads(self):
        """Inicia los archivos seleccionados en azul."""
        selection = self.tree.selection()
        if not selection:
            PremiumMessageModal(self, self.get_id_text("msg_api_title"), self.get_id_text("msg_no_links"))
            return
        self.start_downloads(override_iids=list(selection))

    def stop_downloads(self):
        """Detiene todas las descargas y verificaciones solicitando parada a los workers (v1.1.20260405)."""
        self.stop_requested = True
        self.is_downloading = False
        self.pending_iids.clear()
        self.active_speeds.clear()
        
        # Marcar visualmente lo que se estaba descargando
        for iid in list(self.running_iids):
            self.tree.set(iid, "resultado", f"  🛑 {self.get_id_text('st_stopping')}")

        # Marcar visualmente lo que se estaba verificando (v1.1.20260405)
        for iid in list(self.verifying_iids):
            self.tree.set(iid, "resultado", f"  🛑 {self.get_id_text('st_stopping')}")
        
        self._update_action_buttons_ui(is_downloading=False)
        self._update_status_bar_ui()

    def stop_selected_downloads(self, override_iids=None):
        """Detiene los archivos seleccionados (blue selection o override)."""
        iids_to_stop = override_iids if override_iids else list(self.tree.selection())
        
        # 🔥 Limpieza quirúrgica de la cola pendiente (v1.1.20260405)
        for iid in iids_to_stop:
            if iid in self.pending_iids:
                self.pending_iids.remove(iid)
        
        for iid in iids_to_stop:
            if iid in self.running_iids or iid in self.verifying_iids:
                self.stopped_iids.add(iid)
                self.tree.set(iid, "resultado", f"  🛑 {self.get_id_text('st_stopping')}")

    def start_downloads(self, override_iids=None, start_all=False):
        """Inicia el motor de descargas basándose en la selección o en toda la lista."""
        if self.is_downloading and not override_iids: return
        
        token = self.config.get("api_key", "").strip()
        if not token:
            PremiumMessageModal(self, self.get_id_text("msg_api_title"), self.get_id_text("msg_api_empty"), icon="warn")
            return

        if not hasattr(self, "pending_iids"): self.pending_iids = []
        if not hasattr(self, "running_iids"): self.running_iids = set()
        if not hasattr(self, "stopped_iids"): self.stopped_iids = set()

        # 🔥 Lógica Unificada: Blue Selection o All (v1.1.20260405)
        if start_all:
            target_list = list(self.download_rows.keys())
        else:
            target_list = override_iids if override_iids else list(self.tree.selection())

        added_count = 0
        skipped_count = 0

        for iid in target_list:
            if iid in self.stopped_iids: self.stopped_iids.remove(iid)
            
            # 🔥 Optimización Re-verificación Inteligente (v1.1.20260405)
            data = self.download_rows.get(iid)
            if data:
                is_done = (data.get("downloaded", 0) >= data.get("filesize", 1)) if data.get("filesize", 0) > 0 else False
                if is_done and data.get("verified", False):
                    skipped_count += 1
                    continue # Ya está perfecto, no encolar ni verificar de nuevo
            
            if iid not in self.pending_iids and iid not in self.running_iids:
                self.pending_iids.append(iid)
                added_count += 1

        if not self.pending_iids and not self.running_iids:
            self.is_downloading = False
            if skipped_count > 0 and added_count == 0:
                PremiumMessageModal(self, self.get_id_text("prefix_notice"), self.get_id_text("msg_all_verified"), icon="success")
            else:
                PremiumMessageModal(self, self.get_id_text("prefix_notice"), self.get_id_text("msg_no_links"))
            return

        if not self.is_downloading:
            self.is_downloading = True
            self.stop_requested = False
            self._update_action_buttons_ui(is_downloading=True)
            self._check_and_launch_next()
        else:
            self._check_and_launch_next()

    def _has_active_tasks(self):
        """Comprueba si hay alguna tarea pendiente, descargando o verificando (v1.1.20260405)."""
        has_pending = bool(getattr(self, "pending_iids", []))
        has_running = bool(getattr(self, "running_iids", set()))
        has_verifying = bool(getattr(self, "verifying_iids", set()))
        return has_pending or has_running or has_verifying

    def _check_and_launch_next(self):
        """Planificador dinámico de descargas concurrentes por IID (v1.1.20260405)."""
        if self.stop_requested:
            if not self.running_iids and not self.verifying_iids:
                self.is_downloading = False
                self._update_action_buttons_ui(is_downloading=False)
            return

        # Si no hay nada pendiente ni corriendo (incl. verificaciones), apagamos botones de parada
        if not self._has_active_tasks():
            self.is_downloading = False
            self._update_action_buttons_ui(is_downloading=False)
            return

        while len(self.running_iids) < self.config["max_workers"] and self.pending_iids:
            iid = self.pending_iids.pop(0)
            if iid in self.running_iids: continue
            
            self.running_iids.add(iid)
            self.config["_active_count"] = len(self.running_iids)
            row_data = self.download_rows[iid]
            filename = row_data["filename"]
            self.tree.set(iid, "velocidad", "  ⌛ ...")
            
            threading.Thread(target=download_worker, 
                             args=(iid, filename, self.download_rows, self.config, self.update_queue, 
                                   self.stopped_iids, self.running_iids, self.force_rotate,
                                   self.get_id_text, lambda: self.stop_requested or iid in self.stopped_iids), 
                             daemon=True).start()

    def rotate_selected_link(self):
        """Señal de rotación para todos los hosters con [X] marcada por IID."""
        for iid, data in self.download_rows.items():
            if data["checked"]:
                if len(data.get("links", [])) > 1:
                    self.force_rotate.add(iid)
                    self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_rotate')}] {self.get_id_text('log_rotate_ok')}"))
                    self.tree.set(iid, "resultado", f"  🔄 {self.get_id_text('st_rotating')}")
                else:
                    self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_rotate')}] {self.get_id_text('log_rotate_none')}"))

    def _start_selected_file(self):
        """Lógica para el menú contextual: Inicia la SELECCIÓN VISUAL (azul) sin tocar las [X]."""
        selection = self.tree.selection()
        if not selection: return
        self.start_downloads(override_iids=list(selection))

    def _stop_selected_file(self):
        """Lógica para el menú contextual: Detiene la SELECCIÓN VISUAL (azul)."""
        selection = self.tree.selection()
        if not selection: return
        self.stop_selected_downloads(override_iids=list(selection))

    def smart_repair_selected(self):
        """Repara todos los archivos seleccionados usando el motor inteligente (v1.1.20260405)."""
        selection = self.tree.selection()
        if not selection: return
        for iid in selection:
            self.smart_repair_by_iid(iid, start_engine=False)
        self.start_downloads()

    def smart_repair_by_iid(self, iid, start_engine=True):
        """Lógica inteligente de reparación: parcheo al primer intento, re-descarga al segundo (v1.1.20260405)."""
        if iid not in self.download_rows: return
        
        data = self.download_rows[iid]
        attempts = data.get("repair_attempts", 0)
        filesize = data.get("filesize", 0)
        filename = data.get("filename", "Archivo")
        
        # 1. Incrementar intentos
        data["repair_attempts"] = attempts + 1
        
        # 2. Decisión lógica
        # Si ya se intentó reparar y sigue fallando (attempts >= 1), forzamos descarga completa.
        # Excepto si el archivo es enorme (> 1GB) y todavía queremos darle una oportunidad de parcheo manual desde el modal.
        if attempts >= 1:
            self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_fix')}] Falló reparación previa. Iniciando re-descarga completa del archivo..."))
            self.force_redownload_by_iid(iid)
            return

        # Primer intento de reparación
        is_large = filesize > 1024 * 1024 * 1024 # > 1 GB
        if is_large:
            self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_fix')}] Archivo grande detectado ({format_size(filesize)}). Intentando parcheo de integridad..."))
        
        self.force_resume_by_iid(iid, start_engine=start_engine)

    def force_repair_by_iid(self, iid):
        """Disparador oficial para el botón Reparar (v3.16.47)."""
        # Si no hay rango de cirugía, simplemente reanudamos normal (sin truncar)
        self.force_resume_by_iid(iid, start_engine=True)

    def force_redownload_by_iid(self, iid):
        """Elimina el archivo local corrupto y fuerza re-descarga desde cero (v3.16.59)."""
        if iid not in self.download_rows: return
        row_data = self.download_rows[iid]
        filename = row_data["filename"]
        sub_folder = row_data.get("subfolder", self.var_subfolder.get().strip())
        target_path = os.path.join(self.config["base_dir"], sub_folder, filename)
        
        # Eliminar archivo corrupto del disco
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_fix')}] Archivo corrupto eliminado. Iniciando re-descarga..."))
                row_data["repair_attempts"] = 0 # Resetear intentos al empezar de cero
            except Exception as e:
                self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_err')}] No se pudo eliminar el archivo: {e}"))
                return
        
        # Resetear progreso para descarga desde cero
        row_data["downloaded"] = 0
        row_data["filesize"] = 0
        row_data["current_link_idx"] = 0
        row_data["checked"] = True
        self.tree.set(iid, "progreso", "  [░░░░░░░░░░░░░░░░░░░░]   0% ")
        self.tree.set(iid, "tamanio", " - ")
        self.tree.set(iid, "resultado", f"  ⏳ {self.get_id_text('st_waiting')} (Re-descarga)")
        self._update_row_tags(iid, clear_all=True)
        
        if iid not in self.pending_iids and iid not in self.running_iids:
            self.pending_iids.append(iid)
        self.start_downloads()

    def force_resume_by_iid(self, iid, start_engine=True):
        """Reanudación forzada SIN TRUNCADO (v3.16.47)."""
        if iid not in self.download_rows: return
        
        row_data = self.download_rows[iid]
        row_data["checked"] = True
        self.tree.set(iid, "resultado", f"  ⏳ {self.get_id_text('st_waiting')}...")
        self._update_row_tags(iid, clear_all=True)
        
        if iid not in self.pending_iids and iid not in self.running_iids:
            self.pending_iids.append(iid)
        
        if start_engine:
            self.start_downloads()

    def surgical_repair_by_iid(self, iid, repair_range):
        """Repara una o múltiples secciones corruptas de un archivo ZIP (v3.16.55)."""
        if not iid or not repair_range or iid not in self.download_rows: return
        
        row_data = self.download_rows[iid]
        filename = row_data["filename"]
        
        # Normalizar: acepta tanto un solo rango como una lista de rangos
        if isinstance(repair_range, list):
            repair_ranges = repair_range
        else:
            repair_ranges = [repair_range]
        
        links = row_data.get("links", [])
        if not links: return

        # Log inicial
        self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_verify')}] Iniciando cirugía binaria: {len(repair_ranges)} sección(es) a reparar..."))
        self.tree.set(iid, "resultado", f"  💉 {self.get_id_text('prefix_fix')} (0/{len(repair_ranges)})...")

        def run_surgery():
            try:
                self.verifying_iids.add(iid)
                row_data["is_verifying"] = True  # protege la columna de tamaño (v3.16.56)
                sub_folder = row_data.get("subfolder", self.var_subfolder.get().strip())
                target_path = os.path.join(self.config["base_dir"], sub_folder, filename)
                
                if not os.path.exists(target_path):
                    raise Exception(f"Archivo local no encontrado: {target_path}")
                
                api_key = self.config.get("api_key", "").strip()
                api_url = "https://api.real-debrid.com/rest/1.0/unrestrict/link"
                
                # Obtener enlace directo una vez (es el mismo archivo)
                self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_verify')}] RD: Solicitando enlace directo..."))
                r = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}"}, data={"link": links[0]}, timeout=15)
                
                if r.status_code != 200:
                    raise Exception(f"RD Error {r.status_code}: {r.text[:100]}")
                
                direct_link = r.json().get('download')
                if not direct_link: raise Exception("RD: No se obtuvo enlace de descarga")
                
                self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_verify')}] Enlace obtenido. Reparando {len(repair_ranges)} sección(es)..."))
                
                # Reparar cada rango secuencialmente
                for idx, (start, end) in enumerate(repair_ranges, 1):
                    expected_bytes = end - start + 1
                    self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_fix')}] Sección {idx}/{len(repair_ranges)}: inyectando {format_size(expected_bytes)} en offset {start}..."))
                    self.tree.set(iid, "resultado", f"  💉 {self.get_id_text('prefix_fix')} ({idx}/{len(repair_ranges)})...")
                    
                    headers = {"Range": f"bytes={start}-{end}"}
                    with requests.get(direct_link, headers=headers, stream=True, timeout=60) as resp:
                        resp.raise_for_status()
                        written = 0
                        with open(target_path, "r+b") as f:
                            f.seek(start)
                            for chunk in resp.iter_content(chunk_size=512 * 1024):
                                if chunk:
                                    f.write(chunk)
                                    written += len(chunk)
                                    pct = (written / expected_bytes * 100) if expected_bytes > 0 else 0
                                    overall = ((idx - 1 + pct / 100) / len(repair_ranges)) * 100
                                    self.update_queue.put(("progress_full", iid, int(overall), 100, 0, f"💉 Cirugía {idx}/{len(repair_ranges)} ({int(pct)}%)"))
                    
                    self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_fix')}] Sección {idx} completada ({format_size(written)})"))
                
                # Todas las secciones reparadas — re-verificar
                row_data["is_verifying"] = False  # la verificación la pondrá a True ella sola
                self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_verify')}] {self.get_id_text('log_surgical_ok')} — Iniciando re-verificación..."))
                time.sleep(0.5)
                self._verify_single_iid(iid)

            except Exception as e:
                print(f"[SURGERY] ERROR: {e}")
                row_data["is_verifying"] = False  # limpiar flag en caso de error
                if iid in self.verifying_iids: self.verifying_iids.remove(iid)
                err_msg = self.get_id_text('log_surgical_err').format(e=str(e))
                self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_err')}] {err_msg}"))
                self.update_queue.put(('status', iid, f"  ❌ {self.get_id_text('prefix_err')}"))

        threading.Thread(target=run_surgery, daemon=True).start()

    def _verify_single_iid(self, iid):
        """Lanza la verificación de un único archivo sin depender de la selección (v3.16.47)."""
        if iid not in self.download_rows: return
        data = self.download_rows[iid]
        data["is_verifying"] = True
        self.verifying_iids.add(iid)
        self._update_row_tags(iid, 'verifying')
        threading.Thread(target=verify_worker, 
                         args=(iid, data["filename"], self.download_rows, self.config, self.update_queue, self.get_id_text, lambda: self.stop_requested or iid in self.stopped_iids), 
                         daemon=True).start()

    def show_technical_report(self):
        """Muestra el último informe de verificación guardado para el archivo seleccionado."""
        selection = self.tree.selection()
        if not selection: return
        iid = selection[0]
        
        if iid in self.download_rows:
            data = self.download_rows[iid]
            report = data.get("last_report")
            if report:
                from ui.components.modals import VerificationWindow
                VerificationWindow(self, data["filename"], report, iid=iid)
            else:
                PremiumMessageModal(self, self.get_id_text('prefix_notice'), self.get_id_text('msg_verify_not_found'), icon="warn")

    def verify_selected_file(self):
        """Inicia el motor de verificación para los archivos seleccionados por IID."""
        selection = self.tree.selection()
        if not selection: return
        for iid in selection:
            self._verify_single_iid(iid)

    def clean_completed_files(self):
        """Elimina de la lista los archivos que están al 100% y verificados OK (v3.2)."""
        to_remove = []
        for iid, data in self.download_rows.items():
            # 1. Obtener estado visual actual (v3.2)
            res_txt = str(self.tree.set(iid, "resultado")).upper()
            tags = self.tree.item(iid, 'tags')
            
            # 2. Criterio de Finalización (100% o Tag verde)
            is_done = (data.get("downloaded", 0) >= data.get("filesize", 0.999)) if data.get("filesize", 0) > 0 else False
            is_completed_tag = 'completed' in tags
            
            # 3. Criterio de Integridad (Dato interno O texto [OK] en la tabla)
            is_verified = data.get("verified", False) or "[OK]" in res_txt
            
            # Decisión final: Debe estar terminado Y verificado
            if (is_done or is_completed_tag) and is_verified:
                to_remove.append(iid)
        
        if not to_remove:
            return
            
        for iid in to_remove:
            if iid in self.download_rows: del self.download_rows[iid]
            if iid in self.logs_dict: del self.logs_dict[iid]
            if self.tree.exists(iid): self.tree.delete(iid)
            
        count = len(to_remove)
        self.update_queue.put(('log', 'Global', f"[SYS] {self.get_id_text('msg_cleaned_count').format(count)}"))
        self._update_status_bar_ui()
        self.save_session()

    def process_queue(self):
        """Procesador de mensajes basado en IID (v3.16.4)."""
        try:
            for _ in range(50):
                msg = self.update_queue.get_nowait()
                mtype = msg[0]
                
                if mtype == 'show_loader':
                    self.processing_modal = ProcessingModal(self, msg[1], msg[2])
                elif mtype == 'update_loader':
                    modal = getattr(self, 'processing_modal', None)
                    if modal and modal.winfo_exists(): modal.update_progress(msg[1], msg[2])
                elif mtype == 'hide_loader':
                    modal = getattr(self, 'processing_modal', None)
                    if modal:
                        if modal.winfo_exists(): modal.destroy()
                        del self.processing_modal
                
                elif mtype == 'rename':
                    iid, new_name = msg[1], msg[2]
                    if iid in self.download_rows:
                        data = self.download_rows[iid]
                        data["filename"] = new_name
                        self.tree.set(iid, "archivo", f"  {new_name}")
                        self.save_session()
                
                elif mtype == 'log':
                    iid, txt = msg[1], msg[2]
                    t_str = time.strftime("%H:%M:%S")
                    if iid not in self.logs_dict: self.logs_dict[iid] = []
                    self.logs_dict[iid].append(f"[{t_str}] {txt}")
                    if len(self.logs_dict[iid]) > 100: self.logs_dict[iid].pop(0)
                    if self.console_visible:
                        sel = self.tree.selection()
                        if sel and sel[0] == iid: self.refresh_console(iid)
                
                elif mtype == 'status':
                    iid, status_text = msg[1], msg[2]
                    if iid in self.download_rows:
                        self.tree.set(iid, "resultado", status_text)
                
                elif mtype == 'progress_full':
                    iid, downloaded, total, speed, status_text = msg[1], msg[2], msg[3], msg[4], msg[5]
                    self.active_speeds[iid] = speed
                    if iid in self.download_rows:
                        data = self.download_rows[iid]
                        pct = max(0.0, min(1.0, downloaded / total if total > 0 else 0))
                        filled = int(pct * 20)
                        bar_text = f"  [{'▓' * filled}{'░' * (20 - filled)}] {int(pct * 100):3d}% "
                        self.tree.set(iid, "progreso", bar_text)
                        
                        # Solo actualizamos tamaño y velocidad si es una descarga real (v3.16.37)
                        if not data.get("is_verifying") and not data.get("zip_verifying"):
                            self.tree.set(iid, "tamanio", f" {format_size(downloaded)} / {format_size(total)} ")
                            self.tree.set(iid, "velocidad", f" {format_size(speed)}/s " if speed > 0 else " - ")
                        else:
                            # Durante verificación, podemos ocultar la velocidad o mostrar un guión
                            self.tree.set(iid, "velocidad", " - ")
                        
                        self.tree.set(iid, "resultado", f"  {status_text}")
                        
                        # Solo guardamos progreso en disco si NO es una verificación (v3.16.35)
                        if not data.get("is_verifying") and not data.get("zip_verifying"):
                            data["downloaded"] = downloaded
                            data["filesize"] = total
                        
                        st_comp = self.get_id_text('st_completed')
                        st_err = self.get_id_text('log_error')
                        is_done = (pct >= 0.999) or (st_comp in status_text)
                        is_error = "ERROR" in status_text or st_err in status_text
                        
                        if data.get("zip_verifying", False):
                            self._update_row_tags(iid, 'zip_verifying')
                        elif data.get("is_verifying", False):
                            self._update_row_tags(iid, 'verifying')
                        elif is_done:
                            self._update_row_tags(iid, 'completed')
                        elif is_error:
                            self._update_row_tags(iid, 'failed')
                        else:
                            self._update_row_tags(iid)
                
                elif mtype == 'error':
                    iid, err_msg = msg[1], msg[2]
                    if iid in self.download_rows:
                        self.tree.set(iid, "resultado", f"  ERROR: {err_msg}")
                        self._update_row_tags(iid, 'failed')

                elif mtype == 'worker_done':
                    iid = msg[1]
                    if iid in self.running_iids: self.running_iids.remove(iid)
                    self.config["_active_count"] = len(self.running_iids)
                    self.active_speeds.pop(iid, None)
                    
                    # 🔥 AUTO-VERIFICACIÓN QUIRÚRGICA (v1.1.20260405)
                    # Solo lanzamos si el estado final es "Completado"
                    if iid in self.download_rows:
                        status_text = self.tree.set(iid, "resultado")
                        if self.get_id_text('st_completed') in status_text:
                            self._verify_single_iid(iid)
                    
                    self._check_and_launch_next()
                    self.save_session()

                elif mtype == 'multi_links_loaded':
                    grouped_data = msg[1]
                    for filename, group_data in grouped_data.items():
                        self._add_row_to_queue(filename, group_data)
                    # Carga finalizada (v1.3)
                    self.save_session()

                elif mtype == 'links_failed':
                    # Carga finalizada (v1.3)
                    PremiumMessageModal(self, self.get_id_text("msg_api_title"), msg[1], icon="error")

                elif mtype == 'verify_status':
                    iid, status_text = msg[1], msg[2]
                    if iid in self.download_rows:
                        self.download_rows[iid]["is_verifying"] = True
                        self._update_row_tags(iid, 'verifying')
                        self.tree.set(iid, "resultado", f"  {status_text}")
                
                elif mtype == 'verify_zip_status':
                    iid, status_text = msg[1], msg[2]
                    if iid in self.download_rows:
                        self.download_rows[iid]["zip_verifying"] = True
                        self._update_row_tags(iid, 'zip_verifying')
                        self.tree.set(iid, "resultado", f"  {status_text}")
                
                elif mtype == 'verify_done':
                    iid, bar_text, tag, status_txt, report = msg[1], msg[2], msg[3], msg[4], msg[5]
                    if iid in self.download_rows:
                        data = self.download_rows[iid]
                        data["is_verifying"] = False
                        data["zip_verifying"] = False 
                        data["last_report"] = report 
                        data["verified"] = (report.get('status') == "OK") # 🔥 NUEVO (Persistencia de Integridad)
                        if iid in self.verifying_iids: self.verifying_iids.remove(iid)
                        self.tree.set(iid, "progreso", bar_text)
                        self.tree.set(iid, "resultado", f"  {status_txt}")
                        self._update_row_tags(iid, tag)
                        
                        # Comprobar si todas las tareas han terminado tras una verificación
                        self._check_and_launch_next()
                        self._update_status_bar_ui()
                        
                        if self.var_show_report.get():
                            if report.get('status') == "NOT_FOUND":
                                PremiumMessageModal(self, self.get_id_text('win_verify'), self.get_id_text('msg_verify_not_found'), icon="warn")
                            else:
                                self.after(50, lambda: VerificationWindow(self, data["filename"], report, iid=iid))

        except queue.Empty: pass
        self._update_status_bar_ui()
        self.after(150, self.process_queue)

    def _on_tree_selection_changed(self, event):
        """Gestiona el resaltado azul personalizado y la consola de logs por IID."""
        selection = self.tree.selection()
        if selection:
            self.refresh_console(selection[0])

        # 2. Limpiar tag de los que ya no están seleccionados
        for iid in self.tree.tag_has('active_selection'):
            if iid not in selection:
                tags = list(self.tree.item(iid, 'tags'))
                if 'active_selection' in tags:
                    tags.remove('active_selection')
                    self.tree.item(iid, tags=tuple(tags))
        
        # 3. Poner tag a los nuevos seleccionados
        for iid in selection:
            tags = list(self.tree.item(iid, 'tags'))
            if 'active_selection' not in tags:
                tags.append('active_selection')
                self.tree.item(iid, tags=tuple(tags))

    def _update_row_tags(self, iid, tag=None, clear_all=False):
        """Asigna etiquetas de color preservando selección y checkbox (v1.1.20260402)."""
        if clear_all: 
            self.tree.item(iid, tags=())
            return
            
        current_tags = list(self.tree.item(iid, "tags"))
        
        # 1. Eliminar tags de estado previos (solo uno activo a la vez)
        for t in ['completed', 'failed', 'verifying', 'zip_verifying']:
            while t in current_tags: current_tags.remove(t)
                
        # 2. Añadir nuevo tag de estado si existe
        if tag:
            if tag not in current_tags:
                current_tags.append(tag)
        
        # 3. Asegurar persistencia de tags de persistencia visual
        if iid in self.tree.selection() and 'active_selection' not in current_tags:
            current_tags.append('active_selection')
            
        self.tree.item(iid, tags=tuple(current_tags))

    def _resubmit_link(self, iid):
        """Re-encola un archivo tras un error de red por IID."""
        if iid in self.download_rows and not self.stop_requested:
            if iid not in self.pending_iids and iid not in self.running_iids:
                self.pending_iids.append(iid)
                self._check_and_launch_next()
                
    def find_iid_by_filename(self, filename):
        """Helper para encontrar un IID por nombre (usar con cautela por duplicados)."""
        for iid, d in self.download_rows.items():
            if d["filename"] == filename: return iid
        return None

    def _add_row_to_queue(self, filename, group_data):
        """Crea e inserta o ACTUALIZA una fila mediante Agrupación Inteligente (v3.16.4)."""
        bar_text = "  [░░░░░░░░░░░░░░░░░░░░]   0% "
        
        if isinstance(group_data, dict):
            links = list(group_data.get("links", []))
            # 🔥 PRIORIDAD UI (v2.2) 🔥
            # Si el motor sugiere General pero el usuario tiene algo escrito en Destino, usamos lo del usuario.
            engine_folder = group_data.get("folder", "General")
            ui_folder = self.var_subfolder.get().strip()
            subfolder = ui_folder if (engine_folder == "General" and ui_folder) else engine_folder
        else:
            links = list(group_data)
            subfolder = self.var_subfolder.get().strip() or "General"

        # 🔥 SMART MATCHING (v3.16.4) 🔥
        # Buscamos si ya existe una fila con el mismo nombre y carpeta de destino
        target_iid = None
        for iid, d in self.download_rows.items():
            if d["filename"] == filename and d["subfolder"] == subfolder:
                target_iid = iid
                break

        if target_iid:
            # Agrupación: Añadimos nuevos links a la fila existente
            old_data = self.download_rows[target_iid]
            for l in links:
                if l not in old_data["links"]: old_data["links"].append(l)
            
            status_text = f"  {self.get_id_text('st_waiting')} ({len(old_data['links'])} hoster/s)"
            self.tree.set(target_iid, "resultado", status_text)
            return

        # Nueva Fila (Sin columna Check v1.1.20260405)
        status_text = f"  {self.get_id_text('st_waiting')} ({len(links)} hoster/s)"
        iid = self.tree.insert("", "end", values=(f"  {filename}", subfolder, bar_text, "-", "-", status_text))
        
        self.download_rows[iid] = {
            "iid": iid,
            "filename": filename,
            "links": links,
            "current_link_idx": 0,
            "subfolder": subfolder,
            "is_verifying": False,
            "verified": False,
            "repair_attempts": 0,
            "downloaded": 0,
            "filesize": 0
        }
        self.logs_dict[iid] = []
        self.active_speeds[iid] = 0
        # Registro profesional traducido (v2.2)
        self.update_queue.put(('log', iid, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_row_init')}"))
