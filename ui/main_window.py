import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
import queue

# IMPORTACIONES MODULARES (v1.1.20260401)
from core.config import __version__, FONT_FAMILY
from core.i18n import Translator
from utils.helpers import resource_path

# MODULARIZACIÓN (v1.1.20260401)
from ui.mixins.persistence_mixin import PersistenceMixin
from ui.mixins.download_mixin import DownloadMixin
from ui.mixins.ui_mixin import UIMixin
from ui.components.banner_component import BannerFrame
from ui.tabs.queue_tab import QueueTab
from ui.tabs.options_tab import OptionsTab

class DownloaderApp(ctk.CTk, PersistenceMixin, DownloadMixin, UIMixin):
    """Orquestador principal de la UI de Bandolero AutoDebrid (v1.1.20260401)."""

    def __init__(self):
        super().__init__()
        
        # 0. Ocultar ventana principal durante la construcción para un renderizado limpio
        self.withdraw()
            
        self.title(f"Bandolero AutoDebrid - Pro Downloader v{__version__}")
        self.geometry("1400x850")
        self.active_context_menu = None
        
        # Icono de la ventana (v1.1.20260402)
        try:
            icon_path = resource_path("resources/app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"[DEBUG] No se pudo cargar el icono .ico: {e}")
        
        # Setup básico de variables de estado
        self._init_vars()
        self.app_load_config()
        
        # Sincronizar estado inicial de consola antes de construir UI
        self.console_visible = self.var_auto_console.get()
        
        # Construir UI modular
        self._build_ui()
        self.load_session()
        
        # Sincronizar textos finales del idioma cargado (v1.1.20260401)
        self.refresh_ui_texts()
        
        # Finalización: Cerrar Splash Nativo (PyInstaller) y mostrar App
        try:
            import pyi_splash
            pyi_splash.close()
        except ImportError:
            pass

        self.after(200, lambda: (self.deiconify(), self.lift(), self.focus_force()))
        
        # Auto-selección del primer archivo al iniciar (v1.1.20260403) - Delay reducido para evitar efecto macro
        self.after(50, self._auto_select_first_item)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Nota: La apertura de consola ahora es nativa en _build_ui/refresh_texts
            
        self.after(150, self.process_queue)

    def _init_vars(self):
        """Inicializa las variables internas y de control."""
        self.config = {
            "api_key": "", "base_dir": r"C:\Descargas", "max_workers": 3,
            "auto_retry": True, "font_size": 13, "tree_font_size": 14,
            "retry_delay": 10, "language": "es", "auto_console": False,
            "speed_limit_mb": 0
        }
        self.dlc_path = ctk.StringVar(value="")
        self._selected_dlc_paths = []
        self._sort_reverse = False
        
        self.var_api_key = ctk.StringVar()
        self.var_base_dir = ctk.StringVar()
        self.var_max_workers = ctk.IntVar()
        self.var_auto_retry = ctk.BooleanVar()
        self.var_font_size = ctk.IntVar()
        self.var_tree_font_size = ctk.IntVar()
        self.var_retry_delay = ctk.IntVar()
        self.var_language = ctk.StringVar()
        self.var_f95_user = ctk.StringVar()
        self.var_f95_pass = ctk.StringVar()
        self.var_auto_console = ctk.BooleanVar()
        self.var_show_report = ctk.BooleanVar(value=True)
        self.var_subfolder = ctk.StringVar()
        self.var_speed_limit = ctk.IntVar(value=0)
        
        self.sz = 13 
        self.tsz = 14
        
        self.update_queue = queue.Queue()
        self.download_rows = {}
        self.running_iids = set()
        self.verifying_iids = set()
        self.active_speeds = {}
        self.logs_dict = {}
        self.stopped_iids = set()
        self.force_rotate = set()
        self.pending_iids = []
        self.console_visible = False
        self.is_downloading = False
        self.stop_requested = False
        
        # Variables de hover para evitar AttributeError (v1.1.20260401)
        self._hover_job = None
        self._hover_win = None
        self._hover_iid = None

        self.COL_WIDTHS = {
            "archivo":   {"width": 300, "minwidth": 140, "stretch": True},
            "carpeta":   {"width": 100, "minwidth": 100, "stretch": True},
            "progreso":  {"width": 550, "minwidth": 550, "stretch": False},
            "tamanio":   {"width": 140, "minwidth": 140, "stretch": False},
            "velocidad": {"width": 140, "minwidth": 140, "stretch": False},
            "resultado": {"width": 550, "minwidth": 550, "stretch": False},
        }

    def _auto_select_first_item(self):
        """Selecciona visualmente el primer elemento de la tabla al iniciar (v1.1.20260403)."""
        if hasattr(self, 'tree'):
            children = self.tree.get_children()
            if children:
                first_iid = children[0]
                self.tree.selection_set(first_iid)
                self.tree.focus(first_iid)
                self.tree.see(first_iid)
                print(f"[DEBUG] UI: Auto-seleccionado primer archivo ({first_iid})")

    def _build_ui(self):
        """Ensambla los componentes modulares en la ventana principal."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Banner
        self.header = BannerFrame(self)
        self.header.pack(fill="x", side="top")

        # 2. Barra de Estado (Empaquetada antes para reservar espacio v1.1.20260402)
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color="#1a1c23", corner_radius=0)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False) # Evitar que el contenido cambie su alto
        
        self.lbl_queue_stats = ctk.CTkLabel(self.status_bar, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=11))
        self.lbl_queue_stats.pack(side="left", padx=20)

        self.lbl_total_speed = ctk.CTkLabel(self.status_bar, text="Total Speed: 0.00 B/s", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color="#00f2ff")
        self.lbl_total_speed.pack(side="right", padx=20)

        self.lbl_threads = ctk.CTkLabel(self.status_bar, text="Threads: 0", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color="#00f2ff")
        self.lbl_threads.pack(side="right", padx=20)

        # 3. TabView Principal (Restaurado v1.1.20260401)
        self.tabview = ctk.CTkTabview(self, segmented_button_fg_color="#1a1c23", segmented_button_selected_color="#1f538d", text_color="white", corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # 🔥 Ajuste de altura y diseño de pestañas (v1.1.20260401)
        self.tabview._segmented_button.configure(height=45, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz+2, weight="bold"))
        
        self._tab_dl_id = " " + self.get_id_text("tab_dl")
        self._tab_opt_id = " " + self.get_id_text("tab_opt")
        
        tab_queue = self.tabview.add(self._tab_dl_id)
        tab_options = self.tabview.add(self._tab_opt_id)

        self.queue_tab = QueueTab(tab_queue, self)
        self.queue_tab.pack(fill="both", expand=True)
        
        # Alias para compatibilidad con mixins
        self.tree = self.queue_tab.tree
        self.btn_start = self.queue_tab.btn_start

        self.opt_tab = OptionsTab(tab_options, self)
        self.opt_tab.pack(fill="both", expand=True)
        
        self._apply_treeview_style()

    def _on_lang_change(self, lang_code):
        """Orquesta la actualización de textos en todos los componentes modulares (v1.1.20260401)."""
        from core.i18n import Translator
        Translator.set_language(lang_code)
        
        self.var_language.set(lang_code)
        self.config["language"] = lang_code
        self.app_save_config()  # Corregido: app_save_config es el nombre correcto del mixin
        self.refresh_ui_texts() # Nuevo: Forzar refresco de textos en UI
        
        try:
            self.tabview._segmented_button._buttons_dict[self._tab_dl_id].configure(text=self.get_id_text("tab_dl"))
            self.tabview._segmented_button._buttons_dict[self._tab_opt_id].configure(text=self.get_id_text("tab_opt"))
        except: pass
        
        if hasattr(self.header, 'refresh_texts'): self.header.refresh_texts()
        self.queue_tab.refresh_texts()
        self.opt_tab.refresh_texts()
        self._update_status_bar_ui()
        self.title(f"Bandolero AutoDebrid - Pro Downloader v{__version__}")
        self.process_queue()

    def on_closing(self):
        """Cierre seguro del programa."""
        try:
            self.stop_requested = True
            self.save_session()
            self.app_save_config()
        except Exception as e:
            print(f"[DEBUG] Error al cerrar (ignorando para forzar salida): {e}")
        finally:
            self.destroy()
            sys.exit(0)

    def refresh_ui_texts(self):
        """Refresca todos los textos de la aplicación (v1.1.20260401)."""
        # 1. Refrescar Tabs
        if hasattr(self, "queue_tab"): self.queue_tab.refresh_texts()
        if hasattr(self, "options_tab"): self.options_tab.refresh_texts()
        
        # 2. Refrescar contador de archivos (v1.1.20260402)
        if hasattr(self, "refresh_dlc_path_text"): self.refresh_dlc_path_text()
        
        # 2. Refrescar Barra de Estado y otros elementos fixos
        self._update_status_bar_ui()
        
    def get_id_text(self, key):
        return Translator.get(key)

    def _apply_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        rh = int(self.tsz * 2 + 10)
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        rowheight=rh,
                        fieldbackground="#2b2b2b", 
                        borderwidth=0, 
                        font=(FONT_FAMILY, self.tsz)) # Usar cadena simple aquí
        
        style.map('Treeview', background=[], foreground=[])
        
        # Tags de estado y selección definitivos (v1.1.20260402)
        self.tree.tag_configure('active_selection', background="#1f538d")  # El azul de selección manual
        self.tree.tag_configure('verifying', foreground="#FFD700")         # Oro
        self.tree.tag_configure('zip_verifying', foreground="#e67e22")     # Naranja (Estructura ZIP)
        self.tree.tag_configure('completed', foreground="#2da44e")         # Verde
        self.tree.tag_configure('failed', foreground="#e5534b")            # Rojo
        self.tree.tag_configure('bulk_selected', background="#3d424b")     # (Alias por si acaso)        
        style.configure("Treeview.Heading", 
                        background="#333333", 
                        foreground="white", 
                        relief="flat", 
                        font=(FONT_FAMILY, self.tsz, "bold"))  # Usar cadena simple aquí
        style.map("Treeview.Heading", background=[('active', '#444444')])

    def _update_action_buttons_ui(self, is_downloading):
        if hasattr(self, 'queue_tab'):
            self.queue_tab._update_action_buttons_ui(is_downloading)

    def _bind_tooltip(self, widget, title_key, msg_key):
        def start_timer(event): self._tooltip_job = self.after(500, lambda: self._create_tooltip(widget, title_key, msg_key))
        def cancel_timer(event):
            if hasattr(self, "_tooltip_job"): self.after_cancel(self._tooltip_job)
            if hasattr(self, "_active_tooltip"): self._active_tooltip.destroy(); del self._active_tooltip
        widget.bind("<Enter>", start_timer); widget.bind("<Leave>", cancel_timer)

    def _create_tooltip(self, widget, t_key, m_key):
        from ui.components.tooltips import SimpleTooltip
        if hasattr(self, "_active_tooltip"): return
        x, y = widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height() + 5
        self._active_tooltip = SimpleTooltip(self, self.get_id_text(t_key), self.get_id_text(m_key), x, y)

# Eliminado: Ejecución directa (Usar main.py)
