# Pourbaix GUI R2 — Quick Start Guide (Windows)

This quick guide shows how to run the packaged Windows build, obtain your Materials Project API key online, run the app while connected to the internet, generate Pourbaix diagrams, export data/images, and collect logs for debugging.

## Contents
- `pourbaix_gui_R2.exe` — the application executable
- `_internal/` — runtime files required by the exe (keep this folder with the exe)
- `README_FOR_TESTERS.md` — additional tester notes
- `pourbaix_gui_R2_runtime.log` — runtime log (generated/updated when app runs)

> Note: This distribution intentionally does NOT include any API key file. Each user must obtain and configure their own Materials Project API key; do not share keys inside archives.

## 1. Extract and prepare
1. Extract `pourbaix_gui_R2-win64.zip` to a local folder (Desktop or Documents recommended).
2. Verify that `pourbaix_gui_R2.exe` and `_internal/` exist in the same folder. Do not move the exe out of the folder.

## 2. Obtain a Materials Project API key (online)
1. Register or sign in at the Materials Project website: https://materialsproject.org/
2. Visit your account/dashboard or API settings page to create or view your API key. See Materials Project documentation for details: https://next-gen.materialsproject.org/api

## 3. Provide your API key at runtime (recommended — avoid environment variables)
Materials Project API behavior may change over time. To avoid relying on environment variables or persistent local files, paste your current API key into the app each time you run it.

Steps:
1. Open the application.
2. At the top of the window there's an **API Key** field. Paste your Materials Project API key into that field.
3. The app will use the provided key for the current session. For privacy and to avoid stale keys, do not save keys to shared archives.

Important:
- Do NOT place your API key inside the distributed archive or share it in public channels. Keep your key private.
- The application requires internet access to query Materials Project online services.

## 4. Run the application
Recommended (shows console output):
```cmd
cd /d "C:\path\to\extracted\folder"
pourbaix_gui_R2.exe
```
Or double-click `pourbaix_gui_R2.exe` in Explorer.

## 5. Generate a Pourbaix diagram (basic steps)
1. Enter elements (comma-separated), e.g. `Ti,O`.
2. Enter ratios (comma-separated), e.g. `0.3333,0.6667`.
3. Enter pH range (e.g. `0,14`) and potential range (e.g. `-2,4`).
4. Click **Generate Pourbaix Diagram**.
5. Use UI controls to toggle labels, fills, and colors.

**Suggested quick test**: elements `Ti,O` and ratios `0.3333,0.6667`.

## 6. Exporting
- **Export Figure Image**: choose PNG/JPEG/TIFF/SVG and save. Default suggestions are provided.
- **Export Data**: choose CSV/Excel/Text and save. If a save fails, choose `Documents` or `Desktop` (user-writable locations) to avoid permissions issues.

## 7. Logs & diagnostics
- The app writes runtime logs to `pourbaix_gui_R2_runtime.log` in the application folder. This file contains errors and diagnostic information.
- To view the last 200 lines (PowerShell):
```powershell
Get-Content -Path "C:\path\to\extracted\folder\pourbaix_gui_R2_runtime.log" -Tail 200
```
- To show diagnostics from within the GUI, press the **Diagnostics** button.

## 8. Common troubleshooting
- App closes immediately: run from Command Prompt to see errors; check `pourbaix_gui_R2_runtime.log`; allow app through SmartScreen/antivirus.
- Export fails / file not found: save to `Documents` or `Desktop`; ensure `_internal/` is present; check log for permission errors.
- Missing DLL: install Microsoft Visual C++ Redistributable x64 if prompted.
- Network/API errors: ensure the machine can access the internet and the Materials Project API, and that your `MP_API_KEY` is correct.

## 9. What to collect when reporting a bug
When reporting a failure, please include:
- `pourbaix_gui_R2_runtime.log` (last ~200 lines)
- Screenshot of the UI and any error messages
- Exact elements, ratios, pH & potential ranges used
- The save path you attempted for data export (if export failed)

