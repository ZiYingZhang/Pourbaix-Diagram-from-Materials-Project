Pourbaix GUI — Internal test distribution

Contents:
- pourbaix_gui_R2/  (the folder produced by PyInstaller `dist`)
  - pourbaix_gui_R2.exe
  - pourbaix_gui_R2_runtime.log
  - _internal/  (packaged internal modules and data)

Quick test steps (Windows):
1. Copy the entire `pourbaix_gui_R2` folder to a test Windows machine (no Python required).
2. Place your Materials Project API key as one of:
   - Environment variable `MP_API_KEY`, or
   - A file named `mp_api_key.txt` placed next to `pourbaix_gui_R2.exe` containing the key on a single line.
3. Double-click `pourbaix_gui_R2.exe` to run the GUI.
4. Use the GUI to generate a Pourbaix diagram for a simple chemsys (e.g., Ti-O or Sn-O). Try exporting CSV and figure.
5. If anything goes wrong, check `pourbaix_gui_R2_runtime.log` in the same folder for diagnostics. If you can, attach the log when reporting issues.

Notes:
- The app is a GUI-only build (no console). If it silently fails on launch, open `pourbaix_gui_R2_runtime.log` for the last error.
- Cache and log files are currently stored next to the executable. For multi-user deployment we recommend moving them to `%LOCALAPPDATA%`.
- Installer plan: after internal testing, we will create an NSIS installer and optionally code-sign the installer and executable.

Contact: the developer (you) for issues or to request signed/installer builds.
