import customtkinter as ctk
from core.config import FONT_FAMILY

class ProcessingModal(ctk.CTkToplevel):
    """Modal de progreso para operaciones masivas (v17.0)."""
    def __init__(self, master, title, total_steps):
        super().__init__(master)
        self.title(title)
        self.geometry("450x200")
        self.resizable(False, False)
        self.transient(master)
        
        # Centrado v9.0 (Píxel-Perfecto)
        self.app = master.app if hasattr(master, 'app') else master
        self.app.update_idletasks()
        self.update_idletasks()
        w, h = 450, 200
        ax, ay = self.app.winfo_rootx(), self.app.winfo_rooty()
        aw, ah = self.app.winfo_width(), self.app.winfo_height()
        tx = ax + (aw // 2) - (w // 2)
        ty = ay + (ah // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{tx}+{ty}")

        self.label = ctk.CTkLabel(self, text=title, font=("Montserrat", 14, "bold"))
        self.label.pack(pady=(30, 10))

        self.progress = ctk.CTkProgressBar(self, width=350, height=20)
        self.progress.set(0)
        self.progress.pack(pady=10)

        self.status = ctk.CTkLabel(self, text=f"0 / {total_steps}", font=("Montserrat", 12))
        self.status.pack(pady=5)
        
        self.total = total_steps

    def update_progress(self, current, text=None):
        pct = current / self.total if self.total > 0 else 0
        self.progress.set(pct)
        self.status.configure(text=f"{current} / {self.total}")
        if text: self.label.configure(text=text)

class VerificationWindow(ctk.CTkToplevel):
    """Ventana de reporte detallado tras verificación MD5 (v3.16.21)."""
    def __init__(self, master, filename, report_data, iid=None):
        super().__init__(master)
        self.iid = iid # Guardamos el IID para reparaciones directas
        self.title(f"{master.get_id_text('win_verify')}: {filename}")
        self.geometry("700x680")
        self.attributes("-topmost", True)
        self.configure(fg_color="#101114")
        
        # Centrado v9.0 (Píxel-Perfecto)
        self.app = master.app if hasattr(master, 'app') else master
        self.app.update_idletasks()
        self.update_idletasks()
        w, h = 700, 680
        ax, ay = self.app.winfo_rootx(), self.app.winfo_rooty()
        aw, ah = self.app.winfo_width(), self.app.winfo_height()
        tx = ax + (aw // 2) - (w // 2)
        ty = ay + (ah // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{tx}+{ty}")

        title_frame = ctk.CTkFrame(self, fg_color="#1a1c23", height=50, corner_radius=0)
        title_frame.pack(fill="x")
        
        is_suspicious = report_data.get('is_suspicious', False)
        status_icon = "⚠️" if is_suspicious else ("✅" if report_data.get('status') == "OK" else "❌")
        ctk.CTkLabel(title_frame, text=f"{status_icon} {master.get_id_text('win_verify')}", 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold")).pack(pady=10)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=10)

        # Alerta de tamaño sospechoso (v1.1.20260402)
        if is_suspicious:
            alert_frame = ctk.CTkFrame(content, fg_color="#3a2a0d", border_width=1, border_color="#e67e22")
            alert_frame.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(alert_frame, text=f"⚠️ {master.get_id_text('ver_suspicious_title')}", 
                         font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color="#e67e22").pack(pady=(10, 5))
            ctk.CTkLabel(alert_frame, text=master.get_id_text('ver_suspicious_msg'), 
                         font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color="#ccc", wraplength=600).pack(pady=(0, 10), padx=20)

        def add_row(parent, label, value, color="white"):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), 
                         text_color="#888", width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, 
                         font=ctk.CTkFont(family="Consolas" if "MD5" in label or "Ruta" in label else FONT_FAMILY, size=13), 
                         text_color=color, wraplength=450, justify="left").pack(side="left", fill="x")

        status_color = "#e67e22" if is_suspicious else ("#2da44e" if report_data.get('status') == "OK" else "#d32f2f")
        add_row(content, f"{master.get_id_text('win_status')}", report_data.get('status_msg', 'N/A'), status_color)
        
        sep = ctk.CTkFrame(content, height=1, fg_color="#333")
        sep.pack(fill="x", pady=15)

        add_row(content, master.get_id_text("ver_file"), filename)
        add_row(content, master.get_id_text("ver_path"), report_data.get('path', '-'))
        
        loc_fmt = report_data.get('local_size_formatted', '-')
        loc_bytes = report_data.get('local_size_bytes', 0)
        rem_fmt = report_data.get('remote_size_formatted', '-')
        rem_bytes = report_data.get('remote_size_bytes', 0)
        
        add_row(content, master.get_id_text("ver_size_loc"), f"{loc_fmt} ({loc_bytes} bytes)")
        add_row(content, master.get_id_text("ver_size_rem"), f"{rem_fmt} ({rem_bytes} bytes)")
        
        is_match = report_data.get('size_match', False)
        diff_color = "#2da44e" if is_match else "#d32f2f"
        diff_val = master.get_id_text("ver_perfect") if is_match else f"{report_data.get('size_diff', 0)} bytes"
        add_row(content, master.get_id_text("ver_diff"), diff_val, diff_color)

        sep2 = ctk.CTkFrame(content, height=1, fg_color="#333")
        sep2.pack(fill="x", pady=15)
        
        add_row(content, master.get_id_text("ver_type"), report_data.get('mime_type', 'N/A'), "#3b82f6")
        add_row(content, master.get_id_text("ver_header"), report_data.get('magic_desc', 'N/A'))
        
        # [NUEVO v3.0] Fila de Integridad de Estructura (ZIP testzip)
        if "struct_ok" in report_data:
            s_ok = report_data["struct_ok"]
            s_msg = master.get_id_text("msg_verify_zip_ok") if s_ok else f"{master.get_id_text('msg_verify_zip_err')} ({report_data.get('struct_err', '?')})"
            s_col = "#2da44e" if s_ok else "#d32f2f"
            add_row(content, master.get_id_text("ver_struct"), s_msg, s_col)
        add_row(content, master.get_id_text("ver_md5"), report_data.get('md5', 'N/A'), "#a1a1a1")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=20)
        
        btn_close = ctk.CTkButton(footer, text=master.get_id_text("btn_close_report"), width=200, height=40, 
                                  font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), 
                                  command=self.destroy)
        
        if report_data.get('status') == "ERROR":
            # Botón Inteligente de Reparación (v3.16.55)
            # Usa la lista completa de rangos corruptos para reparar todo de una vez
            r_ranges = report_data.get('repair_ranges') or ([report_data.get('repair_range')] if report_data.get('repair_range') else None)
            repair_cmd = lambda: self._trigger_surgical_repair(master, self.iid, r_ranges) if r_ranges else self._trigger_repair(master, self.iid)
            
            btn_repair = ctk.CTkButton(footer, text=master.get_id_text("btn_repair_file"), width=220, height=40,
                                       fg_color="#1f538d" if not r_ranges else "#e67e22", 
                                       hover_color="#2666ae" if not r_ranges else "#d35400",
                                       font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                                       command=repair_cmd)
            
            btn_repair.pack(side="left", padx=(30, 10), expand=True)
            btn_close.pack(side="left", padx=(10, 30), expand=True)
        else:
            btn_close.pack(expand=True)

    def _trigger_surgical_repair(self, master, iid, r_range):
        """Lanza la cirugía binaria por IID y cierra la ventana (v3.16.22)."""
        if iid and hasattr(master, "surgical_repair_by_iid"):
            master.surgical_repair_by_iid(iid, r_range)
        self.destroy()

    def _trigger_repair(self, master, iid):
        """Re-descarga completa: elimina el archivo corrupto y descarga desde cero (v3.16.59)."""
        if iid and hasattr(master, "force_redownload_by_iid"):
            master.force_redownload_by_iid(iid)
        elif iid and hasattr(master, "force_resume_by_iid"):
            master.force_resume_by_iid(iid)
            master.start_downloads()
        self.destroy()

class LinksInputWindow(ctk.CTkToplevel):
    """Ventana Premium para añadir enlaces: Sin bordes, transparente y centrada (v7.0 - Focus & Sync Final)."""
    def __init__(self, master, callback):
        super().__init__(master)
        from tkinter import ttk 
        self.app = master.app if hasattr(master, 'app') else master
        
        # 1. Configuración de Ventana
        self.geometry("1000x800")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000001") 
        self.attributes("-transparentcolor", "#000001")
        self.transient(master)
        
        # 2. Centrado y Sincronización (v14.0)
        self.app.update_idletasks()
        self.update_idletasks()
        
        ax = self.app.winfo_rootx()
        ay = self.app.winfo_rooty()
        aw = self.app.winfo_width()
        ah = self.app.winfo_height()
        mw, mh = 1000, 800
        
        tx = ax + (aw // 2) - (mw // 2)
        ty = ay + (ah // 2) - (mh // 2)
        self.geometry(f"+{tx}+{ty}")

        # 3. Marco Principal Estilizado
        self.main_frame = ctk.CTkFrame(self, fg_color="#101114", border_width=2, border_color="#1f538d", corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # 4. Cabecera con Botón Cerrar
        header_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=40)
        header_bar.pack(fill="x", padx=15, pady=(10, 0))
        
        ctk.CTkLabel(header_bar, text=master.get_id_text('win_add_links'), 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                     text_color="#3b82f6").pack(side="left")
        
        self.btn_close_top = ctk.CTkButton(header_bar, text="✕", width=30, height=30, fg_color="transparent", 
                                          hover_color="#d32f2f", font=ctk.CTkFont(size=16),
                                          command=self.destroy)
        self.btn_close_top.pack(side="right")

        # 5. Contenido del Formulario
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        # Entrada de Texto
        self.textbox = ctk.CTkTextbox(content, height=120, font=(FONT_FAMILY, 12), fg_color="#1a1c23", border_width=1)
        self.textbox.grid(row=0, column=0, pady=(0, 10), sticky="nsew")

        # Botonera
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=5, sticky="ew")
        
        self.btn_analyze = ctk.CTkButton(btn_frame, text=master.get_id_text("btn_analyze_links"), width=180,
                                        command=self._on_analyze)
        self.btn_analyze.pack(side="left", padx=(0, 10))
        
        self.btn_deep = ctk.CTkButton(btn_frame, text=master.get_id_text("btn_deep_analyze"), width=180,
                                     fg_color="#3d3d3d", hover_color="#4d4d4d",
                                     command=self._on_analyze_deep)
        self.btn_deep.pack(side="left")

        self.status_lbl = ctk.CTkLabel(btn_frame, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color="#888")
        self.status_lbl.pack(side="right", padx=10)

        self.total_to_resolve = 0
        self.resolved_count = 0

        # Tabla (Treeview)
        style = ttk.Style()
        style.configure("Links.Treeview", background="#1a1c23", foreground="white", 
                        fieldbackground="#1a1c23", borderwidth=0, rowheight=35)
        style.map("Links.Treeview", background=[('selected', '#1f538d')], foreground=[('selected', 'white')])
        
        self.tree_frame = ctk.CTkFrame(content, fg_color="#1a1c23", border_width=1, border_color="#333")
        self.tree_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        
        self.tree = ttk.Treeview(self.tree_frame, columns=("url", "filename"), show="headings", 
                                 style="Links.Treeview", selectmode="browse")
        
        self.tree.heading("url", text=master.get_id_text('col_link_url'), anchor="w")
        self.tree.heading("filename", text=master.get_id_text('col_target_name'), anchor="w")
        
        self.tree.column("url", width=350, anchor="w", stretch=True)
        self.tree.column("filename", width=550, anchor="w", stretch=True)
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<Double-1>", self._on_double_click)
        self.edit_entry = None

        self.btn_submit = ctk.CTkButton(content, text=master.get_id_text("btn_add_queue"), width=250, height=45,
                                       fg_color="#2da44e", hover_color="#34d058", state="disabled",
                                       font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
                                       command=lambda: self._on_submit(callback))
        self.btn_submit.grid(row=3, column=0, pady=(10, 5))

        # 6. Activación de Foco y Bloqueo (Final Sync)
        self.after(200, self._finalize_focus)

    def _finalize_focus(self):
        """Paso final para asegurar el control total del teclado v7.0."""
        try:
            self.lift()
            self.focus_force()
            self.grab_set() # Mover grab_set aquí para que no bloquee la creación
            self.textbox.focus_set()
        except:
            pass

    def _on_analyze(self, deep=False):
        """Puebla la tabla. Si deep=True, lanza hilos para resolver nombres."""
        text = self.textbox.get("1.0", "end-1c").strip()
        all_links = [l.strip() for l in text.splitlines() if l.strip().startswith('http')]
        
        if not all_links: return
        
        from utils.helpers import get_clean_name
        self.tree.delete(*self.tree.get_children())
        
        self.total_to_resolve = len(all_links) if deep else 0
        self.resolved_count = 0
        if deep:
            self.status_lbl.configure(text=f"Analizando: 0 / {self.total_to_resolve}")
            self.btn_deep.configure(state="disabled")
        else:
            self.status_lbl.configure(text="")

        for link in all_links:
            name = get_clean_name(link)
            # Si es profundo, ponemos un texto de "buscando" provisional (v3.1)
            display_name = "🔍 Consultando..." if deep else name
            iid = self.tree.insert("", "end", values=(link, display_name))
            if deep:
                import threading
                # Pasar la API Key desde la configuración de la app
                api_key = self.app.config.get('api_key')
                threading.Thread(target=self._resolve_worker, args=(iid, link, api_key), daemon=True).start()
        
        self.btn_submit.configure(state="normal")

    def _on_analyze_deep(self):
        self._on_analyze(deep=True)

    def _resolve_worker(self, iid, url, api_key=None):
        from core.engine import resolve_filename_from_url
        try:
            real_name = resolve_filename_from_url(url, api_key=api_key)
            
            def safe_update():
                try:
                    if not self.winfo_exists() or not self.tree.winfo_exists(): return
                    
                    self.resolved_count += 1
                    self.status_lbl.configure(text=f"Analizando: {self.resolved_count} / {self.total_to_resolve}")
                    
                    if self.tree.exists(iid) and real_name:
                        self.tree.set(iid, "filename", real_name)
                    
                    if self.resolved_count >= self.total_to_resolve:
                        self.btn_deep.configure(state="normal")
                        self.status_lbl.configure(text="Análisis completado")
                except:
                    pass
            
            self.after(0, safe_update)
        except Exception as e:
            print(f"[DEBUG] Error en resolve_worker para {url}: {e}")
            self.after(0, lambda: self._increment_counter())

    def _increment_counter(self):
        """Fuerza el incremento del contador incluso en errores para habilitar botones."""
        if not self.winfo_exists(): return
        self.resolved_count += 1
        if self.resolved_count >= self.total_to_resolve:
            self.btn_deep.configure(state="normal")
            self.status_lbl.configure(text="Análisis completado")

    def _on_double_click(self, event):
        """Implementa edición in-place en la columna de nombre de archivo."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        
        column = self.tree.identify_column(event.x)
        if column != "#2": return # Solo permitir editar la segunda columna (Filename)
        
        item = self.tree.identify_row(event.y)
        x, y, w, h = self.tree.bbox(item, column)
        
        value = self.tree.set(item, "filename")
        
        # Eliminar entrada previa si existe
        if self.edit_entry: self.edit_entry.destroy()
        
        # Crear entrada CTK sobre el Treeview
        self.edit_entry = ctk.CTkEntry(self.tree, width=w, height=h, font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        self.edit_entry.insert(0, value)
        self.edit_entry.place(x=x, y=y)
        self.edit_entry.focus_set()
        
        self.edit_entry.bind("<Return>", lambda e: self._save_edit(item))
        self.edit_entry.bind("<FocusOut>", lambda e: self._save_edit(item))
        self.edit_entry.bind("<Escape>", lambda e: self.edit_entry.destroy())

    def _save_edit(self, item):
        if not self.edit_entry: return
        new_val = self.edit_entry.get().strip()
        if new_val:
            self.tree.set(item, "filename", new_val)
        self.edit_entry.destroy()
        self.edit_entry = None

    def _on_submit(self, callback):
        """Agrupa los datos finales editados y los envía al callback."""
        # Recoger todos los pares (url, filename) de la tabla
        final_list = []
        for item in self.tree.get_children():
            url, filename = self.tree.item(item, "values")
            final_list.append((url, filename))
        
        # Realizar agrupación inteligente basada en los nombres finales editados
        grouped_data = {}
        for url, filename in final_list:
            if filename not in grouped_data:
                grouped_data[filename] = {'links': [url], 'folder': 'General'}
            else:
                if url not in grouped_data[filename]['links']:
                    grouped_data[filename]['links'].append(url)
                    
        if grouped_data:
            callback(grouped_data)
        self.destroy()


class PremiumMessageModal(ctk.CTkToplevel):
    """Ventana de mensaje premium con centrado absoluto y diseño moderno (v4.2)."""
    def __init__(self, master, title, message, icon="info"):
        super().__init__(master)
        # Referencia al app real si el master es un mixin o tab
        self.app = master.app if hasattr(master, 'app') else master
        
        self.title(title or "Bandolero")
        self.geometry("400x220")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color="#000001") # Color de transparencia "mágico" (v5.3)
        self.attributes("-transparentcolor", "#000001")
        self.overrideredirect(True) # Quitar bordes de Windows (v5.1)
        self.transient(master)
        self.grab_set()

        # Centrado Directo por Píxeles (v9.0 - Sin cálculos de escala)
        self.app.update_idletasks()
        self.update_idletasks()
        
        # 1. Obtener coordenadas y dimensiones físicas de la App (Píxeles de monitor)
        ax = self.app.winfo_rootx()
        ay = self.app.winfo_rooty()
        aw = self.app.winfo_width()
        ah = self.app.winfo_height()
        
        # 2. Obtener dimensiones físicas del Modal
        mw = self.winfo_width()
        mh = self.winfo_height()
        
        # 3. Calcular posición absoluta (Centro App - Mitad Modal)
        tx = ax + (aw // 2) - (mw // 2)
        ty = ay + (ah // 2) - (mh // 2)
        
        # 4. Aplicar posición y mostrar
        # En Windows con overrideredirect, pasar solo +X+Y posiciona en píxeles absolutos
        self.geometry(f"+{tx}+{ty}")
        self.attributes("-alpha", 1.0)

        # Icono visual (Nemonía simple)
        icons = {"info": "ℹ️", "error": "❌", "warn": "⚠️", "success": "✅"}
        current_icon = icons.get(icon, "ℹ️")

        # Marco principal con borde estilizado (sustituye al marco de Windows)
        self.main_frame = ctk.CTkFrame(self, fg_color="#101114", border_width=2, border_color="#1f538d", corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Cabecera con Icono y Título
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text=current_icon, font=("Segoe UI Emoji", 32)).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), 
                     text_color="#3b82f6").pack(side="left")

        # Cuerpo del mensaje
        msg_label = ctk.CTkLabel(self.content_frame, text=message, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                                 wraplength=350, justify="left", text_color="#ccc")
        msg_label.pack(fill="both", expand=True, pady=10)

        # Botón de confirmación Premium
        self.btn_ok = ctk.CTkButton(self.content_frame, text=self.app.get_id_text("btn_ok"), 
                                    width=120, height=35, corner_radius=8,
                                    font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                                    command=self.destroy)
        self.btn_ok.pack(pady=(10, 0))
        
        # Atajo: Enter para cerrar
        self.bind("<Return>", lambda e: self.destroy())
