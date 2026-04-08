import os
import time
import tkinter.ttk as ttk
import customtkinter as ctk
from core.config import FONT_FAMILY

class QueueTab(ctk.CTkFrame):
    """Pestaña de cola de descargas modularizada (v1.1.20260401)."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.tree = None
        self.log_container = None
        self.log_textbox = None
        self._build_ui()

    def refresh_texts(self):
        """Actualiza todos los textos de la pestaña según el idioma actual (v1.1.20260401)."""
        self.lbl_origen.configure(text=self.app.get_id_text("lbl_origin"))
        self.lbl_destino.configure(text=self.app.get_id_text("lbl_dest"))
        self.btn_paste.configure(text=self.app.get_id_text("btn_add_links"))
        self.btn_browse.configure(text=self.app.get_id_text("btn_browse"))
        self.btn_start.configure(text=self.app.get_id_text("btn_start"))
        self.btn_start_sel.configure(text=self.app.get_id_text("btn_start_sel"))
        self.btn_stop.configure(text=self.app.get_id_text("btn_stop"))
        self.btn_stop_sel.configure(text=self.app.get_id_text("btn_stop_sel"))
        self.btn_apply_subfolder.configure(text=self.app.get_id_text("btn_apply_sel"))
        
        log_text = self.app.get_id_text('btn_hide_log') if self.app.console_visible else self.app.get_id_text('btn_show_log')
        pref = "▲" if self.app.console_visible else "▼"
        self.btn_toggle_log.configure(text=f"{pref} {log_text}")
        
        cw = self.app.COL_WIDTHS
        for col in cw:
            text_key = f"col_{'status' if col=='resultado' else 'file' if col=='archivo' else 'progress' if col=='progreso' else 'size' if col=='tamanio' else 'speed' if col=='velocidad' else 'folder' if col=='carpeta' else col}"
            self.tree.heading(col, text=self.app.get_id_text(text_key))

    def _update_action_buttons_ui(self, is_downloading):
        """Alterna visibilidad de botones de acción."""
        if is_downloading:
            self.btn_start.pack_forget(); self.btn_start_sel.pack_forget()
            self.btn_stop.pack(side="right", padx=0); self.btn_stop_sel.pack(side="right", padx=(0, 5))
        else:
            self.btn_stop.pack_forget(); self.btn_stop_sel.pack_forget()
            self.btn_start.pack(side="right", padx=0); self.btn_start_sel.pack(side="right", padx=(0, 5))

    def _build_ui(self):
        control_panel = ctk.CTkFrame(self, fg_color="#181a1f", corner_radius=10, border_width=1, border_color="#2a2d35")
        control_panel.pack(fill="x", padx=0, pady=(0, 20))
        control_panel.grid_columnconfigure(1, weight=1)

        self.lbl_origen = ctk.CTkLabel(control_panel, text=self.app.get_id_text("lbl_origin"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"))
        self.lbl_origen.grid(row=0, column=0, padx=(15, 15), pady=(15, 5), sticky="e")
        
        self.entry_origen = ctk.CTkEntry(control_panel, textvariable=self.app.dlc_path, state="readonly", fg_color="#101114", border_color="#333", border_width=1, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz))
        self.entry_origen.grid(row=0, column=1, padx=(0, 15), pady=(15, 5), sticky="ew")
        
        self.btn_paste = ctk.CTkButton(control_panel, text=self.app.get_id_text("btn_add_links"), width=280, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#1f538d", hover_color="#2a6fb2", command=self.app.open_add_links_window)
        self.btn_paste.grid(row=0, column=2, columnspan=2, padx=(0, 10), pady=(15, 5), sticky="ew")

        self.btn_browse = ctk.CTkButton(control_panel, text=self.app.get_id_text("btn_browse"), width=250, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#1f538d", hover_color="#2a6fb2", command=self.app.browse_dlc)
        self.btn_browse.grid(row=0, column=4, padx=(0, 15), pady=(15, 5), sticky="ew")

        self.lbl_destino = ctk.CTkLabel(control_panel, text=self.app.get_id_text("lbl_dest"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), text_color="#a1a1a1")
        self.lbl_destino.grid(row=1, column=0, padx=(15, 15), pady=(5, 15), sticky="e")
        
        self.entry_destino = ctk.CTkEntry(control_panel, textvariable=self.app.var_subfolder, fg_color="#101114", border_color="#333", border_width=1, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), text_color="#2da44e")
        self.entry_destino.grid(row=1, column=1, padx=(0, 15), pady=(5, 15), sticky="ew")

        self.btn_apply_subfolder = ctk.CTkButton(control_panel, text=self.app.get_id_text("btn_apply_sel"), width=280, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#5c6bc0", hover_color="#7986cb", command=self.app.apply_folder_to_selected)
        self.btn_apply_subfolder.grid(row=1, column=2, columnspan=2, padx=(0, 10), pady=(5, 15), sticky="ew")

        action_frame = ctk.CTkFrame(control_panel, fg_color="transparent")
        action_frame.grid(row=1, column=4, padx=(0, 15), pady=(5, 15), sticky="ew")
        
        self.btn_start = ctk.CTkButton(action_frame, text=self.app.get_id_text("btn_start"), width=120, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#2da44e", hover_color="#34d058", command=self.app.start_all_downloads)
        self.btn_start_sel = ctk.CTkButton(action_frame, text=self.app.get_id_text("btn_start_sel"), width=120, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#008080", hover_color="#00a0a0", command=self.app.start_selected_downloads)
        self.btn_stop = ctk.CTkButton(action_frame, text=self.app.get_id_text("btn_stop"), height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#d32f2f", hover_color="#e05a47", command=self.app.stop_downloads)
        self.btn_stop_sel = ctk.CTkButton(action_frame, text=self.app.get_id_text("btn_stop_sel"), height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), fg_color="#e67e22", hover_color="#ff9c42", command=self.app.stop_selected_downloads)
        
        self.btn_start.pack(side="right", fill="x", expand=True, padx=0); self.btn_start_sel.pack(side="right", fill="x", expand=True, padx=(0, 5))

        # Vinculación de Tooltips Premium (v1.1.20260405)
        self.app._bind_tooltip(self.btn_paste, "tt_paste_t", "tt_paste_m")
        self.app._bind_tooltip(self.btn_browse, "tt_browse_t", "tt_browse_m")
        self.app._bind_tooltip(self.btn_apply_subfolder, "tt_apply_t", "tt_apply_m")
        self.app._bind_tooltip(self.btn_start, "tt_start_t", "tt_start_m")
        self.app._bind_tooltip(self.btn_start_sel, "tt_start_sel_t", "tt_start_sel_m")
        self.app._bind_tooltip(self.btn_stop, "tt_stop_t", "tt_stop_m")
        self.app._bind_tooltip(self.btn_stop_sel, "tt_stop_sel_t", "tt_stop_sel_m")

        self.btn_toggle_log = ctk.CTkButton(self, text=self.app.get_id_text("btn_show_log"), fg_color="#333", hover_color="#444", font=ctk.CTkFont(family=FONT_FAMILY, size=self.app.sz, weight="bold"), command=self.app.toggle_console)
        self.btn_toggle_log.pack(side="bottom", fill="x", padx=5, pady=(5,0))
        
        self.log_container = ctk.CTkFrame(self, height=220, fg_color="#101010", border_width=1, border_color="#444")
        self.log_textbox = ctk.CTkTextbox(self.log_container, font=ctk.CTkFont(family="Consolas", size=self.app.sz-1), text_color="#4af626", fg_color="transparent")
        self.log_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_textbox.configure(state="disabled")
        
        # [NUEVO v2.12] Empaquetado nativo inicial si está configurado para evitar efecto macro
        if self.app.console_visible:
            self.log_container.pack(side="bottom", fill="x", padx=5, pady=5)
        
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.pack(side="top", fill="both", expand=True, padx=2, pady=(0, 2))
        tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1)

        tree_scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        self.tree = ttk.Treeview(tree_frame, columns=("archivo", "carpeta", "progreso", "tamanio", "velocidad", "resultado"), show="headings")
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.configure(command=self.tree.yview)
        self.tree.grid(row=0, column=0, sticky="nsew"); tree_scroll_y.grid(row=0, column=1, sticky="ns")

        cw = self.app.COL_WIDTHS
        for col in cw:
            text_key = f"col_{'status' if col=='resultado' else 'file' if col=='archivo' else 'progress' if col=='progreso' else 'size' if col=='tamanio' else 'speed' if col=='velocidad' else 'folder' if col=='carpeta' else col}"
            self.tree.heading(col, text=self.app.get_id_text(text_key), command=lambda c=col: self.app._sort_column(c) if c in ["archivo", "carpeta"] else None)
            self.tree.column(col, width=cw[col]["width"], stretch=cw[col]["stretch"], anchor="w", minwidth=cw[col]["minwidth"])

        # self.tree.bind("<Button-1>", self.app.on_tree_click) # Eliminado: No hay casillas [X]
        self.tree.bind("<Double-1>", lambda e: self.app.open_selected_folder())
        self.tree.bind("<Button-3>", self.app.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.app._on_tree_selection_changed)
        self.tree.bind("<Motion>", self.app._on_tree_motion)
        self.tree.bind("<Leave>", lambda e: self.app._hide_file_tooltip())

    def refresh_console(self, iid):
        """Actualiza la caja de texto de logs basándose en el IID de la fila (v3.16.12)."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        
        self.log_textbox.tag_config("host", foreground="#e67e22")
        
        if iid in self.app.logs_dict and self.app.logs_dict[iid]:
            content = "\n".join(self.app.logs_dict[iid])
            self.log_textbox.insert("1.0", content)
            
            idx = "1.0"
            while True:
                idx = self.log_textbox.search("(", idx, stopindex="end")
                if not idx: break
                
                end_idx = self.log_textbox.search(")", idx, stopindex="end")
                if not end_idx: break
                
                actual_end = f"{end_idx}+1c"
                self.log_textbox.tag_add("host", idx, actual_end)
                idx = actual_end
        else:
            self.log_textbox.insert("1.0", f"[{time.strftime('%H:%M:%S')}] {self.app.get_id_text('msg_wait_log')}")
            
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
