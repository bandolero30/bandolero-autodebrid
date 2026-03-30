# Bandolero AutoDebrid - EXE Build Script [v4.7]
# Este script automatiza la creación del binario independiente

# 1. Limpieza de compilaciones previas
Remove-Item -Path "./dist", "./build" -Recurse -ErrorAction SilentlyContinue

write-host "🚀 Iniciando compilación de Bandolero AutoDebrid..." -ForegroundColor Cyan

# 2. Ejecución de PyInstaller mediante el módulo de Python (Garantía v4.9)
# --onefile: Un solo ejecutable
# --windowed: Sin ventana de consola (GUI pura)
# --icon: Icono de Windows (.ico)
# --collect-all: Forzar inclusión de todos los archivos de CustomTkinter
# --hidden-import: Asegurar detección de módulos dinámicos
python -m PyInstaller --noconfirm --onefile --windowed `
    --name "Bandolero_AutoDebrid" `
    --icon "app_icon.ico" `
    --collect-all customtkinter `
    --hidden-import customtkinter `
    --add-data "pirate_tech_banner_pro.png;." `
    --add-data "app_icon.png;." `
    app_gui.py

write-host "✅ Compilación finalizada. El ejecutable se encuentra en la carpeta 'dist/'." -ForegroundColor Green
