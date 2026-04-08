import os
import customtkinter as ctk
from core.config import FONT_FAMILY
from core.i18n import Translator
from utils.helpers import resource_path
from PIL import Image

class PremiumLanguageSelector(ctk.CTkFrame):
    """Selector de idioma premium con banderas y menú desplegable (v20.0)."""
    def __init__(self, master, current_lang, command=None):
        super().__init__(master, fg_color="transparent")
        self.command = command
        self.current_lang = current_lang
        self._images = {}
        self._langs = {}

        self.btn_main = ctk.CTkButton(self, text="", width=170, height=35, 
                                       fg_color="#1e1e1e", border_color="#333", border_width=1,
                                       hover_color="#2a2a2a", corner_radius=8,
                                       font=ctk.CTkFont(family=FONT_FAMILY, size=14),
                                       anchor="w", command=self._toggle_menu)
        self.btn_main.pack(fill="x")
        self.update_selection(current_lang)

    def _toggle_menu(self):
        """Muestra el desplegable personalizado directo."""
        x, y = self.btn_main.winfo_rootx(), self.btn_main.winfo_rooty() + 38
        opts = []
        for k, v in self._langs.items():
            opts.append((v, self._images.get(k), k))
        self.menu = PremiumDropdown(self, opts, x, y, self._on_select)

    def _on_select(self, code):
        self.update_selection(code)
        if self.command: 
            self.command(code)

    def update_selection(self, code):
        self.current_lang = code
        # Obtener idiomas soportados desde el Translator modular (v22.0)
        self._langs = Translator.get_supported_languages()
        
        self._images = {}
        for c in self._langs:
            try:
                path = resource_path(os.path.join("resources", f"flag_{c}.png"))
                if os.path.exists(path):
                    img = Image.open(path).convert("RGBA")
                    self._images[c] = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 22))
            except Exception as e:
                print(f"Error cargando icono modular para {c}: {e}")
        
        lang_name = self._langs.get(code, code.upper())
        icon = self._images.get(code)
        self.btn_main.configure(text=f"  {lang_name}", image=icon, compound="left")

class PremiumDropdown(ctk.CTkToplevel):
    """Menú desplegable directo sin efectos de animación (v17.0)."""
    def __init__(self, master, options, x, y, callback):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self, fg_color="#181a1f", border_color="#333", border_width=1, corner_radius=8)
        frame.pack(fill="both", expand=True)
        
        for name, img, code in options:
            btn = ctk.CTkButton(frame, text=f"  {name}", image=img, compound="left",
                                 anchor="w", height=32, fg_color="transparent",
                                 hover_color="#1f538d", corner_radius=4,
                                 font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                                 command=lambda c=code: [callback(c), self.destroy()])
            btn.pack(fill="x", padx=4, pady=2)
        
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_force()

class ModernContextMenu(ctk.CTkToplevel):
    """Menú contextual moderno con soporte de emojis y diseño premium (v5.0)."""
    def __init__(self, master, options, font_sz=14):
        super().__init__(master)
        self.withdraw()  # Evitar parpadeo inicial (v3.1)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        self.frame = ctk.CTkFrame(self, fg_color="#1e1e1e", border_color="#333333", border_width=2, corner_radius=10)
        self.frame.pack(padx=1, pady=1, fill="both", expand=True)

        for text, command in options:
            if text == "---":
                sep = ctk.CTkFrame(self.frame, height=1, fg_color="#333333")
                sep.pack(fill="x", padx=10, pady=5)
                continue
            
            # Separar el icono del texto para alineación proporcional (v1.1.20260405)
            parts = text.strip().split(" ", 1)
            icon = parts[0].strip() if len(parts) > 1 else ""
            label_text = parts[1].strip() if len(parts) > 1 else text.strip()
            
            # Contenedor de fila con efectos táctiles
            item_frame = ctk.CTkFrame(self.frame, fg_color="transparent", corner_radius=6, height=35)
            item_frame.pack(fill="x", padx=4, pady=1)
            
            # Columna de Icono (Ancho fijo de 45px para garantizar alineación vertical perfecta)
            icon_lbl = ctk.CTkLabel(item_frame, text=icon, width=45,
                                    font=ctk.CTkFont(family=FONT_FAMILY, size=font_sz+2),
                                    text_color="#ffffff", anchor="center")
            icon_lbl.pack(side="left")
            
            # Columna de Texto
            text_lbl = ctk.CTkLabel(item_frame, text=label_text, 
                                    font=ctk.CTkFont(family=FONT_FAMILY, size=font_sz),
                                    text_color="#dddddd", anchor="w")
            text_lbl.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            # Funciones de evento optimizadas
            def on_enter(e, f=item_frame): f.configure(fg_color="#1f538d")
            def on_leave(e, f=item_frame): f.configure(fg_color="transparent")
            def on_click(e, cmd=command): self._on_click(cmd)

            for w in [item_frame, icon_lbl, text_lbl]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)

    def show(self, x, y):
        self.update_idletasks()
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.focus_force()
        
        def _close(e=None):
            try: self.destroy()
            except: pass

        # Desvincular menús anteriores si existen
        self.master.bind("<Button-1>", _close, add="+")
        self.master.bind("<Button-3>", _close, add="+")
        self.after(100, lambda: self.bind("<FocusOut>", _close))

    def _on_click(self, command):
        self.destroy()
        if command:
            command()
