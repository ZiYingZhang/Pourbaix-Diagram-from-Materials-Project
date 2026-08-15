# Pourbaix GUI R3.0 — Windows Quick Start

1. Download `pourbaix_gui_R3-win64.zip` from the GitHub R3.0 release and extract the whole archive.
2. Keep `pourbaix_gui_R3.exe` beside its `_internal` directory; do not move the executable alone.
3. Launch `pourbaix_gui_R3.exe`. No Python installation or administrator rights are required.
4. Paste your own Materials Project API key into the password field. Never add a key to the extracted folder before sharing it.
5. For a first calculation, keep the defaults: elements `Ti`, ratio `1.0`, pH `0,14`, and potential `-2,4` V versus SHE.
6. Add `H` or `O` to the element list only when needed for the API chemical system. Do not add ratios for H/O; they are open species and are excluded from `comp_dict`.

The application requires network access for Materials Project queries. Figure export supports PNG, JPEG, TIFF, and SVG. Boundary export supports CSV, XLSX, and tab-separated TXT.

Runtime logs are written to `%LOCALAPPDATA%\PourbaixGUI\logs\pourbaix_gui_R3_runtime.log`. API keys are not intentionally logged or packaged. For a diagnostic import check, run `pourbaix_gui_R3.exe --self-test` from PowerShell or Command Prompt and inspect the process exit code.

Clean-machine acceptance for the final archive remains Pending until the archive is tested on a separate Windows x64 machine without Python.

