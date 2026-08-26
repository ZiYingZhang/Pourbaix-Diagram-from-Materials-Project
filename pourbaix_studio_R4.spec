# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all, copy_metadata


project_root = os.path.dirname(os.path.abspath(SPEC))
datas = []
binaries = []
hiddenimports = []

datas += [(os.path.join(project_root, "assets", "pourbaix-studio-r4.png"), "assets")]

for package in ("pymatgen", "mp_api", "mpcontribs", "emmet", "shapely", "keyring"):
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
    "keyring",
    "certifi",
):
    try:
        datas += copy_metadata(distribution, recursive=True)
    except Exception:
        pass

hiddenimports += [
    "keyring.backends.Windows",
    "pymatgen.core.entries",
    "pymatgen.analysis.pourbaix_diagram",
    "pymatgen.entries.compatibility",
    "mp_api.client",
    "mp_api.client.mprester",
    "matplotlib.backends.backend_qtagg",
    "openpyxl",
    "pandas",
    "certifi",
    "rfc3987_syntax",
]

a = Analysis(
    [os.path.join(project_root, "pourbaix_studio_R4.py")],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PourbaixStudioR4",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(project_root, "assets", "pourbaix-studio-r4.ico"),
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
    name="PourbaixStudioR4",
)
