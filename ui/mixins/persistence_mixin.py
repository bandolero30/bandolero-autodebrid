import os
import json
from core.config import CONFIG_FILE, SESSION_FILE, load_config, save_config
from core.persistence import save_session as core_save_session, load_session as core_load_session
from core.i18n import Translator
from ui.components.modals import PremiumMessageModal

class PersistenceMixin:
    """Mixin para gestionar la carga y guardado de configuración y sesiones (v1.1.20260401)."""

    def app_load_config(self):
        """Carga la configuración centralizada y sincroniza las variables de UI (v1.1.20260401)."""
        loaded_data = load_config()
        self.config.update(loaded_data)
        
        # Sincronización del motor de traducción ANTES de la UI
        lang = self.config.get("language", "es")
        Translator.set_language(lang)
        
        # Sincronización obligatoria con variables de UI
        self.var_api_key.set(self.config.get("api_key", ""))
        self.var_base_dir.set(self.config.get("base_dir", ""))
        self.var_max_workers.set(self.config.get("max_workers", 3))
        self.var_auto_retry.set(self.config.get("auto_retry", True))
        self.var_font_size.set(self.config.get("font_size", 13))
        self.var_tree_font_size.set(self.config.get("tree_font_size", 14))
        self.var_retry_delay.set(self.config.get("retry_delay", 10))
        self.var_language.set(lang)
        self.var_f95_user.set(self.config.get("f95_user", ""))
        self.var_f95_pass.set(self.config.get("f95_pass", ""))
        self.var_auto_console.set(self.config.get("auto_console", False))
        self.var_show_report.set(self.config.get("show_report", True))
        self.var_speed_limit.set(self.config.get("speed_limit_mb", 0))
        
        # Sincronización de tamaños de fuente internos
        self.sz = self.var_font_size.get()
        self.tsz = self.var_tree_font_size.get()

    def app_save_config(self):
        """Guarda la configuración centralizada leyendo los valores de las variables de la UI (v1.1.20260402)."""
        try:
            print(f"[DEBUG] Persistencia: recopilando datos de la UI...")
            # Saneamiento de entradas para evitar crashes por tipos inesperados
            self.config.update({
                "api_key": str(self.var_api_key.get()).strip(),
                "base_dir": str(self.var_base_dir.get()).strip(),
                "max_workers": int(self.var_max_workers.get() or 3),
                "auto_retry": bool(self.var_auto_retry.get()),
                "font_size": int(self.var_font_size.get() or 13),
                "tree_font_size": int(self.var_tree_font_size.get() or 14),
                "retry_delay": int(self.var_retry_delay.get() or 10),
                "language": str(self.var_language.get()).strip(),
                "f95_user": str(self.var_f95_user.get()).strip(),
                "f95_pass": str(self.var_f95_pass.get()).strip(),
                "auto_console": bool(self.var_auto_console.get()),
                "show_report": bool(self.var_show_report.get()),
                "speed_limit_mb": int(self.var_speed_limit.get() or 0)
            })
            
            # Sincronizar tamaños internos
            self.sz = self.config["font_size"]
            self.tsz = self.config["tree_font_size"]
            
            # Copia para debug anonimizada
            debug_config = self.config.copy()
            if debug_config.get("api_key"):
                debug_config["api_key"] = f"PROTECTED (len: {len(str(debug_config['api_key']))})"
            
            print(f"[DEBUG] Llamando a core.config.save_config con llaves: {list(debug_config.keys())}")
            return save_config(self.config)
        except Exception as e:
            print(f"[ERROR] Fallo crítico en app_save_config: {e}")
            return False

    def on_click_save_config(self):
        """Acción del botón manual con mensaje Premium centralizado (v4.3)."""
        if self.app_save_config():
            PremiumMessageModal(self, self.get_id_text("msg_opt_title"), self.get_id_text("msg_opt_save_ok"), icon="success")

    def save_session(self):
        """Sincroniza y guarda la sesión actual por IID (v3.16.9)."""
        session_data = {
            "subfolder": self.var_subfolder.get(),
            "source_paths": getattr(self, '_selected_dlc_paths', []),
            "files": []
        }
        # download_rows ahora está indexado por iid
        for iid, data in self.download_rows.items():
            if not (hasattr(self, 'tree') and iid and self.tree.exists(iid)): continue
            
            status_text = self.tree.set(iid, "resultado")
            session_data["files"].append({
                "filename": data["filename"],
                "links": data["links"],
                "subfolder": data.get("subfolder", self.var_subfolder.get().strip()),
                "filesize": data.get("filesize", 0),
                "downloaded": data.get("downloaded", 0),
                "resultado": status_text,
                "last_report": data.get("last_report"),
                "verified": data.get("verified", False)
            })
        core_save_session(SESSION_FILE, session_data)

    def load_session(self):
        """Carga la sesión desde el archivo JSON y restaura el Treeview."""
        data = core_load_session(SESSION_FILE)
        if not data: return
        
        if "subfolder" in data: self.var_subfolder.set(data["subfolder"])
        if "source_paths" in data:
            self._selected_dlc_paths = data["source_paths"]
            count = len(self._selected_dlc_paths)
            if count == 1: self.dlc_path.set(self._selected_dlc_paths[0])
            elif count > 1: self.dlc_path.set(f"{count} {self.get_id_text('msg_files_sel')}")
            
        files = data.get("files", [])
        for f_data in files:
            filename = f_data["filename"]
            links = f_data["links"]
            subfolder = f_data.get("subfolder", self.var_subfolder.get().strip())
            raw_status = f_data.get("resultado", f"  {self.get_id_text('st_manual_stop')}")
            
            # Saneamiento de enlaces (v1.1.20260401 Healing)
            # Filtramos links que no sean URLs reales (elimina "links" o "folder" corruptos)
            sanitized_links = [lk for lk in links if isinstance(lk, str) and lk.startswith("http")]
            if not sanitized_links:
                print(f"[WARNING] Sesión: {filename} no tiene enlaces válidos. Se marcará para re-carga.")
                status = f"  [Sesión Corrupta - Re-cargar DLC]"
                tag = ("failed",)
            else:
                links = sanitized_links
                if "OK" not in raw_status and "Completado" not in raw_status and "ERROR" not in raw_status and "Finalizado" not in raw_status:
                    status = f"  {self.get_id_text('st_manual_stop')}"
                else: 
                    status = raw_status

                tag = ()
                if "OK" in status or "Completado" in status or "Finalizado" in status: 
                    tag = ("completed",)
                elif "ERROR" in status: 
                    tag = ("failed",)
                elif "Verificando" in status:
                    # v1.1.20260401: No restaurar estado de verificación al inicio
                    status = f"  {self.get_id_text('st_manual_stop')}"
                    tag = ()
            
            if hasattr(self, 'tree'):
                # Calcular progreso inicial basado en sesión (v3.12)
                rem_size = f_data.get("filesize", 0)
                loc_size = f_data.get("downloaded", 0)
                pct = (loc_size / rem_size) if rem_size > 0 else 0
                
                # Saneamiento visual (si terminó, forzar 100%)
                if "OK" in status or "Finalizado" in status or "Completado" in status: pct = 1.0
                
                filled = int(pct * 20)
                bar_text = f"  [{'▓' * filled}{'░' * (20 - filled)}] {int(pct * 100):3d}% "
                
                from core.engine import format_size
                sz_str = f" {format_size(loc_size)} / {format_size(rem_size)} " if rem_size > 0 else "-"
                
                # REHIDRATACIÓN IID (v3.16.9)
                iid = self.tree.insert("", "end", values=(f"  {filename}", subfolder, bar_text, sz_str, "-", status), tags=tag)
                
                self.download_rows[iid] = {
                    "iid": iid,
                    "filename": filename,
                    "links": links,
                    "current_link_idx": 0,
                    "subfolder": subfolder,
                    "filesize": rem_size,
                    "downloaded": loc_size,
                    "is_verifying": False,
                    "last_report": f_data.get("last_report"),
                    "verified": f_data.get("verified", False)
                }
                # No necesitamos iid_to_link ya que iid es la KEY directa de download_rows
                self.logs_dict[iid] = []
                self.active_speeds[iid] = 0

        if files and hasattr(self, 'btn_start'):
            self.btn_start.configure(state="normal")
