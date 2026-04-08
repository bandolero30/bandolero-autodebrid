import os
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from utils.helpers import resource_path
from core.config import FONT_FAMILY

class BannerFrame(ctk.CTkFrame):
    """Componente de cabecera con banner dinámico y marca de agua (v1.1.20260401)."""

    def __init__(self, master, font_family=FONT_FAMILY, **kwargs):
        super().__init__(master, fg_color="#0a0b0d", height=100, corner_radius=0, **kwargs)
        self.font_family = font_family
        self.banner_img = None
        self.banner_label = None
        self._prepare_banner()
        self._create_widgets()

    def _prepare_banner(self):
        """Genera el banner con procesamiento de ZOOM y CROPPING exacto (v1.1.20260401)."""
        banner_path = resource_path("resources/pirate_tech_banner_pro.png")
        if not os.path.exists(banner_path):
            self.banner_img = None
            return

        try:
            full_img = Image.open(banner_path)
            w, h = full_img.size
            
            # 🔥 RESTAURADO: ZOOM_FACTOR 0.3 🔥
            ZOOM_FACTOR = 0.3
            new_w = int(w * ZOOM_FACTOR)
            new_h = int(h * ZOOM_FACTOR)
            
            zoomed_img = full_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 🔥 RESTAURADO: banner_h 110 🔥
            banner_h = 110
            top = (new_h - banner_h) // 2 if new_h > banner_h else 0
            bottom = top + banner_h if new_h > banner_h else new_h
            banner_crop = zoomed_img.crop((0, top, new_w, bottom))
            
            draw = ImageDraw.Draw(banner_crop)
            
            # Carga de fuentes para PIL (v1.1.20260401)
            path_montserrat = "fonts/Montserrat-Bold.ttf"
            path_emoji = "C:/Windows/Fonts/seguiemj.ttf"
            
            try:
                f_title = ImageFont.truetype(path_montserrat, 30) 
                f_sub = ImageFont.truetype(path_montserrat, 16)
                f_emoji = ImageFont.truetype(path_emoji, 30)
            except:
                f_title = ImageFont.load_default()
                f_sub = ImageFont.load_default()
                f_emoji = ImageFont.load_default()
            
            t_emoji = "⚡"
            t1_text = " BANDOLERO AUTODEBRID"
            t2 = "PRO DOWNLOADER PREMIUM"
            
            # Paleta Laser Blue (original)
            COLOR_MAIN = "#00f2ff" 
            COLOR_SUB = "#afeeee"  
            COLOR_OUTLINE = "black"
            
            def draw_studio_text(x, y, text, emoji, font, e_font, fill_color, out_color):
                e_w = draw.textlength(emoji, font=e_font)
                t_w = draw.textlength(text, font=font)
                total_w = e_w + t_w
                for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (0,-2), (0,2), (-2,0), (2,0)]:
                    draw.text((x - total_w + dx, y + dy), emoji, font=e_font, fill=out_color, anchor="lm")
                    draw.text((x - total_w + e_w + dx, y + dy), text, font=font, fill=out_color, anchor="lm")
                draw.text((x - total_w, y), emoji, font=e_font, fill="white", anchor="lm")
                draw.text((x - total_w + e_w, y), text, font=font, fill=fill_color, anchor="lm")

            draw_studio_text(new_w - 40, banner_h//2 - 25, t1_text, t_emoji, f_title, f_emoji, COLOR_MAIN, COLOR_OUTLINE)
            
            def draw_sub_legacy(x, y, text, font, fill, out):
                for dx, dy in [(-1,-1), (1,1), (-1,1), (1,-1)]:
                    draw.text((x + dx, y + dy), text, font=font, fill=out, anchor="rm")
                draw.text((x, y), text, font=font, fill=fill, anchor="rm")
            
            draw_sub_legacy(new_w - 40, banner_h//2 + 20, t2, f_sub, COLOR_SUB, COLOR_OUTLINE)
            
            self.banner_img = ctk.CTkImage(light_image=banner_crop, dark_image=banner_crop, size=(new_w, banner_h))
            # Ajustar altura del frame dinámicamente
            self.configure(height=banner_h)
        except Exception as e:
            print(f"Error preparando banner component: {e}")
            self.banner_img = None

    def _create_widgets(self):
        """Instancia el label del banner."""
        if self.banner_img:
            self.banner_label = ctk.CTkLabel(self, image=self.banner_img, text="")
            self.banner_label.place(relx=0.5, rely=0.5, anchor="center")


