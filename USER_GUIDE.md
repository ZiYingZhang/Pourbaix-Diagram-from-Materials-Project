# Pourbaix Studio R4 — Windows Quick Start

1. Extract `PourbaixStudioR4-win64.zip` completely.
2. Keep `PourbaixStudioR4.exe` beside its `_internal` directory. Move or copy the complete `PourbaixStudioR4` folder, not the EXE alone.
3. Launch `PourbaixStudioR4.exe`. The portable package does not require a separate Python installation or administrator rights.
4. Open **API settings**, follow the Materials Project link, paste your API key, and optionally save it securely in Windows Credential Manager.
5. Enter a formula or choose up to four closed elements. H and O are open reservoirs and do not receive ratios or concentrations.
6. Set composition ratios, optional ion concentrations, solid filtering, pH range, and potential range; then choose **Generate diagram**.
7. Use the right sidebar to choose region fills and change labels, axes, major-tick increments, lines, view range, physical page size, DPI, or transparency. **Re-plot current result** applies these changes without another API request.
8. Export figures as PNG, SVG, or TIFF and boundary data as CSV, XLSX, or TXT.

The application needs internet access only when querying Materials Project. A remembered API key belongs to the current Windows user and remains available if the application folder is moved. Do not place `mp_api_key.txt` in a folder that will be shared.

For a diagnostic import check, run this from PowerShell:

```powershell
.\PourbaixStudioR4.exe --self-test
```

Clean-machine acceptance for a final ZIP remains pending until that exact archive is tested on a separate Windows x64 computer without Python.

Official repository and future downloads: <https://github.com/ZiYingZhang/Pourbaix-Diagram-from-Materials-Project>
