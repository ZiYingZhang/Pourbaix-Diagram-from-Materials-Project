# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all, copy_metadata


project_root = os.path.dirname(os.path.abspath(SPEC))
datas = []
binaries = []
hiddenimports = []

for package in ("pymatgen", "mp_api", "mpcontribs", "emmet", "shapely"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

for distribution in (
    "mp-api",
    "mpcontribs-client",
    "pymatgen",
    "pymatgen-core",
    "emmet-core",
    "shapely",
    "certifi",
):
    try:
        datas += copy_metadata(distribution, recursive=True)
    except Exception:
        pass

hiddenimports += [
    "pymatgen.core.entries",
    "pymatgen.analysis.pourbaix_diagram",
    "pymatgen.entries.compatibility",
    "mp_api.client",
    "mp_api.client.mprester",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_qtagg",
    "openpyxl",
    "pandas",
    "certifi",
    "rfc3987_syntax",
]

a = Analysis(
    [os.path.join(project_root, "pourbaix_gui_R3.py")],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pourbaix_gui_R3",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="pourbaix_gui_R3",
)

