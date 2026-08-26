# Pourbaix Studio R4 — Windows Quick Start

[English](USER_GUIDE.md) | [简体中文](USER_GUIDE.zh-CN.md)

1. Extract `PourbaixStudioR4-win64.zip` completely.
2. Keep `PourbaixStudioR4.exe` beside its `_internal` directory. Move or copy the complete `PourbaixStudioR4` folder, not the EXE alone.
3. Launch `PourbaixStudioR4.exe`. The portable package does not require a separate Python installation or administrator rights.
4. Open **API settings**, follow the Materials Project link, paste your API key, and optionally save it securely in Windows Credential Manager.
5. Enter a formula or choose up to four closed elements. H and O are open reservoirs and do not receive ratios or concentrations.
6. Set composition ratios, optional ion concentrations, solid filtering, pH range, and potential range; then choose **Generate diagram**.
7. Use the right sidebar to choose region fills and change labels, axes, major-tick increments, lines, view range, physical page size, DPI, or transparency. **Re-plot current result** applies these changes without another API request.
8. Export figures as PNG, SVG, or TIFF and boundary data as CSV, XLSX, or TXT.

![API key settings](tutorial/get%20API%20key%20first.png)

## Define a chemical system

- Enter a formula such as `TiO2` or select up to four non-H/O elements with **Choose elements**.
- Oxygen and hydrogen are open reservoirs. They are not assigned composition ratios or ion concentrations.
- For a multi-element system, edit the displayed ratios to define the desired closed-element composition, for example `Sb : Se = 2 : 3`.
- Enable **Advanced options** to edit solid filtering, ion concentrations, and the calculation pH/potential range. Concentrations are in mol/L.

## Generate and inspect the result

Select **Generate diagram** after changing any calculation input. This downloads the required Materials Project data and creates a new thermodynamic result. The center tabs provide the diagram, available regions, and boundary coordinates.

![TiO2 result and post-processing controls](tutorial/TiO2.png)

The plot toolbar provides reset, back/forward, pan, zoom, subplot adjustment, plot configuration, and save controls. **Focus Plot** temporarily hides both sidebars on smaller screens.

## Post-process without another API request

Use the right sidebar to:

- add or remove filled regions and set a color and opacity for each selected region;
- show or hide species labels and change their font, size, background, and transparency;
- edit X/Y axis titles, title fonts, and title sizes;
- control tick visibility, direction, length, width, major increments, minor ticks, and tick-label fonts;
- change equilibrium-domain and water-stability line styles;
- set the displayed pH and potential limits independently of the calculation range;
- set figure width/height in physical units and configure image DPI and transparency.

Choose **Re-plot current result** after changing these display settings. Re-plotting uses the current calculation snapshot and does not call Materials Project again.

## Export

- **Export Figure** supports PNG, SVG, and TIFF. PNG/TIFF use the selected DPI; transparency is optional.
- **Export Data** supports CSV, XLSX, and TXT and writes the plotted stability-domain boundary vertices.

Generate a current result before exporting. If calculation inputs change, generate again before exporting data under the new composition.

## Troubleshooting

- If a calculation fails, open **Diagnostics** and read the stage, category, and details. API keys are redacted.
- Authentication errors: reopen **API Settings** and verify the key.
- Network/MPContribs errors: confirm internet access and retry after a short interval; Materials Project services are external.
- Do not run the EXE directly inside the ZIP and do not move the EXE away from `_internal`.
- When replacing a release, extract the new ZIP into a new folder instead of copying it over an older package.

The application needs internet access only when querying Materials Project. A remembered API key belongs to the current Windows user and remains available if the application folder is moved. Do not place `mp_api_key.txt` in a folder that will be shared.

For a diagnostic import check, run this from PowerShell:

```powershell
.\PourbaixStudioR4.exe --self-test
```

Additional packaged checks are available with `--gui-smoke` and `--mpcontribs-smoke`.

Clean-machine acceptance for a final ZIP remains pending until that exact archive is tested on a separate Windows x64 computer without Python.

Official repository and future downloads: <https://github.com/ZiYingZhang/Pourbaix-Diagram-from-Materials-Project>
