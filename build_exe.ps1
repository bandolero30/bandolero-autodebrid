# Bandolero AutoDebrid - EXE Build Script [v1.1.20260401]
# Este script automatiza la creación del binario independiente

# 1. Limpieza de compilaciones previas
Remove-Item -Path "./dist", "./build" -Recurse -ErrorAction SilentlyContinue

# 1.5 Extraer versión del código fuente (v1.1.20260401 Modular)
$version = Select-String -Path "core/config.py" -Pattern '__version__ = "(.*)"' | ForEach-Object { $_.Matches.Groups[1].Value }
if (-not $version) { $version = "DEV" }

write-host "🚀 Iniciando compilación de Bandolero AutoDebrid v$version..." -ForegroundColor Cyan

# 2. Ejecución de PyInstaller mediante el módulo de Python (Garantía v1.1.20260401)
# --onefile: Un solo ejecutable
# --windowed: Sin ventana de consola (GUI pura)
# --icon: Icono de Windows (.ico)
# --collect-all: Forzar inclusión de todos los archivos de CustomTkinter
# --hidden-import: Asegurar detección de módulos dinámicos
python -m PyInstaller --noconfirm --onefile --windowed `
    --name "Bandolero_AutoDebrid_v$version" `
    --icon "resources/app_icon.ico" `
    --splash "resources/bando-logo-autodebrid.png" `
    --collect-all customtkinter `
    --hidden-import customtkinter `
    --add-data "resources;resources" `
    --add-data "locales;locales" `
    --add-data "fonts;fonts" `
    main.py

write-host "✅ Compilación finalizada. El ejecutable se encuentra en la carpeta 'dist/'." -ForegroundColor Green
