# Pourbaix-Diagram-from-Materials-Project

Pourbaix GUI R2 — PyQt5 desktop app to generate Pourbaix (pH–potential) diagrams using Materials Project via pymatgen. Interactive UI for multi‑element systems, tunable plot styling, and export of images and boundary data. The packaged Windows build includes the frozen executable and runtime files so non‑Python users can run the tool directly.

## Key features

- Interactive GUI for building Pourbaix diagrams (elements, ratios, pH/potential ranges)
- Export diagram images (PNG / JPEG / TIFF / SVG) and boundary data (CSV / XLSX / TXT)
- Robust handling of API fetches with local caching and sanitized ion records

## Quick start

1. Download and extract `pourbaix_gui_R2-win64.zip`.
2. Launch `pourbaix_gui_R2.exe` and paste your Materials Project API key into the API Key field.
3. Enter elements (comma separated) and ratios, set pH/potential ranges, then click “Generate Pourbaix Diagram”.
4. Use “Export Data” or “Export Figure Image” to save outputs to a writable folder (Documents/Desktop recommended).

## Notes

- The app requires internet access and a valid Materials Project API key. Do not distribute API keys with the package.
- If export fails, choose a user-writable folder (Documents or Desktop) and send `pourbaix_gui_R2_runtime.log` for debugging.
