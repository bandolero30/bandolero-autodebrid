import threading
import requests
import customtkinter as ctk
from core.config import FONT_FAMILY
from ui.components.widgets import PremiumLanguageSelector
from ui.components.modals import PremiumMessageModal

class OptionsTab(ctk.CTkFrame):
    """Pestaña de opciones modularizada (v1.1.20260401)."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def refresh_texts(self):
        """Actualiza todos los textos de la pestaña según el idioma actual (v1.1.20260401)."""
        self.lbl_opt_ui_title.configure(text=self.app.get_id_text("opt_ui_title"))
        self.lbl_opt_lang.configure(text=self.app.get_id_text("opt_lang"))
        self.lbl_opt_gui_size.configure(text=self.app.get_id_text("opt_gui_size"))
        self.lbl_opt_cell_size.configure(text=self.app.get_id_text("opt_cell_size"))
        self.lbl_opt_api_title.configure(text=self.app.get_id_text("opt_api_title"))
        self.lbl_opt_api_desc.configure(text=self.app.get_id_text("opt_api_desc"))
        self.btn_test_api.configure(text=self.app.get_id_text("opt_test"))
        self.lbl_opt_dir_title.configure(text=self.app.get_id_text("opt_dir_title"))
        self.lbl_opt_dir_desc.configure(text=self.app.get_id_text("opt_dir_desc"))
        self.btn_browse_conf.configure(text=self.app.get_id_text("btn_browse"))
        self.btn_save_config.configure(text=self.app.get_id_text("opt_save"))
        
        # Avanzado
        self.lbl_opt_adv_title.configure(text=self.app.get_id_text("opt_adv_title"))
        self.lbl_opt_sim_dl.configure(text=self.app.get_id_text("opt_sim_dl"))
        self.chk_retry.configure(text=self.app.get_id_text("opt_retry_chk"))
        self.lbl_opt_retry_sec.configure(text=self.app.get_id_text("opt_retry_sec"))
        self.chk_auto_console.configure(text=self.app.get_id_text("opt_auto_console"))
        self.chk_show_report.configure(text=self.app.get_id_text("opt_show_report"))
        self.lbl_opt_speed_limit.configure(text=self.app.get_id_text("opt_speed_limit"))

        # f95zone
        self.lbl_opt_f95_title.configure(text=self.app.get_id_text("opt_f95_title"))
        self.lbl_opt_f95_desc.configure(text=self.app.get_id_text("opt_f95_desc"))
        self.lbl_f95_u.configure(text=self.app.get_id_text("opt_f95_user"))
        self.lbl_f95_p.configure(text=self.app.get_id_text("opt_f95_pass"))
        self.btn_test_f95.configure(text=self.app.get_id_text("opt_f95_test"))

    def _build_ui(self):
        # ── Sistema de Diseño UX v2.1 ──
        CARD_IPAD = 16          # Padding interno de tarjetas
        CARD_GAP = 20           # Espacio vertical entre tarjetas
        OUTER_PAD = 24          # Márgenes exteriores
        ROW_GAP = 8             # Espacio entre filas dentro de tarjetas
        LBL_W = 160             # Ancho fijo de etiquetas para alineación
        TITLE_SZ = int(self.app.sz + 1)
        DESC_SZ  = int(self.app.sz - 2)
        BASE_SZ  = self.app.sz
        CARD_BG  = ("#e8eaed", "#1a1c23")
        CARD_R   = 10           # Corner radius

        # ── Botón de guardado fijo en la base ──
        self.bottom_bar = ctk.CTkFrame(self, height=64, fg_color="transparent")
        self.bottom_bar.pack(side="bottom", fill="x", padx=OUTER_PAD*2, pady=(8, 16))
        self.btn_save_config = ctk.CTkButton(
            self.bottom_bar, text=self.app.get_id_text("opt_save"),
            width=240, height=40, corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold"),
            fg_color="#1f538d", hover_color="#14375e",
            command=self.app.on_click_save_config)
        self.btn_save_config.pack(expand=True)

        # ── Área de scroll ──
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(side="top", fill="both", expand=True, padx=OUTER_PAD, pady=(OUTER_PAD, 0))

        # ── Grid de 2 columnas ──
        self.grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=8)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)
        self.grid_frame.grid_rowconfigure(0, weight=1)

        # ══════════════════════════════════════════════
        # COLUMNA IZQUIERDA — Credenciales y Cuentas
        # ══════════════════════════════════════════════
        col_left = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        col_left.grid(row=0, column=0, sticky="new", padx=(0, 10))

        # ── 1. API Key Real-Debrid ──
        rd_card = ctk.CTkFrame(col_left, fg_color=CARD_BG, corner_radius=CARD_R)
        rd_card.pack(fill="x", pady=(0, CARD_GAP))

        self.lbl_opt_api_title = ctk.CTkLabel(
            rd_card, text=self.app.get_id_text('opt_api_title'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=TITLE_SZ, weight="bold"))
        self.lbl_opt_api_title.pack(anchor="w", padx=CARD_IPAD, pady=(CARD_IPAD, 2))

        self.lbl_opt_api_desc = ctk.CTkLabel(
            rd_card, text=self.app.get_id_text("opt_api_desc"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=DESC_SZ), text_color="gray")
        self.lbl_opt_api_desc.pack(anchor="w", padx=CARD_IPAD, pady=(0, 12))

        rd_row = ctk.CTkFrame(rd_card, fg_color="transparent")
        rd_row.pack(fill="x", padx=CARD_IPAD, pady=(0, CARD_IPAD))
        rd_row.columnconfigure(0, weight=1)

        ctk.CTkEntry(rd_row, textvariable=self.app.var_api_key, height=34,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), show="*"
                     ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_test_api = ctk.CTkButton(
            rd_row, text=self.app.get_id_text("opt_test"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold"),
            width=88, height=34, fg_color="#333", hover_color="#444",
            command=self.test_api_key)
        self.btn_test_api.grid(row=0, column=1)

        # ── 2. Interfaz Visual ──
        ui_card = ctk.CTkFrame(col_left, fg_color=CARD_BG, corner_radius=CARD_R)
        ui_card.pack(fill="x", pady=(0, CARD_GAP))

        self.lbl_opt_ui_title = ctk.CTkLabel(
            ui_card, text=self.app.get_id_text('opt_ui_title'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=TITLE_SZ, weight="bold"))
        self.lbl_opt_ui_title.pack(anchor="w", padx=CARD_IPAD, pady=(CARD_IPAD, 10))

        ui_grid = ctk.CTkFrame(ui_card, fg_color="transparent")
        ui_grid.pack(fill="x", padx=CARD_IPAD, pady=(0, CARD_IPAD))
        ui_grid.columnconfigure(1, weight=1)

        self.lbl_opt_lang = ctk.CTkLabel(
            ui_grid, text=self.app.get_id_text("opt_lang"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W, anchor="w")
        self.lbl_opt_lang.grid(row=0, column=0, pady=ROW_GAP, sticky="w")
        self.premium_lang = PremiumLanguageSelector(ui_grid, self.app.var_language.get(), command=self.app._on_lang_change)
        self.premium_lang.grid(row=0, column=1, pady=ROW_GAP, sticky="w")

        self.lbl_opt_gui_size = ctk.CTkLabel(
            ui_grid, text=self.app.get_id_text("opt_gui_size"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W, anchor="w")
        self.lbl_opt_gui_size.grid(row=1, column=0, pady=ROW_GAP, sticky="w")
        ctk.CTkSlider(ui_grid, from_=10, to=24, number_of_steps=14, 
                      variable=self.app.var_font_size, width=180
                      ).grid(row=1, column=1, pady=ROW_GAP, sticky="w")
        ctk.CTkLabel(ui_grid, textvariable=self.app.var_font_size, width=32,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold")
                     ).grid(row=1, column=2, pady=ROW_GAP)

        self.lbl_opt_cell_size = ctk.CTkLabel(
            ui_grid, text=self.app.get_id_text("opt_cell_size"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W, anchor="w")
        self.lbl_opt_cell_size.grid(row=2, column=0, pady=ROW_GAP, sticky="w")
        ctk.CTkSlider(ui_grid, from_=10, to=30, number_of_steps=20,
                      variable=self.app.var_tree_font_size, width=180
                      ).grid(row=2, column=1, pady=ROW_GAP, sticky="w")
        ctk.CTkLabel(ui_grid, textvariable=self.app.var_tree_font_size, width=32,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold")
                     ).grid(row=2, column=2, pady=ROW_GAP)

        self.chk_auto_console = ctk.CTkCheckBox(
            ui_grid, text=self.app.get_id_text("opt_auto_console"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ),
            variable=self.app.var_auto_console)
        self.chk_auto_console.grid(row=3, column=0, columnspan=2, pady=(ROW_GAP, 0), sticky="w")
        
        self.chk_show_report = ctk.CTkCheckBox(
            ui_grid, text=self.app.get_id_text("opt_show_report"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ),
            variable=self.app.var_show_report)
        self.chk_show_report.grid(row=4, column=0, columnspan=2, pady=(ROW_GAP, 0), sticky="w")

        # ══════════════════════════════════════════════
        # COLUMNA DERECHA — Rutas, Motor y Cuentas
        # ══════════════════════════════════════════════
        col_right = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        col_right.grid(row=0, column=1, sticky="new", padx=(10, 0))

        # ── 1. Directorio Base de Descargas ──
        dir_card = ctk.CTkFrame(col_right, fg_color=CARD_BG, corner_radius=CARD_R)
        dir_card.pack(fill="x", pady=(0, CARD_GAP))

        self.lbl_opt_dir_title = ctk.CTkLabel(
            dir_card, text=self.app.get_id_text('opt_dir_title'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=TITLE_SZ, weight="bold"))
        self.lbl_opt_dir_title.pack(anchor="w", padx=CARD_IPAD, pady=(CARD_IPAD, 2))

        self.lbl_opt_dir_desc = ctk.CTkLabel(
            dir_card, text=self.app.get_id_text("opt_dir_desc"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=DESC_SZ), text_color="gray")
        self.lbl_opt_dir_desc.pack(anchor="w", padx=CARD_IPAD, pady=(0, 10))

        dir_row = ctk.CTkFrame(dir_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=CARD_IPAD, pady=(0, CARD_IPAD))
        ctk.CTkEntry(dir_row, textvariable=self.app.var_base_dir, height=34,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ)
                     ).pack(side="left", padx=(0, 8), fill="x", expand=True)
        self.btn_browse_conf = ctk.CTkButton(
            dir_row, text=self.app.get_id_text("btn_browse"),
            width=100, height=34, corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ),
            fg_color="#444", hover_color="#555",
            command=self.app.browse_base_dir)
        self.btn_browse_conf.pack(side="left")

        # ── 2. Avanzado (Motor Multihilo) ──
        adv_card = ctk.CTkFrame(col_right, fg_color=CARD_BG, corner_radius=CARD_R)
        adv_card.pack(fill="x", pady=(0, CARD_GAP))

        self.lbl_opt_adv_title = ctk.CTkLabel(
            adv_card, text=self.app.get_id_text('opt_adv_title'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=TITLE_SZ, weight="bold"))
        self.lbl_opt_adv_title.pack(anchor="w", padx=CARD_IPAD, pady=(CARD_IPAD, 10))

        adv_grid = ctk.CTkFrame(adv_card, fg_color="transparent")
        adv_grid.pack(fill="x", padx=CARD_IPAD, pady=(0, CARD_IPAD))
        adv_grid.columnconfigure(1, weight=1)

        self.lbl_opt_sim_dl = ctk.CTkLabel(
            adv_grid, text=self.app.get_id_text("opt_sim_dl"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W, anchor="w")
        self.lbl_opt_sim_dl.grid(row=0, column=0, pady=ROW_GAP, sticky="w")
        ctk.CTkSlider(adv_grid, from_=1, to=10, number_of_steps=9,
                      variable=self.app.var_max_workers, width=180
                      ).grid(row=0, column=1, pady=ROW_GAP, sticky="w")
        ctk.CTkLabel(adv_grid, textvariable=self.app.var_max_workers, width=32,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold")
                     ).grid(row=0, column=2, pady=ROW_GAP)

        self.chk_retry = ctk.CTkCheckBox(
            adv_grid, text=self.app.get_id_text("opt_retry_chk"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ),
            variable=self.app.var_auto_retry)
        self.chk_retry.grid(row=1, column=0, columnspan=2, pady=ROW_GAP, sticky="w")

        self.lbl_opt_retry_sec = ctk.CTkLabel(
            adv_grid, text=self.app.get_id_text("opt_retry_sec"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W, anchor="w")
        self.lbl_opt_retry_sec.grid(row=2, column=0, pady=ROW_GAP, sticky="w")
        ctk.CTkSlider(adv_grid, from_=5, to=120, number_of_steps=115,
                      variable=self.app.var_retry_delay, width=180
                      ).grid(row=2, column=1, pady=ROW_GAP, sticky="w")
        ctk.CTkLabel(adv_grid, textvariable=self.app.var_retry_delay, width=32,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold")
                     ).grid(row=2, column=2, pady=ROW_GAP)

        # Límite de Velocidad (v1.1.20260405)
        self.lbl_opt_speed_limit = ctk.CTkLabel(
            adv_grid, text=self.app.get_id_text("opt_speed_limit"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W, anchor="w")
        self.lbl_opt_speed_limit.grid(row=3, column=0, pady=ROW_GAP, sticky="w")
        
        ctk.CTkSlider(adv_grid, from_=0, to=100, number_of_steps=100,
                      variable=self.app.var_speed_limit, width=180
                      ).grid(row=3, column=1, pady=ROW_GAP, sticky="w")
        
        def format_speed(val):
            v = int(float(val))
            return self.app.get_id_text("opt_speed_inf") if v == 0 else f"{v} MB/s"

        self.lbl_speed_val = ctk.CTkLabel(adv_grid, text="", width=60,
                                         font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold"))
        self.lbl_speed_val.grid(row=3, column=2, pady=ROW_GAP)
        
        # Vincular actualización de la etiqueta de velocidad
        self.app.var_speed_limit.trace_add("write", lambda *args: self.lbl_speed_val.configure(text=format_speed(self.app.var_speed_limit.get())))
        self.lbl_speed_val.configure(text=format_speed(self.app.var_speed_limit.get()))

        # ── 3. Cuentas Externas (f95zone) ──
        f95_card = ctk.CTkFrame(col_right, fg_color=CARD_BG, corner_radius=CARD_R)
        f95_card.pack(fill="x", pady=(0, CARD_GAP))

        self.lbl_opt_f95_title = ctk.CTkLabel(
            f95_card, text=self.app.get_id_text('opt_f95_title'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=TITLE_SZ, weight="bold"))
        self.lbl_opt_f95_title.pack(anchor="w", padx=CARD_IPAD, pady=(CARD_IPAD, 2))

        self.lbl_opt_f95_desc = ctk.CTkLabel(
            f95_card, text=self.app.get_id_text("opt_f95_desc"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=DESC_SZ), text_color="gray")
        self.lbl_opt_f95_desc.pack(anchor="w", padx=CARD_IPAD, pady=(0, 12))

        f95_grid = ctk.CTkFrame(f95_card, fg_color="transparent")
        f95_grid.pack(fill="x", padx=CARD_IPAD, pady=(0, CARD_IPAD))
        f95_grid.columnconfigure(1, weight=1)

        self.lbl_f95_u = ctk.CTkLabel(
            f95_grid, text=self.app.get_id_text("opt_f95_user"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W - 60, anchor="w")
        self.lbl_f95_u.grid(row=0, column=0, pady=ROW_GAP, sticky="w")
        ctk.CTkEntry(f95_grid, textvariable=self.app.var_f95_user, height=34,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ)
                     ).grid(row=0, column=1, pady=ROW_GAP, sticky="ew", padx=(0, 8))

        self.lbl_f95_p = ctk.CTkLabel(
            f95_grid, text=self.app.get_id_text("opt_f95_pass"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ), width=LBL_W - 60, anchor="w")
        self.lbl_f95_p.grid(row=1, column=0, pady=ROW_GAP, sticky="w")
        ctk.CTkEntry(f95_grid, textvariable=self.app.var_f95_pass, height=34, show="*",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ)
                     ).grid(row=1, column=1, pady=ROW_GAP, sticky="ew", padx=(0, 8))

        self.btn_test_f95 = ctk.CTkButton(
            f95_grid, text=self.app.get_id_text("opt_f95_test"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_SZ, weight="bold"),
            width=88, height=34, fg_color="#333", hover_color="#444",
            command=self.test_f95_connection)
        self.btn_test_f95.grid(row=1, column=2, pady=ROW_GAP)

    def test_api_key(self):
        token = self.app.var_api_key.get().strip()
        if not token:
            PremiumMessageModal(self.app, self.app.get_id_text("msg_api_title"), self.app.get_id_text("msg_api_empty"), icon="warn")
            return
            
        self.btn_test_api.configure(state="disabled", text="⌛ ...")
        
        def run_test():
            try:
                r = requests.get("https://api.real-debrid.com/rest/1.0/user", 
                                 headers={"Authorization": f"Bearer {token}"}, timeout=10)
                if r.status_code == 200:
                    user_data = r.json()
                    user_name = user_data.get('username', self.app.get_id_text("msg_api_user"))
                    self.app.after(0, lambda: PremiumMessageModal(self.app, self.app.get_id_text("msg_api_title"), f"{self.app.get_id_text('msg_api_ok')}\n{self.app.get_id_text('msg_api_user')}: {user_name}", icon="success"))
                else:
                    self.app.after(0, lambda: PremiumMessageModal(self.app, self.app.get_id_text("msg_api_title"), f"{self.app.get_id_text('msg_api_error')} ({r.status_code})", icon="error"))
            except Exception as e:
                self.app.after(0, lambda: PremiumMessageModal(self.app, self.app.get_id_text("msg_api_title"), f"{self.app.get_id_text('msg_api_conn')}:\n{e}", icon="error"))
            finally:
                self.app.after(0, lambda: self.btn_test_api.configure(state="normal", text=self.app.get_id_text("opt_test")))

        threading.Thread(target=run_test, daemon=True).start()

    def test_f95_connection(self):
        """Prueba las credenciales de f95zone en un hilo separado."""
        user = self.app.var_f95_user.get().strip()
        pwd = self.app.var_f95_pass.get().strip()
        
        if not user or not pwd:
            PremiumMessageModal(self.app, "f95zone", self.app.get_id_text("msg_f95_empty"), icon="warn")
            return

        self.btn_test_f95.configure(state="disabled", text="⌛ ...")
        
        def run_test():
            from utils.helpers import F95ZoneResolver
            resolver = F95ZoneResolver()
            try:
                ok, msg = resolver.login(user, pwd)
                if ok:
                    self.app.after(0, lambda: PremiumMessageModal(self.app, "f95zone", self.app.get_id_text("log_f95_login_ok"), icon="success"))
                else:
                    self.app.after(0, lambda: PremiumMessageModal(self.app, "f95zone", f"{self.app.get_id_text('log_f95_login_err')}\n{msg}", icon="error"))
            except Exception as e:
                self.app.after(0, lambda: PremiumMessageModal(self.app, "f95zone", f"{self.app.get_id_text('msg_f95_conn_err')}\n{e}", icon="error"))
            finally:
                self.app.after(0, lambda: self.btn_test_f95.configure(state="normal", text=self.app.get_id_text("opt_f95_test")))

        threading.Thread(target=run_test, daemon=True).start()
