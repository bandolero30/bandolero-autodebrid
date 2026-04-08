import os
import urllib.parse
import customtkinter as ctk
from core.config import FONT_FAMILY
from utils.helpers import format_size

class SimpleTooltip(ctk.CTkToplevel):
    """Ventana flotante premium para mensajes informativos cortos (v13.3)."""
    def __init__(self, master, title, message, x, y):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(fg_color="#1a1c1e")
        
        self.geometry(f"+{x+20}+{y+20}")
        
        # Marco principal con borde cian 'Premium'
        self.frame = ctk.CTkFrame(self, fg_color="#181a1f", border_color="#00f2ff", border_width=1, corner_radius=8)
        self.frame.pack(fill="both", expand=True)
        
        # Mini Header informativo (Más compacto v13.9)
        header = ctk.CTkFrame(self.frame, fg_color="#1f538d", height=20, corner_radius=6)
        header.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(header, text=f"💡 {title}", 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), 
                     text_color="white").pack(pady=1)
        
        content = ctk.CTkFrame(self.frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=8)
        
        lbl = ctk.CTkLabel(content, text=message, font=ctk.CTkFont(family=FONT_FAMILY, size=14), 
                           text_color="#ddd", justify="left", wraplength=400)
        lbl.pack()
        
        self.alpha = 0.0
        self._fade_in()

    def _fade_in(self):
        """Animación de aparición suave (Alpha blending)."""
        if self.alpha < 0.95:
            self.alpha += 0.15
            self.attributes("-alpha", self.alpha)
            self.after(20, self._fade_in)

class FileDetailsTooltip(ctk.CTkToplevel):
    """Ficha técnica premium que aparece al hacer hover sobre archivos (v14.0 - Compact & Hosting)."""
    def __init__(self, master, filename, data, x, y):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        
        self.frame = ctk.CTkFrame(self, fg_color="#181a1f", border_color="#00f2ff", border_width=1, corner_radius=8)
        self.frame.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(self.frame, fg_color="#1f538d", height=25, corner_radius=6)
        header.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(header, text=master.get_id_text("tt_technical"), 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), 
                     text_color="white").pack(pady=2)
        
        content = ctk.CTkFrame(self.frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=5)
        
        def add_field(label, value, color="#888"):
            f = ctk.CTkFrame(content, fg_color="transparent")
            f.pack(fill="x", pady=1)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), 
                         text_color=color, width=90, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=value, font=ctk.CTkFont(family=FONT_FAMILY, size=12), 
                         text_color="#ddd", wraplength=350, justify="left").pack(side="left", fill="x")

        # Extraer información
        base_dir = master.config.get("base_dir", "T:\\Descargas")
        sub_folder = data.get("subfolder", master.var_subfolder.get().strip())
        full_path = os.path.join(base_dir, sub_folder)
        
        # Extraer hosting del primer enlace (v14.0)
        links = data.get("links", [])
        host_domain = master.get_id_text("st_unknown")
        if links:
            try:
                parsed = urllib.parse.urlparse(links[0])
                host_domain = parsed.netloc or master.get_id_text("st_unknown")
            except: pass
            
        size_bytes = data.get("filesize", 0)
        size_str = format_size(size_bytes) if size_bytes > 0 else master.get_id_text("st_unknown")
        status = master.tree.set(data["iid"], "resultado").strip()
        
        add_field(master.get_id_text("ver_file"), filename, "#00f2ff")
        add_field(master.get_id_text("tt_host"), host_domain, "#2da44e")
        add_field(master.get_id_text("tt_dir"), full_path)
        add_field(f"{master.get_id_text('tt_hosters')}", f"{len(links)} hoster/s")
        add_field(master.get_id_text("tt_size"), size_str)
        add_field(master.get_id_text("tt_status"), status)

        # Posicionamiento inteligente (evitar salirse de la pantalla)
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        
        # Offset para que no tape el cursor
        final_x = x + 20
        final_y = y + 20
        
        # Ajuste si se sale por la derecha
        if final_x + w > self.winfo_screenwidth():
            final_x = x - w - 10
            
        # Ajuste si se sale por abajo
        if final_y + h > self.winfo_screenheight():
            final_y = y - h - 10
            
        self.geometry(f"+{final_x}+{final_y}")
        self._fade_in()

    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 0.95:
            alpha += 0.15
            self.attributes("-alpha", alpha)
            self.after(20, self._fade_in)
