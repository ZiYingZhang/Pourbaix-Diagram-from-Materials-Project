# -*- mode: python ; coding: utf-8 -*-

import os
import certifi

# Extra imports for dynamic dependency collection
try:
    import shapely
    try:
        from shapely import get_dlls  # Shapely >=2.0
    except Exception:  # Fallback for older versions
        get_dlls = None
except Exception:
    shapely = None
    get_dlls = None

def collect_datas(pkg_path, rel_target_root):
    """Collect structured data files preserving original package-relative layout.

    rel_target_root should normally be the top-level package name (e.g. 'pymatgen').
    This way runtime code that does os.path.join(os.path.dirname(__file__), 'xxx.json') still works.
    """
    out = []
    for root, dirs, files in os.walk(pkg_path):
        for file in files:
            if file.endswith(('.json', '.json.gz', '.yaml', '.yml', '.bz2', '.txt')):
                full_path = os.path.join(root, file)
                rel_path_inside_pkg = os.path.relpath(full_path, pkg_path)  # e.g. core/periodic_table.json.gz
                target_dir = os.path.join(rel_target_root, os.path.dirname(rel_path_inside_pkg))
                out.append((full_path, target_dir))
    return out

base = r'E:/Research Library/Data/materials project/pourbaix diagram/pourbaix_env/Lib/site-packages'

datas = []
# recursive data for pymatgen and emmet/core (preserve original package paths)
datas += collect_datas(os.path.join(base, 'pymatgen'), 'pymatgen')
datas += collect_datas(os.path.join(base, 'emmet', 'core'), os.path.join('emmet', 'core'))
# Include certifi CA bundle to avoid SSL trust issues in frozen exe
datas.append((certifi.where(), 'certifi'))
# Add rfc3987_syntax grammar file needed by mpcontribs / validators
grammar_file = os.path.join(base, 'rfc3987_syntax', 'syntax_rfc3987.lark')
if os.path.exists(grammar_file):
    datas.append((grammar_file, 'rfc3987_syntax'))

# explicit critical files
pt_json = os.path.join(base, 'pymatgen', 'core', 'periodic_table.json.gz')
if os.path.exists(pt_json):
    # Place directly under pymatgen/core (may already be included above, but keep idempotent)
    datas += [(pt_json, os.path.join('pymatgen', 'core'))]
else:
    # Fallback: try alternate site-packages path resolution
    alt = os.path.join(os.path.dirname(__file__), 'pourbaix_env', 'Lib', 'site-packages', 'pymatgen', 'core', 'periodic_table.json.gz')
    if os.path.exists(alt):
        datas += [(alt, os.path.join('pymatgen', 'core'))]

hidden = [
    # Existing declared dependencies
    'mpcontribs',
    'mpcontribs.client',
    'mp_api',
    'mp_api.client',
    'mp_api.client.mprester',
    'emmet.core',
    'requests',
    'urllib3',
    'charset_normalizer',
    'idna',
    'certifi',
    'pint',
    'monty',
    'rfc3987_syntax',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_qt5',
    'matplotlib.backends.qt_compat',
    # Added for robustness
    'numpy',
    'pandas',
    'shapely',
    'shapely.geometry',
    'shapely.ops',
    'pymatgen.analysis.pourbaix_diagram',
]

# Collect shapely / GEOS DLLs (prevents runtime GEOS not found errors when frozen)
shapely_binaries = []
if get_dlls:
    try:
        for dll_path in get_dlls():
            if os.path.isfile(dll_path):
                shapely_binaries.append((dll_path, '.'))
    except Exception:
        pass
elif shapely:
    # Fallback: attempt to locate libgeos*.dll in package directory
    try:
        shp_dir = os.path.dirname(shapely.__file__)
        for fn in os.listdir(shp_dir):
            if fn.lower().startswith('geos') and fn.lower().endswith('.dll'):
                shapely_binaries.append((os.path.join(shp_dir, fn), '.'))
    except Exception:
        pass

a = Analysis(
    ['pourbaix_gui_R2.py'],
    pathex=[],
    binaries=shapely_binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,  # keep as before for transparency of modules
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pourbaix_gui_R2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Disable UPX by default (less AV false positives / DLL issues). Set to True if you want compression.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # disable console for production build
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pourbaix_gui_R2'
)
