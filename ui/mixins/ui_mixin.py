import os
import threading
from tkinter import filedialog
from core.engine import extract_multi_dlc_worker, extract_links_from_text_worker
from ui.components.widgets import ModernContextMenu
from ui.components.tooltips import FileDetailsTooltip
from ui.components.modals import LinksInputWindow, PremiumMessageModal
from utils.helpers import format_size

class UIMixin:
    """Mixin para gestionar eventos e interacciones de la interfaz (v1.1.20260401)."""

    def browse_dlc(self):
        """Selecciona uno o varios archivos DLC y los carga automáticamente (v1.2)."""
        paths = filedialog.askopenfilenames(filetypes=[("Container Files", "*.dlc;*.txt")])
        if paths:
            self._selected_dlc_paths = list(paths)
            if len(paths) == 1:
                self.dlc_path.set(paths[0])
            else:
                self.dlc_path.set(f"{len(paths)} {self.get_id_text('msg_files_sel')}")
            # Inicio automático de la carga tras cerrar el diálogo de archivos (v1.2)
            self.load_dlc_links()
 
    def refresh_dlc_path_text(self):
        """Actualiza el texto del campo de origen según el idioma actual (v1.1.20260402)."""
        if hasattr(self, '_selected_dlc_paths') and self._selected_dlc_paths:
            count = len(self._selected_dlc_paths)
            if count > 1:
                self.dlc_path.set(f"{count} {self.get_id_text('msg_files_sel')}")
            elif count == 1:
                # Si solo hay uno, mantenemos el path (no necesita traducción)
                self.dlc_path.set(self._selected_dlc_paths[0])

    def load_dlc_links(self):
        """Dispara el worker de extracción de enlaces de forma silenciosa (v1.3)."""
        if not self._selected_dlc_paths: return
        threading.Thread(target=extract_multi_dlc_worker, args=(self._selected_dlc_paths, self.update_queue, self.get_id_text), daemon=True).start()

    def open_add_links_window(self):
         """Abre el modal para pegar enlaces manuales (v1.1.20260402)."""
         LinksInputWindow(self, self.process_pasted_links_callback)

    def process_pasted_links_callback(self, grouped_data):
        """Recibe los datos ya agrupados y editados desde el modal y los carga a la cola (v2.0.20260405)."""
        if not grouped_data: return
        self.update_queue.put(('multi_links_loaded', grouped_data))

    def _sort_column(self, col):
        """Ordenación interactiva de la tabla con indicadores visuales (v2.3)."""
        # 1. Resetear todos los encabezados a su estado base traducido
        cw = self.COL_WIDTHS
        for c in cw:
            text_key = f"col_{'status' if c=='resultado' else 'file' if c=='archivo' else 'progress' if c=='progreso' else 'size' if c=='tamanio' else 'speed' if c=='velocidad' else 'folder' if c=='carpeta' else c}"
            self.tree.heading(c, text=self.get_id_text(text_key))

        # 2. Ordenar datos
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=self._sort_reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # 3. Aplicar indicador a la columna activa
        arrow = " ▲" if not self._sort_reverse else " ▼"
        old_text = self.tree.heading(col, "text")
        self.tree.heading(col, text=f"{old_text}{arrow}")

        # 4. Toggle para la siguiente pulsación
        self._sort_reverse = not self._sort_reverse

    def apply_folder_to_selected(self):
        """Aplica la subcarpeta destino a los archivos seleccionados en azul."""
        selection = self.tree.selection()
        if not selection:
            PremiumMessageModal(self, self.get_id_text("msg_api_title"), self.get_id_text("msg_no_links"), icon="info")
            return
            
        new_folder = self.var_subfolder.get().strip()
        count = 0
        for iid in selection:
            if iid in self.download_rows:
                data = self.download_rows[iid]
                data["subfolder"] = new_folder
                self.tree.set(iid, "carpeta", new_folder)
                count += 1
        if count > 0:
            self.update_queue.put(('log', 'Global', f"[SYS] Carpeta '{new_folder}' aplicada a {count} archivos."))

    def toggle_console(self):
        """Muestra/Oculta la consola de logs."""
        self.console_visible = not self.console_visible
        if self.console_visible:
            self.queue_tab.log_container.pack(side="bottom", fill="x", padx=5, pady=5)
            self.queue_tab.btn_toggle_log.configure(text=f"▲ {self.get_id_text('btn_hide_log')}")
        else:
            self.queue_tab.log_container.pack_forget()
            self.queue_tab.btn_toggle_log.configure(text=f"▼ {self.get_id_text('btn_show_log')}")

    def show_context_menu(self, event):
        """Despliega el menú contextual premium basado en IID (v3.16.11)."""
        iid = self.tree.identify_row(event.y)
        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
            
            row_data = self.download_rows.get(iid, {})
            filename = row_data.get("filename", "Unknown")
            
            options = [
                (f"▶ {self.get_id_text('ctx_start_f')}", self._start_selected_file),
                (f"⏸ {self.get_id_text('ctx_stop_f')}", self._stop_selected_file),
                ("---", None),
                (f"📋 {self.get_id_text('ctx_copy_n')} {filename[:25]}...", lambda: self.clipboard_clear() or self.clipboard_append(filename)),
                (f"📂 {self.get_id_text('ctx_open_f')}", self.open_selected_folder),
                (f"📁 {self.get_id_text('ctx_change_folder')}", self.apply_folder_to_selected),
                ("---", None),
                (f"🔍 {self.get_id_text('ctx_verify_f')}", self.verify_selected_file),
                (f"📄 {self.get_id_text('ctx_report')}", self.show_technical_report),
                (f"🧹 {self.get_id_text('ctx_clean_completed')}", self.clean_completed_files),
                (f"🛠 {self.get_id_text('ctx_resume_f')}", self.smart_repair_selected),
                ("---", None),
                (f"🔄 {self.get_id_text('ctx_rotate_f')}", self.rotate_selected_link),
                (f"❌ {self.get_id_text('ctx_remove_f')}", self.remove_selected_link),
            ]
            
            if self.active_context_menu: self.active_context_menu.destroy()
            self.active_context_menu = ModernContextMenu(self, options, font_sz=self.sz)
            self.active_context_menu.show(event.x_root, event.y_root)

    def open_selected_folder(self, event=None):
        """Abre la carpeta de destino en el explorador de Windows por IID."""
        selection = self.tree.selection()
        if not selection: return
        iid = selection[0]
        
        if iid in self.download_rows:
            data = self.download_rows[iid]
            sub = data.get("subfolder", "").strip()
            filename = data["filename"]
        else:
            sub = self.var_subfolder.get().strip()
            filename = "Unknown"
            
        final_dir = os.path.normpath(os.path.join(self.config["base_dir"], sub))
        
        if os.path.exists(final_dir):
            os.startfile(final_dir)
        else:
            self.update_queue.put(('log', iid, f"[SYS] {self.get_id_text('msg_api_title')}: {final_dir} no existe todavía."))

    def remove_selected_links(self):
        """Elimina de la lista los archivos seleccionados en azul."""
        selection = self.tree.selection()
        if not selection: return
        
        for iid in list(selection):
            if iid in self.download_rows: del self.download_rows[iid]
            if iid in self.logs_dict: del self.logs_dict[iid]
            if self.tree.exists(iid): self.tree.delete(iid)
            self.update_queue.put(('log', 'Global', f"[SYS] {self.get_id_text('msg_removed')}"))
        
        self._update_status_bar_ui()
        self.save_session()

    def remove_selected_link(self):
        """Alias para el menú contextual: Elimina las filas seleccionadas en azul por IID."""
        selection = self.tree.selection()
        if not selection: return
        for iid in selection:
            if iid in self.download_rows: del self.download_rows[iid]
            if iid in self.logs_dict: del self.logs_dict[iid]
            if self.tree.exists(iid): self.tree.delete(iid)
        self._update_status_bar_ui()
        self.save_session()


    def _on_tree_motion(self, event):
        """Gestiona el sistema de tooltips dinámicos por IID."""
        iid = self.tree.identify_row(event.y)
        if iid != self._hover_iid:
            self._hide_file_tooltip()
            self._hover_iid = iid
            if iid:
                if iid in self.download_rows:
                    self._hover_job = self.after(3000, lambda: self._show_file_tooltip(event, iid))

    def _show_file_tooltip(self, event, iid):
        """Muestra detalles del archivo en una ventana flotante por IID."""
        data = self.download_rows[iid]
        self._hover_win = FileDetailsTooltip(self, data["filename"], data, event.x_root, event.y_root)

    def _hide_file_tooltip(self):
        """Cierra el tooltip activo."""
        if self._hover_job: self.after_cancel(self._hover_job); self._hover_job = None
        if self._hover_win: self._hover_win.destroy(); self._hover_win = None
        self._hover_iid = None

    def refresh_console(self, iid):
        """Delega la actualización de la consola al componente correspondiente por IID."""
        if hasattr(self, 'queue_tab'):
            self.queue_tab.refresh_console(iid)

    def _update_status_bar_ui(self):
        """Actualiza el pie de página con estadísticas en tiempo real por IID."""
        total_speed = sum(self.active_speeds.values()) if hasattr(self, 'active_speeds') else 0
        tot_str = f"{format_size(total_speed)}/s"
        prefix_speed = self.get_id_text("lbl_status_total")
        self.lbl_total_speed.configure(text=f"{prefix_speed} {tot_str}")
        
        # Conteo de hilos (Descargas + Verificaciones)
        active_threads = (len(self.running_iids) if hasattr(self, 'running_iids') else 0) + \
                         (len(self.verifying_iids) if hasattr(self, 'verifying_iids') else 0)
        prefix_threads = self.get_id_text("lbl_status_threads")
        if hasattr(self, 'lbl_threads'):
            self.lbl_threads.configure(text=f"{prefix_threads} {active_threads}")
        
        running_count = len(self.running_iids) if hasattr(self, 'running_iids') else 0
        done = sum(1 for iid in self.download_rows.keys() if "✅" in self.tree.set(iid, "resultado"))
        
        txt = f"{self.get_id_text('lbl_status_files')} {len(self.download_rows)} | " \
              f"{self.get_id_text('lbl_status_active')} {running_count} | " \
              f"{self.get_id_text('lbl_status_done')} {done}"
        if hasattr(self, 'lbl_queue_stats'): self.lbl_queue_stats.configure(text=txt)

    def browse_base_dir(self):
        """Selecciona el directorio base para las descargas."""
        path = filedialog.askdirectory(initialdir=self.var_base_dir.get())
        if path:
            self.var_base_dir.set(os.path.normpath(path))

    def _animate_watermark(self):
        """Animación sutil decorativa."""
        pass # Por ahora estática
