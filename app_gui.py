"""
 * @title Bandolero AutoDebrid - Download Manager
 * @version 1.0.20260330
 * @description Advanced download manager for Debrid services with multi-selection support, 
 *              MD5 batch verification, secure technical resume, and intelligent hoster rotation.
 * 
 * @custom:v1.0.20260330 Implementation of intelligent multi-selection context menu and batch processing 
 *                engine for technical actions (Start, Stop, Remove, Verify, Resume, Rotate).
 * 
 * @author Bandolero
 * @license CC BY-NC-SA 4.0
 * @repository https://github.com/bandolero30/bandolero-autodebrid
 * 
 * @tech-stack: CustomTkinter, Python 3.x, ThreadPoolExecutor, Win32 API.
 """

import os
import sys
import re
import json
import time
import queue
import threading
import requests
import urllib.request
import urllib.parse
import base64
import hashlib
try:
    import win32crypt
except ImportError:
    win32crypt = None
import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageTk, ImageDraw

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

if not os.path.exists("fonts"):
    os.makedirs("fonts")

montserrat_reg = "fonts/Montserrat-Regular.ttf"
montserrat_bold = "fonts/Montserrat-Bold.ttf"

try:
    if not os.path.exists(montserrat_reg):
        urllib.request.urlretrieve("https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf", montserrat_reg)
    if not os.path.exists(montserrat_bold):
        urllib.request.urlretrieve("https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf", montserrat_bold)
        
    ctk.FontManager.load_font(montserrat_reg)
    ctk.FontManager.load_font(montserrat_bold)
    # Fallback system: Montserrat for Latin/Cyrillic, Microsoft YaHei for Chinese, Segoe UI as ultimate fallback
    FONT_FAMILY = ("Montserrat", "Microsoft YaHei", "SimSun", "Segoe UI")
except Exception as e:
    FONT_FAMILY = ("Segoe UI", "Tahoma", "Arial")

def resource_path(relative_path):
    """ Obtiene la ruta absoluta para recursos, compatible con PyInstaller (_MEIPASS) y dev. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE LOCALIZACIÓN (v7.0 GLOBAL EDITION)
# ─────────────────────────────────────────────────────────────────────────────
LANG_DATA = {
    "es": {
        "tab_dl": "☁️ Descargas", "tab_opt": "⚙️ Opciones",
        "lbl_origin": "📦 Origen:", "lbl_dest": "📁 Destino:",
        "btn_browse": "Examinar Multi...", "btn_load": "📥 Cargar a la Tabla",
        "btn_start": "▶ Iniciar Cola", "btn_stop": "⏹ Parar En Seco",
        "btn_toggle_all": "☑ Marcar / Desmarcar Todos", "btn_show_log": "▼ Mostrar Consola de Eventos",
        "btn_hide_log": "▲ Ocultar Consola de Eventos", "col_check": "[X]",
        "col_file": "  Archivo", "col_progress": "  Progreso",
        "col_size": "Tamaño", "col_speed": "Velocidad", "col_status": "  Estado",
        "opt_ui_title": "🎨 Interfaz Visual", "opt_lang": "Idioma de Interfaz:",
        "opt_gui_size": "Tamaño Interfaz General:", "opt_cell_size": "Tamaño Celdas de Tabla:",
        "opt_api_title": "🔑 API Key Real-Debrid", "opt_api_desc": "Token privado para acelerar descargas automáticamente.",
        "opt_test": "🧪 Probar", "opt_dir_title": "📁 Directorio Base de Descargas",
        "opt_dir_desc": "Se creará una subcarpeta inteligente dentro de este directorio.",
        "opt_adv_title": "⚙️ Avanzado (Motor Multihilo)", "opt_sim_dl": "Descargas simultáneas:",
        "opt_retry_chk": "Reintento Automático Infinito", "opt_retry_sec": "Segundos de Auto-Reintento:",
        "opt_save": "💾 Guardar Cambios", "msg_wait_log": "Esperando trazas de red...",
        "ctx_start": "Iniciar", "ctx_stop": "Parar", "ctx_rotate": "Rotar Hoster",
        "ctx_verify": "Verificar Integridad", "ctx_open": "Abrir Carpeta",
        "ctx_copy": "Copiar Enlace Original", "ctx_report": "Ver Reporte MD5",
        "log_verify": "Verificando MD5...", "log_error": "ERROR (Inconsistencia)",
        "win_verify": "Reporte de Integridad Técnica", "win_status": "Estado General:",
        "msg_api_title": "Prueba API", "msg_api_empty": "Introduce un token primero.",
        "msg_api_ok": "🚀 ¡Conexión Exitosa!", "msg_api_error": "❌ Error de Token",
        "msg_api_conn": "🚫 Error de Conexión", "msg_api_user": "Usuario",
        "msg_opt_title": "Opciones", "msg_opt_save_ok": "✅ Configuración guardada correctamente.\nLos cambios de fuente surtirán efecto al reiniciar.",
        "msg_opt_save_err": "❌ Fallo al guardar configuración:",
        "st_waiting": "  En Espera", "st_downloading": "  Descargando...",
        "st_completed": "  Finalizado ✅", "st_error": "  Error ❌",
        "st_verifying": "  Verificando...", "st_rotating": "  Rotando Hoster...",
        "st_paused": "  En Pausa", "st_manual_stop": "  Detenido Manualmente",
        "log_queue_start": "Iniciando descarga activa...", "log_retry": "Re-encolando para reintentar...",
        "log_unrestricting": "Solicitando desbloqueo a Real-Debrid...", "log_unrestrict_ok": "RD desbloqueó con éxito.",
        "log_unrestrict_fail": "RD rechazó el enlace.", "log_network_err": "Excepción de red al contactar con RD.",
        "log_hoster_dead": "Hoster caído o bloqueado. Omitiendo...", "log_rotate_ok": "Señal de rotación enviada.",
        "log_rotate_none": "Solo hay 1 enlace disponible, no se puede rotar.", "log_manual_start": "Reiniciando descarga por petición del usuario.",
        "log_manual_stop": "Descarga detenida por el usuario.", "log_removed": "Archivo eliminado de la lista.",
        "log_trunc_ok": "Truncado de seguridad para parcheo de integridad.", "log_trunc_err": "No se pudo truncar el archivo.",
        "log_connecting": "Conectando...", "log_reconnecting": "Reconectando...",
        "log_http_head": "HEAD para obtener tamaño...", "log_http_size": "Tamaño obtenido:",
        "log_cache_hit": "Archivo completo en disco. Finalizado.", "log_range": "Reanudando con Range HTTP.",
        "log_corrupt": "Archivo local corrupto. Borrando.", "log_tcp_start": "Conectando flujo de datos...",
        "log_range_ignored": "Servidor ignoró Range header. Descargando desde 0.", "log_stop_save": "Guardado seguro capturado. Parando.",
        "log_final_ok": "Transferencia completa.", "log_scheduler_coma": "Todos los hosters en coma. Planificando reintento.",
        "log_scheduler_kill": "Matando el hilo. El archivo no está disponible.",
        "prefix_sys": "SYS", "prefix_err": "ERR", "prefix_rotate": "ROTATE", "prefix_retry": "RETRY", "prefix_req": "REQ", "prefix_fix": "FIX", "prefix_http": "HTTP", "prefix_tcp": "TCP", "prefix_stop": "STOP", "prefix_range": "RANGE",
        "ctx_start_f": "▶️ Iniciar Descarga (Archivo)", "ctx_stop_f": "⏸️ Parar de Inmediato (Archivo)",
        "ctx_copy_n": "📋 Copiar Nombre:", "ctx_open_f": "📂 Abrir Carpeta Destino",
        "ctx_verify_f": "🔍 Verificar Integridad (Técnico)", "ctx_resume_f": "🛠️ Reanudar / Parchear Archivo",
        "ctx_rotate_f": "🔄 Forzar Rotación (Manual)", "ctx_remove_f": "❌ Eliminar de la Lista",
        "msg_select_f": "Selecciona al menos un archivo para descargar.", "msg_sub_f": "Define una Subcarpeta Final antes de iniciar.",
        "ver_file": "Archivo:", "ver_path": "Ruta Local:", "ver_size_loc": "Tamaño Local:",
        "ver_size_rem": "Tamaño Remoto:", "ver_diff": "Diferencia:", "ver_type": "Tipo Detectado:",
        "ver_header": "Firma Header:", "ver_md5": "Checksum MD5:", "ver_perfect": "0 bytes (Perfecto)",
        "prefix_notice": "Aviso", "msg_error_dlc": "Error DLC", "msg_select_dlc": "Selecciona al menos un archivo DLC válido",
        "lbl_footer": "Edición Profesional - Optimizado para operaciones Debrid de alta velocidad.",
        "st_processing": "  Procesando...", "msg_wait_log": "Esperando trazas de red (Selecciona fila en azul)...",
        "log_fail_alt": "Fallaron {} alternativas ({})",
        "msg_files_sel": "archivos seleccionados", "st_processing_dlc": "Procesando DLC..."
    },
    "en": {
        "tab_dl": "☁️ Downloads", "tab_opt": "⚙️ Options",
        "lbl_origin": "📦 Origin:", "lbl_dest": "📁 Destination:",
        "btn_browse": "Browse Multi...", "btn_load": "📥 Load to Table",
        "btn_start": "▶ Start Queue", "btn_stop": "⏹ Stop Full",
        "btn_toggle_all": "☑ Check / Uncheck All", "btn_show_log": "▼ Show Event Console",
        "btn_hide_log": "▲ Hide Event Console", "col_check": "[X]",
        "col_file": "  File", "col_progress": "  Progress",
        "col_size": "Size", "col_speed": "Speed", "col_status": "  Status",
        "opt_ui_title": "🎨 Visual Interface", "opt_lang": "Interface Language:",
        "opt_gui_size": "General UI Size:", "opt_cell_size": "Table Cell Size:",
        "opt_api_title": "🔑 Real-Debrid API Key", "opt_api_desc": "Private token to accelerate downloads automatically.",
        "opt_test": "🧪 Test", "opt_dir_title": "📁 Base Download Directory",
        "opt_dir_desc": "A smart subfolder will be created inside this directory.",
        "opt_adv_title": "⚙️ Advanced (Multi-thread Engine)", "opt_sim_dl": "Simultaneous downloads:",
        "opt_retry_chk": "Infinite Auto-Retry", "opt_retry_sec": "Auto-Retry Seconds:",
        "opt_save": "💾 Save Changes", "msg_wait_log": "Waiting for network traces...",
        "ctx_start": "Start", "ctx_stop": "Stop", "ctx_rotate": "Rotate Hoster",
        "ctx_verify": "Verify Integrity", "ctx_open": "Open Folder",
        "ctx_copy": "Copy Original Link", "ctx_report": "View MD5 Report",
        "log_verify": "Verifying MD5...", "log_error": "ERROR (Inconsistency)",
        "win_verify": "Technical Integrity Report", "win_status": "General Status:",
        "msg_api_title": "API Test", "msg_api_empty": "Please enter a token first.",
        "msg_api_ok": "🚀 Connection Successful!", "msg_api_error": "❌ Token Error",
        "msg_api_conn": "🚫 Connection Error", "msg_api_user": "User",
        "msg_opt_title": "Options", "msg_opt_save_ok": "✅ Config saved successfully.\nFont changes will apply after restart.",
        "msg_opt_save_err": "❌ Failed to save config:",
        "st_waiting": "  Waiting", "st_downloading": "  Downloading...",
        "st_completed": "  Finished ✅", "st_error": "  Error ❌",
        "st_verifying": "  Verifying...", "st_rotating": "  Rotating Hoster...",
        "st_paused": "  Paused", "st_manual_stop": "  Stopped Manually",
        "log_queue_start": "Starting active download...", "log_retry": "Re-queueing after failure to retry...",
        "log_unrestricting": "Requesting unlock from Real-Debrid...", "log_unrestrict_ok": "RD unlocked successfully.",
        "log_unrestrict_fail": "RD rejected the link. Error:", "log_network_err": "Network exception contacting RD.",
        "log_hoster_dead": "Hoster dead or blocked. Skipping...", "log_rotate_ok": "Rotation signal sent.",
        "log_rotate_none": "Only 1 link available, cannot rotate.", "log_manual_start": "Restarting download by user request.",
        "log_manual_stop": "Download stopped by user.", "log_removed": "File removed from list.",
        "log_trunc_ok": "Security truncate for integrity patching.", "log_trunc_err": "Failed to truncate file.",
        "log_connecting": "Connecting...", "log_reconnecting": "Reconnecting...",
        "log_http_head": "HEAD to obtain size...", "log_http_size": "Size obtained:",
        "log_cache_hit": "Full file on disk. Finished.", "log_range": "Resuming with HTTP Range.",
        "log_corrupt": "Local file corrupt. DELETING.", "log_tcp_start": "Connecting data stream...",
        "log_range_ignored": "Server ignored Range header. Downloading from 0.", "log_stop_save": "Safe save captured. Stopping.",
        "log_final_ok": "Transfer complete.", "log_scheduler_coma": "All hosters down. Scheduling retry.",
        "log_scheduler_kill": "Killing thread. File unavailable.",
        "prefix_sys": "SYS", "prefix_err": "ERR", "prefix_rotate": "ROTATE", "prefix_retry": "RETRY", "prefix_req": "REQ", "prefix_fix": "FIX", "prefix_http": "HTTP", "prefix_tcp": "TCP", "prefix_stop": "STOP", "prefix_range": "RANGE",
        "ctx_start_f": "▶️ Start Download (File)", "ctx_stop_f": "⏸️ Stop Immediately (File)",
        "ctx_copy_n": "📋 Copy Name:", "ctx_open_f": "📂 Open Destination Folder",
        "ctx_verify_f": "🔍 Verify Integrity (MD5)", "ctx_resume_f": "🛠️ Resume / Patch File",
        "ctx_rotate_f": "🔄 Force Hoster Rotation", "ctx_remove_f": "❌ Remove from List",
        "msg_select_f": "Select at least one file to download.", "msg_sub_f": "Set a Subfolder name before starting.",
        "ver_file": "File:", "ver_path": "Local Path:", "ver_size_loc": "Local Size:",
        "ver_size_rem": "Remote Size:", "ver_diff": "Difference:", "ver_type": "Detected Type:",
        "ver_header": "Header Signature:", "ver_md5": "MD5 Checksum:", "ver_perfect": "0 bytes (Perfect)",
        "lbl_origin": "📦 Origin:", "lbl_dest": "📁 Destination:", "btn_browse": "Browse Multi...",
        "prefix_notice": "Notice", "msg_error_dlc": "DLC Error", "msg_select_dlc": "Select at least one valid DLC file",
        "lbl_footer": "Professional Edition - Optimized for High-Speed Debrid Operations.",
        "st_processing": "  Processing...", "msg_wait_log": "Waiting for network traces (Select blue row)...",
        "log_fail_alt": "{} alternatives failed ({})"
    },
    "ru": {
        "tab_dl": "☁️ Загрузки", "tab_opt": "⚙️ Настройки",
        "lbl_origin": "📦 Источник:", "lbl_dest": "📁 Назначение:",
        "btn_browse": "Обзор...", "btn_load": "📥 Загрузить в таблицу",
        "btn_start": "▶ Запустить очередь", "btn_stop": "⏹ Остановить",
        "btn_toggle_all": "☑ Выбрать / Снять все", "btn_show_log": "▼ Показать консоль событий",
        "btn_hide_log": "▲ Скрыть консоль событий", "col_check": "[X]",
        "col_file": "  Файл", "col_progress": "  Прогресс",
        "col_size": "Размер", "col_speed": "Скорость", "col_status": "  Статус",
        "opt_ui_title": "🎨 Интерфейс", "opt_lang": "Язык интерфейса:",
        "opt_gui_size": "Размер интерфейса:", "opt_cell_size": "Размер ячеек таблицы:",
        "opt_api_title": "🔑 API Ключ Real-Debrid", "opt_api_desc": "Приватный токен для ускорения загрузок.",
        "opt_test": "🧪 Тест", "opt_dir_title": "📁 Базовая директория",
        "opt_dir_desc": "В этой папке будет создана умная поддиректория.",
        "opt_adv_title": "⚙️ Дополнительно (Движок)", "opt_sim_dl": "Одновременные закачки:",
        "opt_retry_chk": "Бесконечный повтор", "opt_retry_sec": "Секунды повтора:",
        "opt_save": "💾 Сохранить изменения", "msg_wait_log": "Ожидание сетевых трасс...",
        "ctx_start": "Запустить", "ctx_stop": "Остановить", "ctx_rotate": "Сменить хостер",
        "ctx_verify": "Проверить целостность", "ctx_open": "Открыть папку",
        "ctx_copy": "Копировать ссылку", "ctx_report": "Посмотреть MD5 отчет",
        "log_verify": "Проверка MD5...", "log_error": "ОШИБКА (Несоответствие)",
        "win_verify": "Отчет о технической целостности", "win_status": "Общий статус:",
        "msg_api_title": "Тест API", "msg_api_empty": "Сначала введите токен.",
        "msg_api_ok": "🚀 Соединение успешно!", "msg_api_error": "❌ Ошибка токена",
        "msg_api_conn": "🚫 Ошибка соединения", "msg_api_user": "Пользователь",
        "msg_opt_title": "Настройки", "msg_opt_save_ok": "✅ Настройки сохранены.\nИзменения шрифта вступят в силу после перезапуска.",
        "msg_opt_save_err": "❌ Не удалось сохранить настройки:",
        "st_waiting": "  В ожидании", "st_downloading": "  Загрузка...",
        "st_completed": "  Завершено ✅", "st_error": "  Ошибка ❌",
        "st_verifying": "  Проверка...", "st_rotating": "  Смена хостера...",
        "st_paused": "  Приостановлено", "st_manual_stop": "  Остановлено",
        "log_queue_start": "Запуск активной загрузки...", "log_retry": "Повторная постановка в очередь после сбоя...",
        "log_unrestricting": "Запрос разблокировки в Real-Debrid...", "log_unrestrict_ok": "RD успешно разблокировал.",
        "log_unrestrict_fail": "RD отклонил ссылку. Ошибка:", "log_network_err": "Сетевое исключение при связи с RD.",
        "log_hoster_dead": "Хостер мертв или заблокирован. Пропуск...", "log_rotate_ok": "Сигнал ротации отправлен.",
        "log_rotate_none": "Доступна только 1 ссылка, ротация невозможна.", "log_manual_start": "Перезапуск загрузки по запросу пользователя.",
        "log_manual_stop": "Загрузка остановлена пользователем.", "log_removed": "Файл удален из списка.",
        "log_trunc_ok": "Безопасная обрезка для исправления целостности.", "log_trunc_err": "Не удалось обрезать файл.",
        "log_connecting": "Установка соединения...", "log_reconnecting": "Переподключение...",
        "log_http_head": "HEAD для получения размера...", "log_http_size": "Размер получен:",
        "log_cache_hit": "Файл уже на диске. Завершено.", "log_range": "Возобновление через HTTP Range.",
        "log_corrupt": "Файл поврежден. УДАЛЕНИЕ.", "log_tcp_start": "Соединение с потоком данных...",
        "log_range_ignored": "Сервер игнорировал Range. Загрузка с 0.", "log_stop_save": "Безопасная остановка. Выход.",
        "log_final_ok": "Передача завершена.", "log_scheduler_coma": "Все хостеры недоступны. Планирование повтора.",
        "log_scheduler_kill": "Завершение потока. Файл недоступен.",
        "prefix_sys": "СИС", "prefix_err": "ОШИБ", "prefix_rotate": "РОТАЦИЯ", "prefix_retry": "ПОВТОР", "prefix_req": "ЗАПРОС", "prefix_fix": "ИСПР", "prefix_http": "HTTP", "prefix_tcp": "TCP", "prefix_stop": "СТОП", "prefix_range": "ДИАПАЗОН",
        "ctx_start_f": "▶️ Запустить (Файл)", "ctx_stop_f": "⏸️ Остановить (Файл)",
        "ctx_copy_n": "📋 Копировать имя:", "ctx_open_f": "📂 Открыть папку",
        "ctx_verify_f": "🔍 Проверить MD5", "ctx_resume_f": "🛠️ Исправить/Возобновить",
        "ctx_rotate_f": "🔄 Сменить хостер (Ручной)", "ctx_remove_f": "❌ Удалить из списка",
        "msg_select_f": "Выберите хотя бы один файл.", "msg_sub_f": "Укажите имя подпапки перед запуском.",
        "ver_file": "Файл:", "ver_path": "Локальный путь:", "ver_size_loc": "Локальный размер:",
        "ver_size_rem": "Удаленный размер:", "ver_diff": "Разница:", "ver_type": "Тип файла:",
        "ver_header": "Заголовок (Magic):", "ver_md5": "Хеш MD5:", "ver_perfect": "0 байт (Идеально)",
        "lbl_origin": "📦 Источник:", "lbl_dest": "📁 Путь:", "btn_browse": "Обзор...",
        "prefix_notice": "Уведомление", "msg_error_dlc": "Ошибка DLC", "msg_select_dlc": "Выберите хотя бы один действительный файл DLC",
        "lbl_footer": "Профессиональное издание - Оптимизировано для высокоскоростных операций Debrid.",
        "st_processing": "  Обработка...", "msg_wait_log": "Ожидание сетевых трасс (Выберите синюю строку)...",
        "log_fail_alt": "Сбой {} альтернатив ({})"
    },
    "zh": {
        "tab_dl": "☁️ 下载", "tab_opt": "⚙️ 设置",
        "lbl_origin": "📦 来源:", "lbl_dest": "📁 目标:",
        "btn_browse": "浏览多文件...", "btn_load": "📥 加载链接",
        "btn_start": "▶ 开始队列", "btn_stop": "⏹ 立即停止",
        "btn_toggle_all": "☑ 切换全部选择", "btn_show_log": "▼ 显示事件控制台",
        "btn_hide_log": "▲ 隐藏事件控制台", "col_check": "[X]",
        "col_file": "  文件名", "col_progress": "  进度",
        "col_size": "大小", "col_speed": "速度", "col_status": "  状态",
        "opt_ui_title": "🎨 视觉界面", "opt_lang": "界面语言:",
        "opt_gui_size": "整体界面大小:", "opt_cell_size": "表格单元格大小:",
        "opt_api_title": "🔑 Real-Debrid API 令牌", "opt_api_desc": "用于自动加速下载的专用令牌。",
        "opt_test": "🧪 测试", "opt_dir_title": "📁 基础下载目录",
        "opt_dir_desc": "在此目录内将创建一个智能子文件夹。",
        "opt_adv_title": "⚙️ 高级设置 (多线程引擎)", "opt_sim_dl": "同时下载数:",
        "opt_retry_chk": "无限自动重试", "opt_retry_sec": "自动重试秒数:",
        "opt_save": "💾 保存所有更改", "msg_wait_log": "等待网络跟踪 (请选择蓝色行)...",
        "ctx_start": "开始", "ctx_stop": "停止", "ctx_rotate": "更换主机",
        "ctx_verify": "验证完整性", "ctx_open": "打开文件夹",
        "ctx_copy": "复制原始链接", "ctx_report": "查看 MD5 报告",
        "log_verify": "正在验证 MD5...", "log_error": "错误 (数据不一致)",
        "win_verify": "技术完整性报告", "win_status": "全局状态:",
        "msg_api_title": "API 测试", "msg_api_empty": "请先输入令牌。",
        "msg_api_ok": "🚀 连接成功!", "msg_api_error": "❌ 令牌错误",
        "msg_api_conn": "🚫 连接错误", "msg_api_user": "用户",
        "msg_opt_title": "选项", "msg_opt_save_ok": "✅ 设置已成功保存并加密。\n字体更改将在重启后生效。",
        "msg_opt_save_err": "❌ 无法保存设置:",
        "st_waiting": "  等待中", "st_downloading": "  正在下载...",
        "st_completed": "  已完成 ✅", "st_error": "  错误 ❌",
        "st_verifying": "  正在验证...", "st_rotating": "  更换主机...",
        "st_paused": "  已暂停", "st_manual_stop": "  手动停止",
        "log_queue_start": "启动活动下载线程...", "log_retry": "失败后重新排队重试...",
        "log_unrestricting": "正在向 Real-Debrid 请求转换链接...", "log_unrestrict_ok": "RD 转换成功。",
        "log_unrestrict_fail": "RD 拒绝了该链接。错误:", "log_network_err": "联系 RD 时发生网络异常。",
        "log_hoster_dead": "主机无效或受限。正在跳过...", "log_rotate_ok": "已发送更换主机信号。",
        "log_rotate_none": "仅有一个可用链接，无法更换主机。", "log_manual_start": "根据用户请求重新开始下载。",
        "log_manual_stop": "用户已停止下载。", "log_removed": "文件已从列表中删除。",
        "log_trunc_ok": "安全截断以修补完整性。", "log_trunc_err": "无法截断文件。",
        "log_connecting": "正在建立连接...", "log_reconnecting": "正在重新连接...",
        "log_http_head": "HEAD 请求以获取大小...", "log_http_size": "获取的大小:",
        "log_cache_hit": "文件已在磁盘上。完成。", "log_range": "通过 HTTP Range 恢复下载。",
        "log_corrupt": "本地文件损坏。正在删除。", "log_tcp_start": "正在连接到数据流...",
        "log_range_ignored": "服务器忽略了 Range。从 0 开始下载。", "log_stop_save": "安全保存捕获。正在停止。",
        "log_final_ok": "传输已完成。", "log_scheduler_coma": "所有主机均不可用。正在安排重试。",
        "log_scheduler_kill": "终止线程。文件不可用。",
        "prefix_sys": "系统", "prefix_err": "错误", "prefix_rotate": "轮换", "prefix_retry": "重试", "prefix_req": "请求", "prefix_fix": "修复", "prefix_http": "HTTP", "prefix_tcp": "TCP", "prefix_stop": "停止", "prefix_range": "范围",
        "ctx_start_f": "▶️ 开始下载 (文件)", "ctx_stop_f": "⏸️ 立即停止 (文件)",
        "ctx_copy_n": "📋 复制名称:", "ctx_open_f": "📂 打开目标文件夹",
        "ctx_verify_f": "🔍 验证完整性 (MD5)", "ctx_resume_f": "🛠️ 恢复/修补文件",
        "ctx_rotate_f": "🔄 强制更换主机", "ctx_remove_f": "❌ 从列表中删除",
        "msg_select_f": "请选择至少一个文件进行下载。", "msg_sub_f": "开始前请设置子文件夹名称。",
        "ver_file": "文件名:", "ver_path": "本地路径:", "ver_size_loc": "本地大小:",
        "ver_size_rem": "远程大小:", "ver_diff": "差异:", "ver_type": "检测类型:",
        "ver_header": "文件头签名:", "ver_md5": "MD5 校验和:", "ver_perfect": "0 字节 (完美)",
        "lbl_origin": "📦 来源:", "lbl_dest": "📁 目标:", "btn_browse": "浏览多文件...",
        "prefix_notice": "提示", "msg_error_dlc": "DLC 错误", "msg_select_dlc": "请选择至少一个有效的 DLC 文件",
        "lbl_footer": "专业版 - 针对高速 Debrid 操作进行了优化。",
        "st_processing": "  正在处理...", "msg_api_title": "API 测试", "msg_api_empty": "请先输入令牌。",
        "msg_api_ok": "🚀 连接成功!", "msg_api_user": "用户", "msg_api_error": "❌ 令牌错误", "msg_api_conn": "🚫 连接错误",
        "msg_opt_title": "选项", "msg_opt_save_ok": "✅ 设置已成功保存并加密。\n字体更改将在重启后生效。",
        "msg_opt_save_err": "❌ 无法保存设置:",
        "msg_files_sel": "个文件已选择", "st_processing_dlc": "正在处理 DLC...",
        "log_fail_alt": "{} 个备选方案失败 ({})"
    }
}

class ModernContextMenu(ctk.CTkToplevel):
    def __init__(self, master, options, font_sz=14):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Menu frame with professional borders - NO FIXED WIDTH, let it expand
        self.frame = ctk.CTkFrame(self, fg_color="#1e1e1e", border_color="#333333", border_width=2, corner_radius=10)
        self.frame.pack(padx=1, pady=1, fill="both", expand=True)

        for text, command in options:
            if text == "---":
                sep = ctk.CTkFrame(self.frame, height=1, fg_color="#333333")
                sep.pack(fill="x", padx=10, pady=5)
                continue
            
            # Robust Split: clean emoji selectors and leading spaces
            parts = text.strip().split(" ", 1)
            icon = parts[0].replace("\ufe0f", "").strip() if len(parts) > 1 else ""
            label_text = parts[1].strip() if len(parts) > 1 else text.strip()
            
            # Row container with Grid for perfect alignment
            item_frame = ctk.CTkFrame(self.frame, fg_color="transparent", corner_radius=6, height=35)
            item_frame.pack(fill="x", padx=4, pady=1)
            item_frame.grid_columnconfigure(1, weight=1)
            
            # Col 0: Icon Zone (Absolute center, no margins)
            icon_lbl = ctk.CTkLabel(item_frame, text=icon, width=40,
                                    font=ctk.CTkFont(family=FONT_FAMILY, size=font_sz+2),
                                    text_color="#ffffff", anchor="center")
            icon_lbl.grid(row=0, column=0, sticky="nsew")
            
            # Col 1: Text Zone (Slimmer labels)
            text_lbl = ctk.CTkLabel(item_frame, text=label_text, 
                                    font=ctk.CTkFont(family=FONT_FAMILY, size=font_sz),
                                    text_color="#dddddd", anchor="w")
            text_lbl.grid(row=0, column=1, sticky="nwes", padx=(0, 10))
            
            # Interactive Events
            def make_on_enter(f): return lambda e: f.configure(fg_color="#1f538d")
            def make_on_leave(f): return lambda e: f.configure(fg_color="transparent")
            def make_on_click(cmd): return lambda e: self._on_click(cmd)

            for widget in [item_frame, icon_lbl, text_lbl]:
                widget.bind("<Enter>", make_on_enter(item_frame))
                widget.bind("<Leave>", make_on_leave(item_frame))
                widget.bind("<Button-1>", make_on_click(command))

    def show(self, x, y):
        self.update_idletasks()
        # Let Tkinter calculate the ideal size automatically (Shrink-wrap)
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.focus_force()
        
        # Robust Dismissal
        def _close(e=None):
            try: self.destroy()
            except: pass

        self.master.bind("<Button-1>", _close, add="+")
        self.master.bind("<Button-3>", _close, add="+")
        self.after(100, lambda: self.bind("<FocusOut>", _close))

    def _on_click(self, command):
        self.destroy()
        if command:
            command()

class VerificationWindow(ctk.CTkToplevel):
    def __init__(self, master, filename, report_data):
        super().__init__(master)
        self.title(f"{master.get_id_text('win_verify')}: {filename}")
        self.geometry("700x580")
        self.attributes("-topmost", True)
        self.configure(fg_color="#101114")
        
        # Centrar ventana
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        extra_x = (self.winfo_screenwidth() // 2) - (w // 2)
        extra_y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{extra_x}+{extra_y}")

        title_frame = ctk.CTkFrame(self, fg_color="#1a1c23", height=60, corner_radius=0)
        title_frame.pack(fill="x")
        
        status_icon = "✅" if report_data['status'] == "OK" else "❌" if report_data['status'] == "ERROR" else "⚠️"
        ctk.CTkLabel(title_frame, text=f"{status_icon} {master.get_id_text('win_verify')}", font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold")).pack(pady=15)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        def add_row(parent, label, value, color="white"):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color="#888", width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(family="Consolas" if "MD5" in label or "Ruta" in label else FONT_FAMILY, size=13), text_color=color, wraplength=450, justify="left").pack(side="left", fill="x")

        status_color = "#2da44e" if report_data['status'] == "OK" else "#d32f2f"
        add_row(content, f"{master.get_id_text('win_status')}", report_data['status_msg'], status_color)
        
        sep = ctk.CTkFrame(content, height=1, fg_color="#333")
        sep.pack(fill="x", pady=15)

        add_row(content, master.get_id_text("ver_file"), filename)
        add_row(content, master.get_id_text("ver_path"), report_data['path'])
        
        add_row(content, master.get_id_text("ver_size_loc"), f"{report_data['local_size_formatted']} ({report_data['local_size_bytes']} bytes)")
        add_row(content, master.get_id_text("ver_size_rem"), f"{report_data['remote_size_formatted']} ({report_data['remote_size_bytes']} bytes)")
        
        diff_color = "#2da44e" if report_data['size_match'] else "#d32f2f"
        diff_val = master.get_id_text("ver_perfect") if report_data['size_match'] else f"{report_data['size_diff']} bytes"
        add_row(content, master.get_id_text("ver_diff"), diff_val, diff_color)

        sep2 = ctk.CTkFrame(content, height=1, fg_color="#333")
        sep2.pack(fill="x", pady=15)
        
        add_row(content, master.get_id_text("ver_type"), report_data['mime_type'], "#3b82f6")
        add_row(content, master.get_id_text("ver_header"), report_data['magic_desc'])
        add_row(content, master.get_id_text("ver_md5"), report_data['md5'], "#a1a1a1")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=20)
        
        # Botón de cerrar (Siempre visible)
        btn_close = ctk.CTkButton(footer, text="Cerrar Informe", width=200, height=40, 
                                  font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), 
                                  command=self.destroy)
        
        if report_data['status'] == "ERROR":
            # Si hay error, mostrar botón de reparación inmediata (v4.2)
            btn_repair = ctk.CTkButton(footer, text="🛠️ Intentar Reparar (Parcheo)", width=220, height=40,
                                       fg_color="#1f538d", hover_color="#2666ae",
                                       font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                                       command=lambda: self._trigger_repair(master, filename))
            btn_repair.pack(side="left", padx=(30, 10), expand=True)
            btn_close.pack(side="left", padx=(10, 30), expand=True)
        else:
            btn_close.pack(expand=True)

    def _trigger_repair(self, master, filename):
        """Lanza la reparación desde el reporte y cierra la ventana."""
        if hasattr(master, "force_resume_by_filename"):
            master.force_resume_by_filename(filename)
        self.destroy()

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return "Error calculando MD5"

def detect_file_type(file_path):
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
            if header.startswith(b"Rar!\x1a\x07"): return "Archivo RAR", "Rar Signature Found"
            if header.startswith(b"PK\x03\x04"): return "Archivo ZIP / Office", "Standard PK Header"
            if header.startswith(b"7z\xbc\xaf"): return "Archivo 7-Zip", "7z Signature Found"
            if header.startswith(b"\x1f\x8b\x08"): return "Archivo GZIP", "GZIP Compression"
            if header.startswith(b"MZ"): return "Ejecutable (EXE/DLL)", "Windows PE Header"
            if header.startswith(b"\x25\x50\x44\x46"): return "Documento PDF", "PDF Reference"
            return "Binario Desconocido", f"Hex: {header.hex()[:8]}..."
    except:
        return "Error de Lectura", "N/A"

class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bandolero AutoDebrid - Pro Downloader v1.0.20260330")
        self.geometry("1400x850") # Mayor anchura para los logs detallados
        self.active_context_menu = None  # v5.0: Gestión de menú de instancia única
        
        # Inyectar icono personalizado en la barra de tareas y ventana (v4.6)
        import os
        try:
            # Magia oscura para arrancar el icono a Windows (separar proceso de python.exe)
            import ctypes
            myappid = 'bandolero.autodebrid.pro.final'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
            
        from PIL import Image, ImageTk
        icon_path = resource_path("app_icon.png")
        if os.path.exists(icon_path):
            try:
                # 1. Aplicarlo a las ventanas flotantes (Tkinter PhotoImage nativo)
                icon_img = ImageTk.PhotoImage(Image.open(icon_path))
                self.iconphoto(True, icon_img)
                
                # 2. Forzarlo agresivamente en la Barra de Tareas (Windows nativo requiere .ICO)
                ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
                if not os.path.exists(ico_path):
                    Image.open(icon_path).save(ico_path, format='ICO', sizes=[(256, 256)])
                self.iconbitmap(ico_path)
            except Exception as e:
                print(f"Error técnico cargando icono en barra: {e}")
        
        self.config = {
            "api_key": "",
            "base_dir": r"T:\Descargas",
            "max_workers": 3,
            "auto_retry": True,
            "font_size": 13,
            "tree_font_size": 14,
            "retry_delay": 10,
            "language": "es"
        }
        self.load_config()
        
        self.dlc_path = ctk.StringVar(value="")
        self._selected_dlc_paths = []
        
        self.var_api_key = ctk.StringVar(value=self.config.get("api_key", ""))
        self.var_base_dir = ctk.StringVar(value=self.config.get("base_dir", ""))
        self.var_max_workers = ctk.IntVar(value=self.config.get("max_workers", 3))
        self.var_auto_retry = ctk.BooleanVar(value=bool(self.config.get("auto_retry", True)))
        self.var_font_size = ctk.IntVar(value=self.config.get("font_size", 13))
        self.var_tree_font_size = ctk.IntVar(value=self.config.get("tree_font_size", 14))
        self.var_retry_delay = ctk.IntVar(value=self.config.get("retry_delay", 10))
        self.var_language = ctk.StringVar(value=self.config.get("language", "es"))
        self.var_subfolder = ctk.StringVar(value="")
        
        self.sz = self.var_font_size.get() 
        self.tsz = self.var_tree_font_size.get()
        
        self.links = [] # Ya no se usa directamente para la descarga, usamos filenames
        self.update_queue = queue.Queue()
        self.download_rows = {} # dict de filename -> datos (iid, checked, links)
        self.executor = None
        self.is_downloading = False
        self.stop_requested = False
        self.stopped_links = set()
        self.force_rotate = set()  # filenames that need a forced hoster rotation
        self.active_downloads_count = 0
        self.target_dir = "" 
        
        self.chk_all_state = True

        # ─────────────────────────────────────────────────────
        # ANCHOS DE COLUMNAS — Modifica aquí para ajustar todo
        # ─────────────────────────────────────────────────────
        self.COL_WIDTHS = {
            "check":     {"width": 50,  "minwidth": 50,  "stretch": False},
            "archivo":   {"width": 240, "minwidth": 140, "stretch": True},
            "progreso":  {"width": 380, "minwidth": 380, "stretch": False},
            "tamanio":   {"width": 230, "minwidth": 230, "stretch": False},
            "velocidad": {"width": 220, "minwidth": 220, "stretch": False},
            "resultado": {"width": 415, "minwidth": 415, "stretch": False},
        }
        # ─────────────────────────────────────────────────────
        
        # Cola Dinámica
        self.pending_queue = []
        self.running_filenames = set()
        self.session_file = "session.json"
        
        # Consola de Eventos
        self.logs_dict = {}
        self.iid_to_link = {}
        self.console_visible = False
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Cargar y preparar banner pirata profesional
        self.banner_img_path = resource_path("pirate_tech_banner_pro.png")
        self._prepare_banner_image()
        
        self._build_ui()
        self.load_session()
        self.after(100, self.process_queue)
        
        # Iniciar animación sutil (opcional en el futuro)
        self.after(1000, self._animate_watermark)

    def get_id_text(self, key):
        """Recupera la cadena traducida según el idioma configurado (v7.0)."""
        lang = self.var_language.get() if hasattr(self, "var_language") else "es"
        return LANG_DATA.get(lang, LANG_DATA["es"]).get(key, key)

    def _on_lang_change(self, new_val):
        """Actualización masiva de la interfaz al cambiar el idioma (v7.5)."""
        lang_map = {"Español": "es", "English": "en", "Русский": "ru", "中文": "zh"}
        lang_code = lang_map.get(new_val, "es")
        self.var_language.set(lang_code)
        self.config["language"] = lang_code
        self.save_config()
        
        # 1. Pestañas
        try:
            self.tabview._segmented_button._buttons_dict[self._tab_dl_id].configure(text=self.get_id_text("tab_dl"))
            self.tabview._segmented_button._buttons_dict[self._tab_opt_id].configure(text=self.get_id_text("tab_opt"))
        except Exception as e:
            print(f"Error actualizando pestañas: {e}")
        
        # 2. Pestaña de Descargas
        if hasattr(self, 'lbl_origen'): self.lbl_origen.configure(text=self.get_id_text("lbl_origin"))
        if hasattr(self, 'lbl_destino'): self.lbl_destino.configure(text=self.get_id_text("lbl_dest"))
        if hasattr(self, 'btn_browse'): self.btn_browse.configure(text=self.get_id_text("btn_browse"))
        if hasattr(self, 'btn_load'): self.btn_load.configure(text=self.get_id_text("btn_load"))
        if hasattr(self, 'btn_start'): self.btn_start.configure(text=self.get_id_text("btn_start"))
        if hasattr(self, 'btn_stop'): self.btn_stop.configure(text=self.get_id_text("btn_stop"))
        if hasattr(self, 'btn_toggle_all'): self.btn_toggle_all.configure(text=self.get_id_text("btn_toggle_all"))
        
        # 3. Consola
        if hasattr(self, 'btn_toggle_log'):
            log_text = self.get_id_text('btn_hide_log') if self.console_visible else self.get_id_text('btn_show_log')
            pref = "▲" if self.console_visible else "▼"
            self.btn_toggle_log.configure(text=f"{pref} {log_text}")
        
        # 4. Pestaña de Opciones
        if hasattr(self, 'lbl_opt_ui_title'): self.lbl_opt_ui_title.configure(text=self.get_id_text("opt_ui_title"))
        if hasattr(self, 'lbl_opt_lang'): self.lbl_opt_lang.configure(text=self.get_id_text("opt_lang"))
        if hasattr(self, 'lbl_opt_gui_size'): self.lbl_opt_gui_size.configure(text=self.get_id_text("opt_gui_size"))
        if hasattr(self, 'lbl_opt_cell_size'): self.lbl_opt_cell_size.configure(text=self.get_id_text("opt_cell_size"))
        if hasattr(self, 'lbl_opt_api_title'): self.lbl_opt_api_title.configure(text=self.get_id_text("opt_api_title"))
        if hasattr(self, 'lbl_opt_api_desc'): self.lbl_opt_api_desc.configure(text=self.get_id_text("opt_api_desc"))
        if hasattr(self, 'btn_test_api'): self.btn_test_api.configure(text=self.get_id_text("opt_test"))
        if hasattr(self, 'lbl_opt_dir_title'): self.lbl_opt_dir_title.configure(text=self.get_id_text("opt_dir_title"))
        if hasattr(self, 'lbl_opt_dir_desc'): self.lbl_opt_dir_desc.configure(text=self.get_id_text("opt_dir_desc"))
        if hasattr(self, 'btn_browse_conf'): self.btn_browse_conf.configure(text=self.get_id_text("btn_browse"))
        if hasattr(self, 'lbl_opt_adv_title'): self.lbl_opt_adv_title.configure(text=self.get_id_text("opt_adv_title"))
        if hasattr(self, 'lbl_opt_sim_dl'): self.lbl_opt_sim_dl.configure(text=self.get_id_text("opt_sim_dl"))
        if hasattr(self, 'chk_retry'): self.chk_retry.configure(text=self.get_id_text("opt_retry_chk"))
        if hasattr(self, 'lbl_opt_retry_sec'): self.lbl_opt_retry_sec.configure(text=self.get_id_text("opt_retry_sec"))
        if hasattr(self, 'btn_save_config'): self.btn_save_config.configure(text=self.get_id_text("opt_save"))
        
        # 5. Pie de página profesional
        if hasattr(self, 'lbl_footer'): self.lbl_footer.configure(text=self.get_id_text("lbl_footer"))

    def on_closing(self):
        """Protocolo de Cierre Total v5.4: Seguro, visible y compatible."""
        if getattr(self, "_closing_in_progress", False): return 
        self._closing_in_progress = True
        self.stop_requested = True
        self.is_downloading = False
        
        # Feedback Visual
        self.title("⚠️ Bandolero - Guardando y cerrando de forma segura... Espere.")
        try:
            if hasattr(self, 'btn_start'): self.btn_start.configure(state="disabled")
            if hasattr(self, 'btn_stop'): self.btn_stop.configure(state="disabled")
        except: pass
        self.update()
        
        # Guardado garantizado
        try:
            self.save_session()
            self.save_config()
        except Exception as e:
            print(f"Error al guardar al cerrar: {e}")
            
        # Espera de vaciado de buffers (max 3 segundos)
        wait_cycles = 30
        import time
        while self.running_filenames and wait_cycles > 0:
            try: self.update()
            except: pass
            time.sleep(0.1)
            wait_cycles -= 1
            
        # Apagado del motor (Compatible)
        if hasattr(self, 'executor') and self.executor:
            try:
                self.executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                self.executor.shutdown(wait=False)
                
        # Matar proceso para liberación de RAM
        try: self.destroy()
        except: pass
        import os
        os._exit(0)

    def save_session(self):
        """Guarda la tabla actual, la subcarpeta y los orígenes en disco."""
        session_data = {
            "subfolder": self.var_subfolder.get(),
            "source_paths": self._selected_dlc_paths,
            "files": []
        }
        for filename, data in self.download_rows.items():
            iid = data.get("iid")
            # Obtener el texto actual de la columna resultado (v5.0)
            status_text = self.tree.set(iid, "resultado") if iid else "  En Espera"
            
            session_data["files"].append({
                "filename": filename,
                "links": data["links"],
                "checked": data.get("checked", True),
                "resultado": status_text # Persistencia del informe técnico
            })
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=4)
        except Exception as e:
            print(f"Error guardando sesión: {e}")

    def load_session(self):
        """Carga la sesión previa si existe."""
        if not os.path.exists(self.session_file):
            return
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Restaurar metadatos generales
                if "subfolder" in data:
                    self.var_subfolder.set(data["subfolder"])
                
                if "source_paths" in data:
                    self._selected_dlc_paths = data["source_paths"]
                    count = len(self._selected_dlc_paths)
                    if count == 1:
                        self.dlc_path.set(self._selected_dlc_paths[0])
                    elif count > 1:
                        self.dlc_path.set(f"{count} {self.get_id_text('msg_files_sel')}")
                
                # Restaurar filas
                files = data.get("files", [])
                for f_data in files:
                    filename = f_data["filename"]
                    links = f_data["links"]
                    checked = f_data.get("checked", True)
                    # Restaurar el informe técnico (v5.0)
                    status = f_data.get("resultado", "  En Espera")
                    
                    # Deducción de tags para restaurar colores
                    tag = ()
                    if "OK" in status: tag = ("completed",)
                    elif "ERROR" in status: tag = ("failed",)
                    
                    # Crear fila en el treeview
                    iid = self.tree.insert("", "end", values=("[X]" if checked else "[  ]", f"  {filename}", "  [░░░░░░░░░░░░░░░░░░░░]   0% ", "-", "-", status), tags=tag)
                    
                    self.download_rows[filename] = {
                        "iid": iid,
                        "checked": checked,
                        "links": links,
                        "current_link_idx": 0
                    }
                    self.iid_to_link[iid] = filename
                    self.logs_dict[filename] = []
                    
            if files:
                if hasattr(self, 'btn_start'):
                    self.btn_start.configure(state="normal")
        except Exception as e:
            print(f"Error cargando sesión: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # Descifrar token si existe
                    if "api_key" in data:
                        data["api_key"] = self._deobfuscate(data["api_key"])
                    self.config.update(data)
            except Exception:
                pass

    def save_config(self):
        """Sincroniza la UI con la memoria y guarda en disco de forma segura (cifrada)."""
        # 1. Sincronizar memoria (SIEMPRE EN TEXTO PLANO)
        self.config["api_key"] = self.var_api_key.get().strip()
        self.config["base_dir"] = self.var_base_dir.get()
        self.config["max_workers"] = self.var_max_workers.get()
        self.config["auto_retry"] = self.var_auto_retry.get()
        self.config["font_size"] = self.var_font_size.get()
        self.config["tree_font_size"] = self.var_tree_font_size.get()
        self.config["retry_delay"] = self.var_retry_delay.get()
        self.config["language"] = self.var_language.get()

        try:
            # 2. Crear copia para cifrar antes de escribir (NO ensuciar la RAM)
            data_to_save = self.config.copy()
            data_to_save["api_key"] = self._obfuscate(data_to_save["api_key"])
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror(self.get_id_text("msg_opt_title"), f"{self.get_id_text('msg_opt_save_err')} {e}")
            return False

    def on_click_save_config(self):
        """Acción del botón manual con feedback visual."""
        if self.save_config():
            messagebox.showinfo(self.get_id_text("msg_opt_title"), self.get_id_text("msg_opt_save_ok"))

    def _obfuscate(self, text):
        """Cifrado profesional mediante Windows DPAPI (Grado Militar Local)."""
        if not text: return ""
        try:
            if win32crypt:
                # Cifrado vinculado al usuario y máquina de Windows
                crypted_data = win32crypt.CryptProtectData(text.encode(), "BandoDL", None, None, None, 0)
                return base64.b64encode(crypted_data).decode()
            else:
                # Fallback XOR (solo si no hay win32crypt)
                key = "BANDO_KEY_2024"
                xor_res = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
                return base64.b64encode(xor_res.encode()).decode()
        except:
            return text

    def _deobfuscate(self, crypted):
        """Descifrado robusto con detección de formato (DPAPI -> XOR -> Plain)."""
        if not crypted: return ""
        
        # 1. Intentar DPAPI (Windows)
        if win32crypt:
            try:
                decoded_bin = base64.b64decode(crypted)
                descr_data = win32crypt.CryptUnprotectData(decoded_bin, None, None, None, 0)
                return descr_data[1].decode()
            except:
                pass # No es un blob DPAPI válido, seguir al siguiente
        
        # 2. Intentar XOR (Legacy)
        try:
            key = "BANDO_KEY_2024"
            decoded_bin = base64.b64decode(crypted)
            decoded_str = decoded_bin.decode()
            # Si el resultado del XOR tiene caracteres muy extraños, probablemente no era XOR
            res = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(decoded_str))
            # Verificación básica: un token de RD suele ser alfanumérico
            if all(c.isalnum() or c in ".-_" for c in res[:10]):
                return res
        except:
            pass
            
        # 3. Si todo falla, devolver tal cual
        return crypted

    def _apply_treeview_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")  # Cambiamos a 'clam' para romper la rigidez de Windows
        bg_color = "#2b2b2b"
        fg_color = "white"
        
        rh = int(self.tsz * 2 + 10)
        style.configure("Treeview", 
                        background=bg_color,
                        foreground=fg_color,
                        rowheight=rh,
                        fieldbackground=bg_color,
                        bordercolor="#1a1c23",
                        borderwidth=0,
                        font=("Consolas", self.tsz))
        
        # Configuración de Selección Manual v3.0: Deshabilitamos el azul nativo de Windows (el culpable del color blanco)
        style.map('Treeview', background=[], foreground=[])
        
        # Tags de estado definitivos (Sin bold, persistentes al click en clam)
        self.tree.tag_configure('verifying', foreground="#FFD700")  # Oro
        self.tree.tag_configure('completed', foreground="#2da44e")  # Verde
        self.tree.tag_configure('failed', foreground="#e5534b")     # Rojo
        self.tree.tag_configure('selected', background="#3d424b")   # Gris sutil para selección manual
        
        style.configure("Treeview.Heading", 
                        background="#333333", 
                        foreground="white", 
                        relief="flat", 
                        font=(FONT_FAMILY, self.tsz, "bold"))  # Cabeceras sí usan Montserrat
        style.map("Treeview.Heading", background=[('active', '#444444')])

    def _prepare_banner_image(self):
        """Prepara el banner con ZOOM manual e INYECCIÓN de texto con sombra (v5.7)."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            full_img = Image.open(self.banner_img_path)
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
            
            # --- ESTILO STUDIO (v5.9): MONTSERRAT BOLD + HYBRID EMOJI ---
            draw = ImageDraw.Draw(banner_crop)
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
            
            # Paleta Laser Blue (v5.9)
            COLOR_MAIN = "#00f2ff" # Neon Cyan
            COLOR_SUB = "#afeeee"  # Pale Turquoise (Legibilidad máx)
            COLOR_OUTLINE = "black"
            
            def draw_studio_text(x, y, text, emoji, font, e_font, fill_color, out_color):
                # Calcular anchos para posicionamiento híbrido (v5.9)
                e_w = draw.textlength(emoji, font=e_font)
                t_w = draw.textlength(text, font=font)
                total_w = e_w + t_w
                
                # Dibujar Contorno Reforzado (2px Stroke - 8 direcciones)
                for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (0,-2), (0,2), (-2,0), (2,0)]:
                    # Dibujar Sombra del Emoji
                    draw.text((x - total_w + dx, y + dy), emoji, font=e_font, fill=out_color, anchor="lm")
                    # Dibujar Sombra del Texto
                    draw.text((x - total_w + e_w + dx, y + dy), text, font=font, fill=out_color, anchor="lm")
                
                # Dibujar Capa Principal
                draw.text((x - total_w, y), emoji, font=e_font, fill="white", anchor="lm") # Emoji en blanco nativo
                draw.text((x - total_w + e_w, y), text, font=font, fill=fill_color, anchor="lm")

            # Inyectar Título Studio (Hybrid)
            draw_studio_text(new_w - 40, banner_h//2 - 25, t1_text, t_emoji, f_title, f_emoji, COLOR_MAIN, COLOR_OUTLINE)
            
            # Dibujar Subtítulo (Montserrat Bold Cyan-ish)
            def draw_sub_legacy(x, y, text, font, fill, out):
                for dx, dy in [(-1,-1), (1,1), (-1,1), (1,-1)]:
                    draw.text((x + dx, y + dy), text, font=font, fill=out, anchor="rm")
                draw.text((x, y), text, font=font, fill=fill, anchor="rm")
            
            draw_sub_legacy(new_w - 40, banner_h//2 + 20, t2, f_sub, COLOR_SUB, COLOR_OUTLINE)
            
            self.header_bg_img = ctk.CTkImage(light_image=banner_crop, dark_image=banner_crop, size=(new_w, banner_h))
        except Exception as e:
            print(f"Error preparando banner: {e}")
            self.header_bg_img = None

    def _build_ui(self):
        # Header Profesional Unificado (Restaurado v5.7)
        self.header_frame = ctk.CTkFrame(self, fg_color="#0a0b0d", height=110, corner_radius=0)
        self.header_frame.pack(fill="x", padx=0, pady=0)
        
        if self.header_bg_img:
            self.banner_label = ctk.CTkLabel(self.header_frame, image=self.header_bg_img, text="")
            self.banner_label.place(relx=0.5, rely=0.5, anchor="center")

        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview._segmented_button.configure(font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz + 2, weight="bold"))
        self.tabview.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        
        self.tab_downloads = self.tabview.add(" Descargas")
        self.tab_options = self.tabview.add(" Opciones")
        self._tab_dl_id = " Descargas"
        self._tab_opt_id = " Opciones"
        
        # Aplicar textos iniciales según idioma cargado
        try:
            self.tabview._segmented_button._buttons_dict[self._tab_dl_id].configure(text=self.get_id_text("tab_dl"))
            self.tabview._segmented_button._buttons_dict[self._tab_opt_id].configure(text=self.get_id_text("tab_opt"))
        except: pass

        self._build_downloads_tab()
        self._build_options_tab()
        self._apply_treeview_style()
        
        # Vincular evento para selección manual (v3.0)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 4. Pie de página profesional (v7.5)
        self.lbl_footer = ctk.CTkLabel(self, text=self.get_id_text("lbl_footer"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz-1), text_color="#555")
        self.lbl_footer.pack(side="bottom", pady=5)

    def _animate_watermark(self):
        """Bucle de animación pasivo para mantener la cabecera limpia y profesional."""
        if self.stop_requested: return

        self.after(60, self._animate_watermark)

    def _build_downloads_tab(self):
        # PANEL DE CONTROL UNIFICADO (UX/USABILIDAD)
        control_panel = ctk.CTkFrame(self.tab_downloads, fg_color="#181a1f", corner_radius=10, border_width=1, border_color="#2a2d35")
        control_panel.pack(fill="x", padx=10, pady=(10, 5))
        
        control_panel.grid_columnconfigure(1, weight=1) # Permite a las cajas de texto estirarse dinámicamente

        # --- FILA 1: ORIGEN ---
        self.lbl_origen = ctk.CTkLabel(control_panel, text=self.get_id_text("lbl_origin"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"))
        self.lbl_origen.grid(row=0, column=0, padx=(15, 15), pady=(15, 5), sticky="e")
        
        self.entry_origen = ctk.CTkEntry(control_panel, textvariable=self.dlc_path, state="readonly", fg_color="#101114", border_color="#333", border_width=1, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.entry_origen.grid(row=0, column=1, padx=(0, 15), pady=(15, 5), sticky="ew")
        
        self.btn_browse = ctk.CTkButton(control_panel, text=self.get_id_text("btn_browse"), width=140, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz), fg_color="#383b40", hover_color="#4b5057", command=self.browse_dlc)
        self.btn_browse.grid(row=0, column=2, padx=(0, 15), pady=(15, 5))

        self.btn_load = ctk.CTkButton(control_panel, text=self.get_id_text("btn_load"), width=245, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"), fg_color="#1f538d", hover_color="#14375e", command=self.load_dlc_links)
        self.btn_load.grid(row=0, column=3, padx=(0, 15), pady=(15, 5), sticky="e")

        # --- FILA 2: DESTINO ---
        self.lbl_destino = ctk.CTkLabel(control_panel, text=self.get_id_text("lbl_dest"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"), text_color="#a1a1a1")
        self.lbl_destino.grid(row=1, column=0, padx=(15, 15), pady=(5, 15), sticky="e")
        
        self.entry_destino = ctk.CTkEntry(control_panel, textvariable=self.var_subfolder, fg_color="#101114", border_color="#333", border_width=1, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"), text_color="#2da44e")
        self.entry_destino.grid(row=1, column=1, padx=(0, 15), pady=(5, 15), sticky="ew")

        # Marco interior para agrupar Iniciar y Parar (ahora alineado en la columna 3)
        action_frame = ctk.CTkFrame(control_panel, fg_color="transparent")
        action_frame.grid(row=1, column=3, padx=(0, 15), pady=(5, 15), sticky="e")
        
        self.btn_start = ctk.CTkButton(action_frame, text=self.get_id_text("btn_start"), width=245, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"), fg_color="#2da44e", hover_color="#24823d", state="disabled", command=self.start_downloads)
        self.btn_start.pack(side="right")
        
        self.btn_stop = ctk.CTkButton(action_frame, text=self.get_id_text("btn_stop"), width=245, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"), fg_color="#d32f2f", hover_color="#b71c1c", command=self.stop_downloads)
        # Oculto por defecto al inicio
        self.btn_stop.pack_forget()

        # HERRAMIENTAS DE TABLA (Pegado encima del Treeview)
        tools_frame = ctk.CTkFrame(self.tab_downloads, fg_color="transparent")
        tools_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        self.btn_toggle_all = ctk.CTkButton(tools_frame, text=self.get_id_text("btn_toggle_all"), width=200, height=30, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz-1), fg_color="#2b2b2b", hover_color="#363636", command=self.toggle_all)
        self.btn_toggle_all.pack(side="right")
        
        self.btn_toggle_log = ctk.CTkButton(self.tab_downloads, text=self.get_id_text("btn_show_log"), 
                                            fg_color="#333", hover_color="#444", font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz, weight="bold"),
                                            command=self.toggle_console)
        self.btn_toggle_log.pack(side="bottom", fill="x", padx=5, pady=(5,0))
        
        self.log_container = ctk.CTkFrame(self.tab_downloads, height=220, fg_color="#101010", border_width=1, border_color="#444")
        self.log_textbox = ctk.CTkTextbox(self.log_container, font=ctk.CTkFont(family="Consolas", size=self.sz-1), 
                                          text_color="#4af626", fg_color="transparent")
        self.log_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_textbox.configure(state="disabled")
        
        tree_frame = ctk.CTkFrame(self.tab_downloads, fg_color="transparent")
        tree_frame.pack(side="top", fill="both", expand=True, padx=2, pady=(5, 2))
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        tree_scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        tree_scroll_x = ctk.CTkScrollbar(tree_frame, orientation="horizontal")
        
        self.tree = ttk.Treeview(tree_frame, columns=("check", "archivo", "progreso", "tamanio", "velocidad", "resultado"),
                                 show="headings")
        
        def yscroll_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                tree_scroll_y.grid_remove()
            else:
                tree_scroll_y.grid(row=0, column=1, sticky="ns")
            tree_scroll_y.set(first, last)
            
        def xscroll_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                tree_scroll_x.grid_remove()
            else:
                tree_scroll_x.grid(row=1, column=0, sticky="ew")
            tree_scroll_x.set(first, last)

        self.tree.configure(yscrollcommand=yscroll_set, xscrollcommand=xscroll_set)
        tree_scroll_y.configure(command=self.tree.yview)
        tree_scroll_x.configure(command=self.tree.xview)
        
        self.tree.grid(row=0, column=0, sticky="nsew")

        cw = self.COL_WIDTHS
        self.tree.heading("check", text=self.get_id_text("col_check"))
        self.tree.column("check", width=cw["check"]["width"], stretch=cw["check"]["stretch"], anchor="center", minwidth=cw["check"]["minwidth"])
        
        self.tree.heading("archivo", text=self.get_id_text("col_file"))
        self.tree.column("archivo", width=cw["archivo"]["width"], stretch=cw["archivo"]["stretch"], anchor="w", minwidth=cw["archivo"]["minwidth"])
        
        self.tree.heading("progreso", text=self.get_id_text("col_progress"))
        self.tree.column("progreso", width=cw["progreso"]["width"], stretch=cw["progreso"]["stretch"], anchor="w", minwidth=cw["progreso"]["minwidth"])
        
        self.tree.heading("tamanio", text=self.get_id_text("col_size"))
        self.tree.column("tamanio", width=cw["tamanio"]["width"], stretch=cw["tamanio"]["stretch"], anchor="w", minwidth=cw["tamanio"]["minwidth"])
        
        self.tree.heading("velocidad", text=self.get_id_text("col_speed"))
        self.tree.column("velocidad", width=cw["velocidad"]["width"], stretch=cw["velocidad"]["stretch"], anchor="w", minwidth=cw["velocidad"]["minwidth"])
        
        self.tree.heading("resultado", text=self.get_id_text("col_status"))
        self.tree.column("resultado", width=cw["resultado"]["width"], stretch=cw["resultado"]["stretch"], anchor="w", minwidth=cw["resultado"]["minwidth"])

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def force_resume_selected(self):
        """Parchea y reanuda todos los archivos seleccionados v1.0.20260330."""
        selection = self.tree.selection()
        if not selection: return
        
        for iid in selection:
            filename = self.tree.item(iid, 'values')[1].strip()
            if filename:
                self.force_resume_by_filename(filename)

    def force_resume_by_filename(self, filename):
        """Versión programática de la reanudación forzada para el botón de reporte (v4.2)."""
        if filename not in self.download_rows: return
        row_data = self.download_rows[filename]
        iid = row_data["iid"]
        
        sub_folder = self.var_subfolder.get().strip()
        base_dir = self.config["base_dir"]
        self.target_dir = os.path.join(base_dir, sub_folder)  # Asegurar directorio objetivo
        target_path = os.path.join(self.target_dir, filename)
        
        # Lógica de Parcheo v4.1/4.2
        if os.path.exists(target_path):
            current_size = os.path.getsize(target_path)
            trunc_size = min(50 * 1024 * 1024, int(current_size * 0.1))
            new_size = max(0, current_size - trunc_size)
            
            try:
                with open(target_path, "ab") as f:
                    f.truncate(new_size)
                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_fix')}] {self.get_id_text('log_trunc_ok')} ({self._format_size(trunc_size)})"))
            except Exception as e:
                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_err')}] {self.get_id_text('log_trunc_err')}: {e}"))
        
        os.makedirs(self.target_dir, exist_ok=True)
        
        row_data["checked"] = True
        self.tree.set(iid, "resultado", f"  ⏳ {self.get_id_text('st_waiting')} ({self.get_id_text('prefix_fix')})")
        self.tree.item(iid, tags=()) 
        
        # Iniciar solo esta descarga aislada (v4.3)
        self.is_downloading = True
        self.stop_requested = False
        
        if filename not in self.pending_queue and filename not in self.running_filenames:
            self.pending_queue.append(filename)
            self._check_and_launch_next()
            
        try: self.btn_start.pack_forget()
        except: pass
        try: self.btn_stop.pack(side="right")
        except: pass

    def verify_selected_file(self):
        """Lanza la verificación MD5 para todos los archivos seleccionados v1.0.20260330."""
        selection = self.tree.selection()
        if not selection: return
        
        for iid in selection:
            filename = self.tree.item(iid, 'values')[1].strip()
            if filename:
                threading.Thread(target=self._verify_worker, args=(filename,), daemon=True).start()

    def _verify_worker(self, filename):
        """Motor de verificación reubicado v1.0.20260330."""
        if filename not in self.download_rows: return
        row_data = self.download_rows[filename]
        iid = row_data["iid"]
        
        # Reconstruir ruta
        sub_folder = self.var_subfolder.get().strip()
        base_dir = self.config["base_dir"]
        local_path = os.path.join(base_dir, sub_folder, filename)
        
        if not os.path.exists(local_path):
            self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_err')}] {self.get_id_text('log_error')}: {local_path}"))
            return

        # Aplicar tag visual de carga y bandera interna (Amarillo Persistente)
        row_data["is_verifying"] = True
        self.tree.item(iid, tags=('verifying',))
        
        # Feedback Inmediato v2.8: Mostrar 0% para evitar sensación estática
        self.update_queue.put(("progress_full", filename, 0, row_data.get('filesize', 1), 0, f"{self.get_id_text('log_verify')} 0%"))
        
        # Quitar selección para que el color amarillo del tag sea visible (v1.0.20260330: solo si es individual, si no confundimos)
        if len(self.tree.selection()) <= 1:
            self.tree.selection_remove(iid)

        # Lógica de verificación interna (v1.0.20260330)
        try:
            local_bytes = os.path.getsize(local_path)
            remote_bytes = row_data.get('filesize', 0)
            
            # Motor de MD5 con reporte de progreso manual (Muestra barra amarilla)
            hash_md5 = hashlib.md5()
            checked_bytes = 0
            last_ui_update = time.time()
            
            with open(local_path, "rb") as f:
                # Usar bloques de 1MB para el reporte de progreso UI
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    hash_md5.update(chunk)
                    checked_bytes += len(chunk)
                    
                    now = time.time()
                    if now - last_ui_update > 0.5:
                        pct = checked_bytes / local_bytes if local_bytes > 0 else 0
                        self.update_queue.put(("progress_full", filename, checked_bytes, local_bytes, 0, f"{self.get_id_text('log_verify')} {int(pct*100)}%"))
                        last_ui_update = now
                
            final_md5 = hash_md5.hexdigest()
            mime, magic = detect_file_type(local_path)
            
            size_match = (local_bytes == remote_bytes) if remote_bytes > 0 else True
            
            report = {
                "status": "OK" if size_match else "ERROR",
                "status_msg": "Verificación Exitosa" if size_match else "Inconsistencia de Datos Detectada",
                "path": local_path,
                "local_size_bytes": local_bytes,
                "remote_size_bytes": remote_bytes,
                "local_size_formatted": self._format_size(local_bytes),
                "remote_size_formatted": self._format_size(remote_bytes) if remote_bytes > 0 else "Desconocido",
                "size_match": size_match,
                "size_diff": remote_bytes - local_bytes,
                "md5": final_md5,
                "mime_type": mime,
                "magic_desc": magic
            }
                
            # Restaurar estado visual y lanzar popup
            row_data["is_verifying"] = False
            final_tag = 'completed' if size_match else 'failed'
            self.after(0, lambda: self.tree.item(iid, tags=(final_tag,)))
            
            # Forzar barra al 100% y limpiar el residuo visual del 99% (v4.5)
            self.after(0, lambda: self.tree.set(iid, "progreso", "  [████████████████████] 100% "))
            
            # Aviso persistente en el resultado sin borrar el archivo (v4.0)
            status_msg = "OK" if size_match else self.get_id_text("log_error")
            self.after(0, lambda: self.tree.set(iid, "resultado", f"  {self.get_id_text('ctx_verify')} ({status_msg})"))
            self.after(0, lambda: VerificationWindow(self, filename, report))
                
        except Exception as e:
            row_data["is_verifying"] = False
            self.after(0, lambda: self.tree.item(iid, tags=()))
            self.after(0, lambda: messagebox.showerror(self.get_id_text("prefix_err"), f"Error: {e}"))

        
    def _build_options_tab(self):
        container = ctk.CTkFrame(self.tab_options, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=20)
        
        self.lbl_opt_ui_title = ctk.CTkLabel(container, text=self.get_id_text("opt_ui_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz + 4, weight="bold"))
        self.lbl_opt_ui_title.pack(anchor="w", pady=(0, 5))
        ui_frame = ctk.CTkFrame(container, fg_color="transparent")
        ui_frame.pack(anchor="w", fill="x", pady=(0, 30))
        
        # Selector de Idioma (v7.0)
        lang_frame = ctk.CTkFrame(ui_frame, fg_color="transparent")
        lang_frame.pack(anchor="w", fill="x", pady=2)
        self.lbl_opt_lang = ctk.CTkLabel(lang_frame, text=self.get_id_text("opt_lang"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.lbl_opt_lang.pack(side="left", padx=(0, 15))
        
        lang_rev_map = {"es": "Español", "en": "English", "ru": "Русский", "zh": "中文"}
        current_lang_name = lang_rev_map.get(self.var_language.get(), "Español")
        
        self.combo_lang = ctk.CTkOptionMenu(lang_frame, values=["Español", "English", "Русский", "中文"], 
                                            command=self._on_lang_change, width=150,
                                            font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.combo_lang.set(current_lang_name)
        self.combo_lang.pack(side="left")

        ui_frame_1 = ctk.CTkFrame(ui_frame, fg_color="transparent")
        ui_frame_1.pack(anchor="w", fill="x", pady=5)
        self.lbl_opt_gui_size = ctk.CTkLabel(ui_frame_1, text=self.get_id_text("opt_gui_size"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.lbl_opt_gui_size.pack(side="left", padx=(0, 15))
        ctk.CTkSlider(ui_frame_1, from_=10, to=24, number_of_steps=14, variable=self.var_font_size, width=200).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(ui_frame_1, textvariable=self.var_font_size, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz+1, weight="bold"), width=30).pack(side="left", padx=(0, 40))

        ui_frame_2 = ctk.CTkFrame(ui_frame, fg_color="transparent")
        ui_frame_2.pack(anchor="w", fill="x", pady=2)
        self.lbl_opt_cell_size = ctk.CTkLabel(ui_frame_2, text=self.get_id_text("opt_cell_size"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.lbl_opt_cell_size.pack(side="left", padx=(0, 15))
        ctk.CTkSlider(ui_frame_2, from_=10, to=30, number_of_steps=20, variable=self.var_tree_font_size, width=200).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(ui_frame_2, textvariable=self.var_tree_font_size, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz+1, weight="bold"), width=30).pack(side="left", padx=(0, 40))

        self.lbl_opt_api_title = ctk.CTkLabel(container, text=self.get_id_text("opt_api_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz + 4, weight="bold"))
        self.lbl_opt_api_title.pack(anchor="w", pady=(0, 5))
        self.lbl_opt_api_desc = ctk.CTkLabel(container, text=self.get_id_text("opt_api_desc"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz), text_color="gray")
        self.lbl_opt_api_desc.pack(anchor="w", pady=(0, 15))
        
        api_row = ctk.CTkFrame(container, fg_color="transparent")
        api_row.pack(anchor="w", fill="x", pady=(0, 30))
        ctk.CTkEntry(api_row, textvariable=self.var_api_key, width=450, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz), show="*").pack(side="left", padx=(0, 15))
        self.btn_test_api = ctk.CTkButton(api_row, text=self.get_id_text("opt_test"), width=110, height=35, fg_color="#333", command=self.test_api_key)
        self.btn_test_api.pack(side="left")
        
        self.lbl_opt_dir_title = ctk.CTkLabel(container, text=self.get_id_text("opt_dir_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz + 4, weight="bold"))
        self.lbl_opt_dir_title.pack(anchor="w", pady=(0, 5))
        self.lbl_opt_dir_desc = ctk.CTkLabel(container, text=self.get_id_text("opt_dir_desc"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz), text_color="gray")
        self.lbl_opt_dir_desc.pack(anchor="w", pady=(0, 15))
        
        dir_frame = ctk.CTkFrame(container, fg_color="transparent")
        dir_frame.pack(anchor="w", fill="x", pady=(0, 30))
        ctk.CTkEntry(dir_frame, textvariable=self.var_base_dir, width=500, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz)).pack(side="left", padx=(0, 15))
        self.btn_browse_conf = ctk.CTkButton(dir_frame, text=self.get_id_text("btn_browse"), width=110, height=35, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz), fg_color="#444", hover_color="#555", command=self.browse_base_dir)
        self.btn_browse_conf.pack(side="left")
        
        self.lbl_opt_adv_title = ctk.CTkLabel(container, text=self.get_id_text("opt_adv_title"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz + 4, weight="bold"))
        self.lbl_opt_adv_title.pack(anchor="w", pady=(0, 15))
        adv_frame = ctk.CTkFrame(container, fg_color="transparent")
        adv_frame.pack(anchor="w", fill="x", pady=(0, 10))
        
        self.lbl_opt_sim_dl = ctk.CTkLabel(adv_frame, text=self.get_id_text("opt_sim_dl"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.lbl_opt_sim_dl.pack(side="left", padx=(0, 15))
        ctk.CTkSlider(adv_frame, from_=1, to=10, number_of_steps=9, variable=self.var_max_workers, width=200).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(adv_frame, textvariable=self.var_max_workers, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz+1, weight="bold"), width=30).pack(side="left", padx=(0, 40))
        
        self.chk_retry = ctk.CTkCheckBox(adv_frame, text=self.get_id_text("opt_retry_chk"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz), checkbox_width=24, checkbox_height=24, variable=self.var_auto_retry)
        self.chk_retry.pack(side="left", padx=(0, 10))

        retry_frame = ctk.CTkFrame(container, fg_color="transparent")
        retry_frame.pack(anchor="w", fill="x", pady=(0, 40))
        
        self.lbl_opt_retry_sec = ctk.CTkLabel(retry_frame, text=self.get_id_text("opt_retry_sec"), font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz))
        self.lbl_opt_retry_sec.pack(side="left", padx=(0, 15))
        ctk.CTkSlider(retry_frame, from_=5, to=120, number_of_steps=115, variable=self.var_retry_delay, width=200).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(retry_frame, textvariable=self.var_retry_delay, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz+1, weight="bold"), width=30).pack(side="left", padx=(0, 40))

        self.btn_save_config = ctk.CTkButton(container, text=self.get_id_text("opt_save"), width=250, height=45, font=ctk.CTkFont(family=FONT_FAMILY, size=self.sz+2, weight="bold"),
                                 fg_color="#1f538d", hover_color="#14375e", command=self.on_click_save_config)
        self.btn_save_config.pack(anchor="w")

    def test_api_key(self):
        token = self.var_api_key.get().strip()
        if not token:
            messagebox.showwarning(self.get_id_text("msg_api_title"), self.get_id_text("msg_api_empty"))
            return
            
        self.btn_test_api.configure(state="disabled", text="⌛ ...")
        
        def run_test():
            try:
                r = requests.get("https://api.real-debrid.com/rest/1.0/user", 
                                 headers={"Authorization": f"Bearer {token}"}, timeout=10)
                if r.status_code == 200:
                    user_data = r.json()
                    user_name = user_data.get('username', self.get_id_text("msg_api_user"))
                    self.after(0, lambda: messagebox.showinfo(self.get_id_text("msg_api_title"), f"{self.get_id_text('msg_api_ok')}\n{self.get_id_text('msg_api_user')}: {user_name}"))
                else:
                    self.after(0, lambda: messagebox.showerror(self.get_id_text("msg_api_title"), f"{self.get_id_text('msg_api_error')} ({r.status_code})"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(self.get_id_text("msg_api_title"), f"{self.get_id_text('msg_api_conn')}:\n{e}"))
            finally:
                self.after(0, lambda: self.btn_test_api.configure(state="normal", text=self.get_id_text("opt_test")))

        threading.Thread(target=run_test, daemon=True).start()

    def toggle_console(self):
        self.console_visible = not self.console_visible
        if self.console_visible:
            self.btn_toggle_log.configure(text=f"▲ {self.get_id_text('btn_hide_log')}")
            self.log_container.pack(side="bottom", fill="both", expand=False, padx=5, pady=5)
            self._on_tree_select(None)
        else:
            self.btn_toggle_log.configure(text=f"▼ {self.get_id_text('btn_show_log')}")
            self.log_container.pack_forget()

    def refresh_console(self, link):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        if link in self.logs_dict and self.logs_dict[link]:
            text_block = "\n".join(self.logs_dict[link])
            self.log_textbox.insert("1.0", text_block)
        else:
            self.log_textbox.insert("1.0", f"[{time.strftime('%H:%M:%S')}] {self.get_id_text('msg_wait_log')}")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _on_tree_select(self, event):
        """Manejador de selección manual v3.0: Pinta de gris la fila sin tocar el color del texto."""
        # Limpiar tag 'selected' de todas las filas
        all_items = self.tree.get_children()
        for item in all_items:
            current_tags = list(self.tree.item(item, "tags"))
            if "selected" in current_tags:
                current_tags.remove("selected")
                self.tree.item(item, tags=tuple(current_tags))
        
        # Aplicar a las nuevas seleccionadas
        selection = self.tree.selection()
        for iid in selection:
            current_tags = list(self.tree.item(iid, "tags"))
            if "selected" not in current_tags:
                current_tags.append("selected")
                self.tree.item(iid, tags=tuple(current_tags))
            
            # Refrescar consola si está visible
            if self.console_visible and iid in self.iid_to_link:
                self.refresh_console(self.iid_to_link[iid])

    def toggle_all(self):
        if self.is_downloading: return
        self.chk_all_state = not self.chk_all_state
        new_val = "[X]" if self.chk_all_state else "[  ]"
        self.btn_toggle_all.configure(text=self.get_id_text("btn_toggle_all"))
        
        for data in self.download_rows.values():
            data["checked"] = self.chk_all_state
            self.tree.set(data["iid"], "check", new_val)

    def on_tree_click(self, event):
        if self.is_downloading: return
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == '#1':
                iid = self.tree.identify_row(event.y)
                if iid:
                    for l, data in self.download_rows.items():
                        if data["iid"] == iid:
                            current = data["checked"]
                            data["checked"] = not current
                            new_val = "[X]" if not current else "[  ]"
                            self.tree.set(iid, "check", new_val)
                            break

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            # v1.0.20260330: Multi-selección inteligente
            # Si el clic es sobre algo ya seleccionado, mantenemos todo.
            # Si es sobre algo nuevo, limpiamos y seleccionamos solo ese.
            current_selection = self.tree.selection()
            if item not in current_selection:
                self.tree.selection_set(item)
            
            filename = self.tree.item(item, "values")[1].strip()
            
            options = [
                (self.get_id_text("ctx_start_f"), self._start_selected_file),
                (self.get_id_text("ctx_stop_f"), self._stop_selected_file),
                ("---", None),
                (f"{self.get_id_text('ctx_copy_n')} {filename[:25]}...", lambda: self.clipboard_clear() or self.clipboard_append(filename)),
                (self.get_id_text("ctx_open_f"), self.open_selected_folder),
                ("---", None),
                (self.get_id_text("ctx_verify_f"), self.verify_selected_file),
                (self.get_id_text("ctx_resume_f"), self.force_resume_selected),
                ("---", None),
                (self.get_id_text("ctx_rotate_f"), self.rotate_selected_link),
                (self.get_id_text("ctx_remove_f"), self.remove_selected_link)
            ]
            # Limpiar menu anterior antes de crear uno nuevo para evitar bloqueos
            if hasattr(self, 'active_context_menu') and self.active_context_menu:
                try: self.active_context_menu.destroy()
                except: pass

            self.active_context_menu = ModernContextMenu(self, options, font_sz=self.sz)
            self.active_context_menu.show(event.x_root, event.y_root)

    def _start_selected_file(self):
        """Reinicia o inicia la descarga de los archivos seleccionados v1.0.20260330."""
        selection = self.tree.selection()
        if not selection: return
        
        # Validación de subcarpeta destino (Seguridad v1.0.20260330)
        sub_name = self.var_subfolder.get().strip()
        if not sub_name:
            messagebox.showwarning(self.get_id_text("msg_api_title"), self.get_id_text("msg_sub_f"))
            return

        any_processed = False
        for iid in selection:
            filename = self.iid_to_link.get(iid)
            if filename:
                # Liberar si estaba detenido
                self.stopped_links.discard(filename)
                
                # Si no está corriendo, lo aseguramos en la cola
                if filename not in self.running_filenames:
                    if filename not in self.pending_queue:
                        self.pending_queue.append(filename)
                    
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_manual_start')}"))
                    self.tree.set(iid, "resultado", f"  ⏳ {self.get_id_text('st_waiting')} (Cola)")
                    self.tree.item(iid, tags=()) 
                    any_processed = True

        # Despertar motor incondicionalmente si hay selección válida
        self.is_downloading = True
        self.stop_requested = False
        self._check_and_launch_next()
        
        # Actualizar UI
        try: self.btn_start.pack_forget()
        except: pass
        try: self.btn_stop.pack(side="right")
        except: pass

    def _stop_selected_file(self):
        """Detiene de inmediato las descargas seleccionadas v1.0.20260330."""
        selection = self.tree.selection()
        if not selection: return
        
        for iid in selection:
            filename = self.iid_to_link.get(iid)
            if filename:
                self.stopped_links.add(filename)
                self.update_queue.put(('log', filename, f"[MANUAL] Descarga detenida por el usuario."))
                self.tree.set(iid, "resultado", "  Detenido Manualmente")
                self.tree.set(iid, "velocidad", "  0 KB/s")
                self.tree.item(iid, tags=('failed',)) # Color rojo/alerta

    def open_selected_folder(self):
        selection = self.tree.selection()
        if not selection: return
        iid = selection[0]
        filename = self.iid_to_link.get(iid)
        
        base_dir = self.var_subfolder.get().strip()
        final_dir = os.path.join(self.config["base_dir"], base_dir)
        
        if os.path.exists(final_dir):
            os.startfile(final_dir)
        else:
            self.update_queue.put(('log', filename, f"[SYS] Carpeta {final_dir} no existe todavía."))

    def remove_selected_link(self):
        """Elimina de la lista los enlaces seleccionados v1.0.20260330."""
        selection = self.tree.selection()
        if not selection: return
        
        for iid in selection:
            filename = self.iid_to_link.get(iid)
            if filename:
                if filename in self.download_rows:
                    del self.download_rows[filename]
                if filename in self.iid_to_link:
                    del self.iid_to_link[iid]
                if self.tree.exists(iid):
                    self.tree.delete(iid)
                self.update_queue.put(('log', filename, f"[SYS] Archivo eliminado de la lista por usuario."))
        
        self.update_stats()

    def pause_selected_link(self):
        selection = self.tree.selection()
        if not selection: return
        iid = selection[0]
        
        link_to_pause = None
        for l, data in self.download_rows.items():
            if data["iid"] == iid:
                link_to_pause = l
                break
                
        if link_to_pause:
            self.stopped_links.add(link_to_pause)
            self._reset_row_ui(link_to_pause, "⏸ Pausado individualmente")

    def resume_selected_link(self):
        selection = self.tree.selection()
        if not selection: return
        iid = selection[0]
        
        link_to_resume = None
        for l, data in self.download_rows.items():
            if data["iid"] == iid:
                link_to_resume = l
                break
                
        if link_to_resume:
            if link_to_resume in self.stopped_links:
                self.stopped_links.remove(link_to_resume)
            self._reset_row_ui(link_to_resume, "Reanudando...")
            
            if not self.stop_requested and self.executor:
                self.active_downloads_count += 1
                self.executor.submit(self._download_worker, link_to_resume)

    def browse_dlc(self):
        filenames = filedialog.askopenfilenames(title="Seleccionar Enlaces (DLC o TXT)", filetypes=[("Formatos Aceptados", "*.dlc;*.txt"), ("Archivos DLC", "*.dlc"), ("Listas Texto", "*.txt")])
        if filenames:
            self._selected_dlc_paths = filenames
            if len(filenames) == 1:
                self.dlc_path.set(filenames[0])
            else:
                self.dlc_path.set(f"{len(filenames)} {self.get_id_text('msg_files_sel')}")
            self.btn_load.configure(state="normal")
            
            # Autoguess subfolder name if empty
            if not self.var_subfolder.get():
                guess = os.path.splitext(os.path.basename(filenames[0]))[0]
                self.var_subfolder.set(guess)
            
    def browse_base_dir(self):
        folder = filedialog.askdirectory(title="Seleccionar Carpeta Base")
        if folder:
            self.var_base_dir.set(folder)
            
    def get_clean_name(self, link):
        match = re.search(r'([A-Za-z0-9_.-]+\.part[0-9]+\.rar|[A-Za-z0-9_.-]+\.rar|[A-Za-z0-9_.-]+\.iso)', link, re.IGNORECASE)
        if match: return match.group(1)
        parsed = urllib.parse.urlparse(link)
        base = os.path.basename(parsed.path)
        if ".html" in base: base = base.replace(".html", "")
        if ".htm" in base: base = base.replace(".htm", "")
        return base

    def load_dlc_links(self):
        if not self._selected_dlc_paths:
            messagebox.showwarning(self.get_id_text("prefix_notice"), self.get_id_text("msg_select_dlc"))
            return
            
        self.btn_load.configure(state="disabled", text=self.get_id_text("st_processing_dlc"))
        self.update()
        threading.Thread(target=self._worker_extract_multi_dlc, args=(self._selected_dlc_paths,), daemon=True).start()
        
    def _worker_extract_multi_dlc(self, paths):
        all_links = []
        try:
            for path in paths:
                ext = path.lower().split(".")[-1]
                if ext == "txt":
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = [l.strip() for l in f if l.strip() and l.strip().startswith('http')]
                        all_links.extend(lines)
                else:
                    with open(path, 'rb') as f:
                        response = requests.post('http://dcrypt.it/decrypt/upload', files={'dlcfile': f})
                    if response.status_code == 200:
                        match = re.search(r'<textarea>(.*?)</textarea>', response.text, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1).strip())
                            links = data.get('success', {}).get('links', [])
                            all_links.extend(links)
            
            if not all_links:
                self.update_queue.put(('links_failed', "No se encontró ningún enlace dentro de los archivos procesados."))
                return
                
            grouped = {}
            for l in all_links:
                name = self.get_clean_name(l)
                if name not in grouped: grouped[name] = []
                if l not in grouped[name]: grouped[name].append(l)
                
            self.update_queue.put(('multi_links_loaded', grouped))
        except Exception as e:
            self.update_queue.put(('links_failed', f"Fallo al contactar dcrypt.it: {e}"))

    def create_row_for_group(self, filename, group_links):
        bar_text = "  [░░░░░░░░░░░░░░░░░░░░]   0% "
        status_text = f"  {self.get_id_text('st_waiting')} ({len(group_links)} hoster/s)"
        iid = self.tree.insert("", "end", values=("[X]", f"  {filename}", bar_text, "-", "-", status_text))
        
        self.download_rows[filename] = {
            "iid": iid,
            "checked": self.chk_all_state,
            "links": list(group_links),
            "current_link_idx": 0
        }
        self.iid_to_link[iid] = filename
        self.logs_dict[filename] = []
        self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_row_init')}"))
        
    def _reset_row_ui(self, filename, status_text=None):
        """Resetea las columnas de progreso/tamaño/velocidad a estado inicial."""
        if status_text is None:
            status_text = self.get_id_text("st_waiting")
            
        if filename in self.download_rows:
            iid = self.download_rows[filename]["iid"]
            self.after(0, lambda: self.tree.set(iid, "progreso", "  [░░░░░░░░░░░░░░░░░░░░]   0% "))
            self.after(0, lambda: self.tree.set(iid, "tamanio", "-") if self.tree.exists(iid) else None)
            self.after(0, lambda: self.tree.set(iid, "velocidad", "-") if self.tree.exists(iid) else None)
            self.after(0, lambda: self.tree.set(iid, "resultado", f"  {status_text}") if self.tree.exists(iid) else None)
            self.after(0, lambda: self.tree.item(iid, tags=()) if self.tree.exists(iid) else None)

    def rotate_selected_link(self):
        """Señal de rotación para todos los hosters seleccionados v1.0.20260330."""
        selection = self.tree.selection()
        if not selection: return
        
        for iid in selection:
            filename = self.iid_to_link.get(iid)
            if filename and filename in self.download_rows:
                data = self.download_rows[filename]
                if len(data["links"]) > 1:
                    self.force_rotate.add(filename)
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_rotate')}] {self.get_id_text('log_rotate_ok')}"))
                    self._reset_row_ui(filename, self.get_id_text("st_rotating"))
                else:
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_rotate')}] {self.get_id_text('log_rotate_none')}"))

    def stop_downloads(self):
        self.stop_requested = True
        self.is_downloading = False
        
        # Limpiar estados de cola para permitir un reanudado limpio
        self.pending_queue.clear()
        self.running_filenames.clear()

        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.executor = None
            
        self.btn_stop.grid_remove() if hasattr(self.btn_stop, 'grid_info') else None
        try: self.btn_stop.pack_forget()
        except: pass
        self.btn_start.configure(text=self.get_id_text("btn_start"), state="normal")
        try: self.btn_start.pack(side="right")
        except: pass
        self.btn_load.configure(state="normal")
        self.btn_toggle_all.configure(state="normal")

    def start_downloads(self):
        selected_files = [f for f in self.download_rows.keys() if self.download_rows[f]["checked"]]
        if not selected_files:
            messagebox.showinfo(self.get_id_text("msg_api_title"), self.get_id_text("msg_select_f"))
            return
            
        sub_name = self.var_subfolder.get().strip()
        if not sub_name:
            messagebox.showwarning(self.get_id_text("msg_api_title"), self.get_id_text("msg_sub_f"))
            return
        
        base_dir = self.config["base_dir"]
        self.target_dir = os.path.join(base_dir, sub_name)
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            self.update_queue.put(("system_msg", f"{self.get_id_text('log_base_ok')} {self.get_id_text('lbl_dest')} {self.target_dir}"))
        except Exception as e:
            messagebox.showerror(self.get_id_text("msg_api_title"), f"{self.get_id_text('log_trunc_err')} {self.target_dir}\n{e}")
            return
            
        self.is_downloading = True
        self.stop_requested = False
        
        # En el modo dinámico, NO reseteamos current_running al completo si ya hay descargas.
        # Solo añadimos lo nuevo seleccionado a la cola de espera.
        for f in selected_files:
            if f not in self.running_filenames and f not in self.pending_queue:
                self.pending_queue.append(f)
                iid = self.download_rows[f]["iid"]
                status_txt = f"  ⏳ {self.get_id_text('st_waiting')} (Cola)"
                self.after(0, lambda i=iid, s=status_txt: self.tree.set(i, "resultado", s) if self.tree.exists(i) else None)
        
        self.stopped_links.clear()
        self.force_rotate.clear()
        
        try: self.btn_start.pack_forget()
        except: pass
        try: self.btn_stop.pack(side="right")
        except: pass
        
        # Mantenemos carga de DLCs abierta para añadir más en caliente
        self.btn_load.configure(state="normal")
        self.btn_toggle_all.configure(state="normal")
        
        # Lanzamos el motor de comprobación
        self._check_and_launch_next()

    def _check_and_launch_next(self):
        """Comprueba huecos en el executor y lanza el siguiente de la cola."""
        if self.stop_requested: return
        
        max_workers = self.config.get("max_workers", 3)
        while len(self.running_filenames) < max_workers and self.pending_queue:
            filename = self.pending_queue.pop(0)
            self.running_filenames.add(filename)
            
            if not self.executor:
                self.executor = ThreadPoolExecutor(max_workers=10) # Pool grande, el límite lo ponemos nosotros
            
            self.executor.submit(self._download_worker, filename)
            self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_queue')}] {self.get_id_text('log_queue_start')}"))
            
    def _resubmit_link(self, filename):
        if not self.stop_requested:
            if filename not in self.pending_queue and filename not in self.running_filenames:
                self.pending_queue.append(filename)
                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_retry')}] {self.get_id_text('log_retry')}"))
                self._check_and_launch_next()
            
    def _download_worker(self, filename):
        row_data = self.download_rows[filename]
        link_list = row_data["links"]
        api_key = self.config["api_key"]
        target_path = os.path.join(self.target_dir, filename)
        
        fatal_sys_err = ""
        host_success = False
        
        # EL GRAN BUCLE DEL ARRAY MULTI-HOSTER (Bala por Bala)
        for link_idx, direct_raw_link in enumerate(link_list):
            if self.stop_requested or filename in self.stopped_links: return
            
            # Comprobar señal de rotación manual: si alguien marcó este filename para rotar,
            # y ya estamos en un enlace distinto del primero, saltar al siguiente de golpe.
            if filename in self.force_rotate and link_idx == 0:
                # Reorganizamos el array: mover el primero al final para que el segundo sea el nuevo primero
                self.force_rotate.discard(filename)
                rotated = link_list[1:] + link_list[:1]
                row_data["links"] = rotated
                link_list = rotated
                direct_raw_link = link_list[0]
                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_rotate')}] {self.get_id_text('log_rotate_ok')}. {urllib.parse.urlparse(direct_raw_link).netloc}"))
            
            if filename in self.force_rotate:
                self.force_rotate.discard(filename)
            
            try:
                host_domain = urllib.parse.urlparse(direct_raw_link).netloc
            except:
                host_domain = "UnknownHoster"
            
            self.update_queue.put(('log', filename, f"\n[----- {self.get_id_text('log_attempt')} {link_idx+1}/{len(link_list)} | Hoster: {host_domain} -----]"))
            self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_req')}] {self.get_id_text('log_unrestricting')}"))
            self.update_queue.put(("result", filename, f"[{host_domain}] {self.get_id_text('st_rotating')}"))
            
            api_url = "https://api.real-debrid.com/rest/1.0/unrestrict/link"
            try:
                r = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}"}, data={"link": direct_raw_link}, timeout=15)
                if self.stop_requested or filename in self.stopped_links: return
                
                if r.status_code == 200:
                    data = r.json()
                    direct_link = data.get('download')
                    fsize = data.get('filesize', 0)
                    row_data['filesize'] = fsize # Guardar para verificación técnica posterior
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_unrestrict_ok')} ({host_domain})"))
                else:
                    try:
                        err_json = r.json()
                        err_txt = err_json.get('error', f'Cod: {r.status_code}')
                    except:
                        err_txt = f"Cod: {r.status_code}"
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_err')}] {self.get_id_text('log_unrestrict_fail')} {err_txt}"))
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_hoster_dead')}"))
                    self.update_queue.put(("result", filename, f"[{host_domain}] {err_txt} -> {self.get_id_text('st_rotating')}"))
                    fatal_sys_err = err_txt
                    continue
            except Exception as e:
                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_err')}] {self.get_id_text('log_network_err')} {e}"))
                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_hoster_dead')}"))
                self.update_queue.put(("result", filename, f"[{host_domain}] {self.get_id_text('st_error')} -> {self.get_id_text('st_rotating')}"))
                fatal_sys_err = "Sin Conexion RD"
                continue
                
            if not direct_link:
                self.update_queue.put(('log', filename, f"[FALLBACK] Enlace premium vacío para {host_domain}."))
                fatal_sys_err = "Enlace Vacio"
                continue
                
            # RD generó enlace premium. Ahora descargamos.
            max_retries = 3
            host_success_in_download = False
            
            for attempt in range(max_retries):
                if self.stop_requested or filename in self.stopped_links: return
                # Verificar rotación manual durante la descarga activa
                if filename in self.force_rotate:
                    self.force_rotate.discard(filename)
                    rotated = link_list[link_idx+1:] + link_list[:link_idx+1]
                    row_data["links"] = rotated
                    self.update_queue.put(('log', filename, f"[ROTATE] Rotación en caliente. Cortando {host_domain} y saltando al siguiente."))
                    self.update_queue.put(("result", filename, f"Rotación manual -> {urllib.parse.urlparse(rotated[0]).netloc}"))
                    fatal_sys_err = "Rotacion manual"
                    break
                
                try:
                    conn_text = self.get_id_text("log_connecting") if attempt == 0 else f"{self.get_id_text('log_reconnecting')} {attempt+1}/{max_retries}"
                    self.update_queue.put(("result", filename, f"[{host_domain}] {conn_text}"))
                    
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_http')}] {self.get_id_text('log_http_head')} ({host_domain})"))
                    head_resp = requests.head(direct_link, timeout=15)
                    if self.stop_requested or filename in self.stopped_links: return
                    
                    total_size = int(head_resp.headers.get('content-length', 0))
                    if total_size > 0:
                        # v4.4: Confiar en el Content-Length HTTP antes que en la metadata de la API RD (elimina falsos positivos)
                        row_data['filesize'] = total_size
                        
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_http')}] {self.get_id_text('log_http_size')} {total_size} bytes ({self._format_size(total_size)})."))
                    headers = {}
                    existing_size = 0
                    mode = 'wb'
                    
                    if os.path.exists(target_path):
                        existing_size = os.path.getsize(target_path)
                        if total_size > 0:
                            if existing_size == total_size:
                                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_cache_hit')}"))
                                self.update_queue.put(("progress_full", filename, total_size, total_size, 0, f"{self.get_id_text('st_completed')} ({host_domain})"))
                                self.update_queue.put(("decrease_active", filename))
                                self.update_queue.put(("worker_done", filename))
                                return
                            elif existing_size < total_size:
                                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_range')}] {self.get_id_text('log_range')} ({self._format_size(existing_size)})"))
                                headers['Range'] = f"bytes={existing_size}-"
                                mode = 'ab'
                            else:
                                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_err')}] {self.get_id_text('log_corrupt')}"))
                                os.remove(target_path)
                                existing_size = 0
                                
                    self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_tcp')}] {self.get_id_text('log_tcp_start')} ({host_domain})"))
                    response = requests.get(direct_link, headers=headers, stream=True, timeout=15)
                    response.raise_for_status()
                    
                    if response.status_code == 200 and existing_size > 0:
                        self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_range_ignored')}"))
                        existing_size = 0
                        mode = 'wb'
                    
                    block_size = 1024 * 64
                    downloaded = existing_size
                    start_time = time.time()
                    last_ui_update = start_time
                    
                    with open(target_path, mode) as f:
                        last_sync_bytes = downloaded
                        for chunk in response.iter_content(block_size):
                            if self.stop_requested or filename in self.stopped_links:
                                # Blindaje Atómico: Cerrar puntero antes de salir
                                f.flush()
                                os.fsync(f.fileno())
                                self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_stop')}] {self.get_id_text('log_stop_save')}"))
                                self.update_queue.put(("result", filename, self.get_id_text("st_paused") if filename in self.stopped_links else self.get_id_text("st_manual_stop")))
                                self.update_queue.put(("decrease_active", filename))
                                self.update_queue.put(("worker_done", filename))
                                return
                            
                            if filename in self.force_rotate:
                                # Rotación en caliente dentro del chunk loop
                                break
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Blindaje Anti-Corrupción v4.0: Volcado físico a disco cada 10MB
                                if downloaded - last_sync_bytes > 10 * 1024 * 1024:
                                    f.flush()
                                    os.fsync(f.fileno())
                                    last_sync_bytes = downloaded
                                
                                now = time.time()
                                if now - last_ui_update > 0.8:
                                    elapsed = now - start_time
                                    speed = (downloaded - existing_size) / elapsed if elapsed > 0 else 0
                                    pct = downloaded / total_size if total_size else 0
                                    self.update_queue.put(("progress_full", filename, downloaded, total_size, speed, f"Activo [{host_domain}]"))
                                    last_ui_update = now
                        else:
                            # Loop terminó normalmente (sin break)
                            self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_final_ok')} ({host_domain})"))
                            self.update_queue.put(("progress_full", filename, total_size, total_size, 0, f"{self.get_id_text('st_completed')} [{host_domain}]"))
                            self.update_queue.put(("decrease_active", filename))
                            self.update_queue.put(("worker_done", filename))
                            host_success_in_download = True
                            break
                    
                    # Si llegamos aquí con force_rotate activo, salir del retry loop
                    if filename in self.force_rotate:
                        fatal_sys_err = "Rotacion manual"
                        break
                    
                except requests.exceptions.HTTPError as he:
                    if self.stop_requested or filename in self.stopped_links: return
                    status_code = he.response.status_code if he.response is not None else '?'
                    self.update_queue.put(('log', filename, f"[HTTP {status_code}] Error desde {host_domain}. Reintentos restantes: {max_retries-attempt-1}"))
                    if str(status_code) == '503' and attempt < max_retries - 1:
                        self.update_queue.put(("result", filename, f"[{host_domain}] 503 Saturado. Esperando..."))
                        time.sleep(3)
                    else:
                        fatal_sys_err = f"HTTP {status_code}"
                        break
                except Exception as e:
                    err_str = str(e)
                    if self.stop_requested or filename in self.stopped_links: return
                    self.update_queue.put(('log', filename, f"[DROP] Socket caído con {host_domain}: {err_str[:80]}"))
                    if attempt < max_retries - 1:
                        self.update_queue.put(("result", filename, f"[{host_domain}] Reconectando..."))
                        time.sleep(3)
                    else:
                        fatal_sys_err = "TCP Timeout"
                        break

            if host_success_in_download:
                host_success = True
                break

        if not host_success:
            self._handle_worker_fail(filename, self.get_id_text("log_fail_alt").format(len(link_list), fatal_sys_err))
            self.update_queue.put(("worker_done", filename)) # NUEVO: Incluso si falla, liberar hueco

    def _handle_worker_fail(self, filename, reason="Error"):
        delay_sec = self.var_retry_delay.get()
        if self.config.get("auto_retry", True) and not self.stop_requested:
            self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_scheduler_coma')} ({delay_sec}s)"))
            err_msg_short = str(reason).replace("API Error (", "").replace(")", "")
            self.update_queue.put(("retry", filename, f"Err: {err_msg_short} - {delay_sec}s...", delay_sec))
        else:
            self.update_queue.put(('log', filename, f"[{self.get_id_text('prefix_sys')}] {self.get_id_text('log_scheduler_kill')}"))
            self.update_queue.put(("error", filename, reason))
            self.update_queue.put(("decrease_active", filename))

    def _format_size(self, bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0: return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"

    def process_queue(self):
        try:
            for _ in range(50):
                msg = self.update_queue.get_nowait()
                msg_type = msg[0]
                
                if msg_type == 'log':
                    filename, txt = msg[1], msg[2]
                    t_str = time.strftime("%H:%M:%S")
                    if filename not in self.logs_dict: self.logs_dict[filename] = []
                    self.logs_dict[filename].append(f"[{t_str}] {txt}")
                    if len(self.logs_dict[filename]) > 100:
                        self.logs_dict[filename].pop(0)
                        
                    if self.console_visible:
                        selected = self.tree.selection()
                        if selected and selected[0] in self.iid_to_link and self.iid_to_link[selected[0]] == filename:
                            self.refresh_console(filename)
                
                elif msg_type == 'multi_links_loaded':
                    grouped = msg[1]
                    self.btn_load.configure(text=self.get_id_text("btn_load"), state="normal")
                    if not grouped:
                        messagebox.showinfo(self.get_id_text("msg_api_title"), self.get_id_text("msg_api_empty"))
                    else:
                        for row in self.tree.get_children(): self.tree.delete(row)
                        self.download_rows.clear()
                        self.iid_to_link.clear()
                        
                        for fname in sorted(grouped.keys()):
                            links = grouped[fname]
                            self.create_row_for_group(fname, links)
                        self.btn_start.configure(state="normal", text=self.get_id_text("btn_start"))
                
                elif msg_type == 'links_failed':
                    self.btn_load.configure(text=self.get_id_text("btn_load"), state="normal")
                    messagebox.showerror(self.get_id_text("msg_error_dlc"), msg[1])
                    
                elif msg_type == 'status':
                    filename, status_text = msg[1], msg[2]
                    if filename in self.download_rows:
                        iid = self.download_rows[filename]["iid"]
                        self.tree.set(iid, "resultado", status_text)
                        
                elif msg_type == 'name':
                    filename, new_name = msg[1], msg[2]
                    if filename in self.download_rows:
                        iid = self.download_rows[filename]["iid"]
                        self.tree.set(iid, "archivo", new_name)
                        
                elif msg_type == 'progress_full':
                    filename, downloaded, total, speed, status_text = msg[1], msg[2], msg[3], msg[4], msg[5]
                    pct = (downloaded / total) if total > 0 else 0
                    filled = int(pct * 20)
                    filled = max(0, min(20, filled))
                    bar_text = "  [" + "█" * filled + "░" * (20 - filled) + f"] {int(pct*100):3d}% "
                    size_str = f" {self._format_size(downloaded)} / {self._format_size(total)} " if total > 0 else " - "
                    speed_str = f" {self._format_size(speed)}/s " if speed > 0 else " - "
                    status_padded = f"  {status_text}"
                    
                    if filename in self.download_rows:
                        iid = self.download_rows[filename]["iid"]
                        
                        # Lógica de Color Dinámico Blindada (v2.5 - Prioridad Absoluta Verificación)
                        data = self.download_rows[filename]
                        is_verif = data.get("is_verifying", False)
                        
                        if is_verif:
                            self.tree.item(iid, tags=('verifying',))
                        elif pct >= 1.0:
                            self.tree.item(iid, tags=('completed',))
                        else:
                            self.tree.item(iid, tags=())

                        self.tree.set(iid, "progreso", bar_text)
                        self.tree.set(iid, "tamanio", size_str)
                        self.tree.set(iid, "velocidad", speed_str)
                        self.tree.set(iid, "resultado", status_padded)
                
                elif msg_type == 'result':
                    filename, txt = msg[1], msg[2]
                    if filename in self.download_rows:
                        iid = self.download_rows[filename]["iid"]
                        self.tree.set(iid, "resultado", f"  {txt}")
                        
                elif msg_type == 'error':
                    filename, err_text = msg[1], msg[2]
                    if filename in self.download_rows:
                        iid = self.download_rows[filename]["iid"]
                        self.tree.set(iid, "resultado", err_text)
                        
                elif msg_type == 'retry':
                    filename, err_text, delay = msg[1], msg[2], msg[3]
                    if filename in self.download_rows:
                        iid = self.download_rows[filename]["iid"]
                        self.tree.set(iid, "resultado", err_text)
                    self.after(delay * 1000, lambda f=filename: self._resubmit_link(f))
                    
                elif msg_type == 'decrease_active':
                    # Esto ahora es decorativo o para el contador global. El motor real va por 'worker_done'
                    if not self.stop_requested and not self.pending_queue and len(self.running_filenames) == 0:
                        self.stop_downloads()
                        self.btn_start.configure(text=self.get_id_text("btn_start"))
                        
                elif msg_type == 'worker_done':
                    fname = msg[1]
                    if fname in self.running_filenames:
                        self.running_filenames.remove(fname)
                    self._check_and_launch_next()
                    self.save_session() # Aprovechamos para guardar progreso

                elif msg_type == 'system_msg':
                    pass
                        
        except queue.Empty:
            pass
            
        self.after(150, self.process_queue)

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
