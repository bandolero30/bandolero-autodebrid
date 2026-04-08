# Bandolero AutoDebrid 🚀🚢💀⚡⚓
![App Preview](app_preview_final.png)


A professional and robust download manager designed to automate file retrieval via **Real-Debrid**, featuring full support for DLC containers, TXT lists, intelligent queue management, and a **surgical ZIP repair engine**.

> [!IMPORTANT]
> **External Service Requirement**: Bandolero is a bridge to Debrid services. It **requires an active Real-Debrid (AutoDebrid) API token** to function. This software does **NOT** implement native captcha solving; instead, it leverages the [Real-Debrid](https://real-debrid.com/) API to process protected links seamlessly.

---

## ✨ Key Features

- **Smart Queue Engine**: Manages simultaneous downloads while respecting your bandwidth limits. Excess files are automatically queued and processed in order.
- **Multi-Hoster Resilience**: Every file can have multiple sources. If a hoster fails (403, 503 errors, etc.), the engine automatically rotates to the next available mirror in the array.
- **Enterprise-Grade Encryption (DPAPI)**: Your **Real-Debrid API Token** is stored using the native Windows Data Protection API. It is encrypted specifically for your user account on your PC, making it unreadable even if the configuration file is compromised.
- **Session Persistence**: Automatically saves your download list, file selection state, and integrity reports. Upon reopening the app, everything resumes exactly where you left off.
- **Premium Modern UI**: Built with `CustomTkinter`, offering a sleek dark design, high-precision progress bars, a detailed event console with a professional hacker aesthetic, and a glassmorphism banner.
- **Seamless Registry Integration**: Custom Pirate Skull icon in the taskbar and a panoramic integrated header for a native software experience. 💀
- **On-the-Fly Hoster Rotation**: Encountering a slow hoster? Right-click any active download and select "Rotate Hoster" to switch servers instantly without losing progress.
- **Global Multilingual Support**: 100% localized interface, technical logs, and protocol traces in **Spanish (ES)**, **English (EN)**, **Russian (RU)**, and **Chinese (ZH)**.
- **Integrity Auditing — 2-Phase Verification**:
  - **Phase 1/2 (MD5 Checksum)**: Reads the entire file and verifies its digital fingerprint.
  - **Phase 2/2 (ZIP Structure)**: Scans every internal file of the ZIP archive for CRC errors, reporting the exact name and byte offset of each corrupted entry.
  - Live progress bar for both phases, with no UI freeze.
- **🔬 Surgical ZIP Repair Engine** *(New in v1.1.20260404.1)*:
  - Detects **all** corrupted files in a single verification pass (no more one-at-a-time repairs).
  - Downloads **only** the corrupt byte ranges and injects them precisely into the local file using binary streaming — zero RAM buffering, zero destructive operations.
  - Automatically re-verifies after repair.
  - **Smart Threshold**: If corruption exceeds 80% of the file, the engine recommends a full re-download instead, deleting the corrupt file and re-queuing cleanly.

---

## 📁 Project Structure

| File/Folder | Purpose |
| :--- | :--- |
| **`main.py`** | Entry point. Launches the application. |
| **`core/engine.py`** | Download workers, verification engine, surgical repair logic. |
| **`core/config.py`** | Global version, paths, and configuration constants. |
| **`ui/`** | All UI components: main window, mixins, modals, tooltips. |
| **`locales/`** | JSON translation files for ES, EN, RU, ZH. |
| **`utils/`** | Shared helpers (file size formatting, DPAPI, session I/O). |
| **`build_exe.ps1`** | PowerShell script to compile into a standalone `.EXE`. |
| **`requirements.txt`** | Python dependencies. |
| **`app_icon.ico`** | High-resolution icon for the Windows taskbar and executable. |
| **`pirate_tech_banner_pro.png`** | Official glassmorphism header asset. |

---

## ⚙️ Configuration & Execution Files

### `config.json` (User Preferences & Security)
This file stores your persistent settings, such as download limits, UI font sizes, and default directories.
- **API Token Storage**: Your Real-Debrid token is **NOT stored in plain text**. It is obfuscated and protected by Windows DPAPI.

### `session.json` (Download State Persistence)
This file acts as the "memory" of the application.
- It preserves your current file list, the status of each download, and whether a file is pending, completed, or failed.
- Verification progress is kept separately from download progress to avoid overwriting valid completion states.

---

## 🛠️ Installation & Setup

### 1. Clone or Download
Ensure all files are placed in a local directory.

### 2. Install Dependencies
Open a terminal (PowerShell or CMD) in the project folder and run:

```bash
pip install -r requirements.txt
```

*Core libraries: `customtkinter`, `requests`, `pywin32`, `Pillow`, and `pycryptodome`.*

---

## 🚀 How to Use

1. **Initial Setup**:
   - Navigate to the **⚙️ Options** tab.
   - Paste your **Real-Debrid API Token**.
   - Select the **Base Directory** for your downloads.
   - Click **💾 Save Options**.

2. **Loading Links**:
   - Click **📥 Load Links** and select your `.dlc` or `.txt` files.
   - The app will automatically group mirrors by filename.

3. **Downloading**:
   - Define a **Final Subfolder** name (e.g., the name of the game/package).
   - Use **▶ Start Selected** to download only checked files, or **▶ Start All** to queue everything.

4. **Verifying & Repairing**:
   - Right-click a completed file → **Verify Integrity**.
   - If errors are found, click **Attempt Repair** in the Technical Report window.
   - The engine handles everything automatically: surgical injection or full re-download, followed by automatic re-verification.

---

## 📦 Building the Executable (.EXE)

To generate a standalone Windows binary with a custom icon and no background console:

1. **Environment Setup**:
   ```powershell
   pip install customtkinter Pillow requests pyinstaller
   ```

2. **Run the Build Script**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File build_exe.ps1
   ```

3. **Output**:
   The final **`Bandolero_AutoDebrid_vX.Y.Z.exe`** will be generated in the **`dist/`** folder. This file is portable and contains all embedded assets.

---

## 🛡️ Privacy Policy

- **Token Security**: We use `win32crypt.CryptProtectData` to bind your session to your local machine.
- **Transparency**: Logs are shown in the event console for debugging purposes but are not stored or sent to any third-party services.

---

**v1.1.20260408 — Engineered for precision and high-efficiency download management.**
