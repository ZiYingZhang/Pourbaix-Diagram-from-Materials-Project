import sys, os, re, time, logging
from importlib.metadata import version
from typing import List

APP_VERSION = "R3.0"

_BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)

def _runtime_log_path():
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        local_app_data = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
    log_dir = os.path.join(local_app_data, 'PourbaixGUI', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'pourbaix_gui_R3_runtime.log')

log_path = _runtime_log_path()
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
_LOG = logging.getLogger("pourbaix_gui_R3")

def runtime_versions():
    return {
        distribution: version(distribution)
        for distribution in ("mp-api", "pymatgen", "pymatgen-core")
    }

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog, QFontComboBox, QComboBox, QCheckBox, QColorDialog, QCompleter)
from PyQt5.QtCore import QLocale
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram, PourbaixPlotter
from shapely.geometry import Polygon, box
import pandas as pd
import traceback

from pourbaix_core import fetch_pourbaix_entries, parse_inputs

# Lazy matplotlib backend selection
_SELECTED_BACKEND = None
def _ensure_matplotlib():
    global _SELECTED_BACKEND
    import matplotlib
    if _SELECTED_BACKEND is None:
        try:
            matplotlib.use('Qt5Agg')
            _SELECTED_BACKEND = 'Qt5Agg'
        except Exception:
            _SELECTED_BACKEND = matplotlib.get_backend()
    import matplotlib.pyplot as plt
    return plt

class PourbaixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pourbaix Diagram Automation Tool (R3.0)")
        # Default line colors (Hydrogen red, Oxygen blue)
        self.h_color = "#FF0000"
        self.o_color = "#0070C0"
        # Default region fill color
        self.fill_color_default = "#B0C4DE"
        # Ion label background fill defaults
        self.label_fill_default = "#FFFFFF"
        # Caching metrics
        self._entries_cache = {}
        self._cache_ttl = 300
        self._last_entries_count = 0
        self._last_sanitation_retry = False
        self._last_fetch_seconds = 0.0
        self._last_figure = None
        # Export / label caches
        self._last_labels = []  # cache of last stable species labels for auto-complete
        self._last_elements = []  # for export naming
        self._last_comp_dict = {}
        # Build UI
        self._build_ui_en()

    def open_api_url(self):
        import webbrowser
        webbrowser.open('https://next-gen.materialsproject.org/api')

    def _resolve_api_key(self) -> str:
        raw = self.api_input.text().strip()
        if not raw:
            raw = (os.environ.get('MP_API_KEY') or os.environ.get('MAPI_KEY') or os.environ.get('PMG_MAPI_KEY') or '')
        if not raw:
            try:
                key_path = os.path.join(_BASE_DIR, 'mp_api_key.txt')
                if os.path.exists(key_path):
                    with open(key_path, 'r', encoding='utf-8') as fh:
                        ln = fh.readline().strip()
                        if ln:
                            raw = ln
            except Exception:
                pass
        key = raw.strip().strip('"').strip("'")
        if key:
            os.environ['MP_API_KEY'] = key
            os.environ['MAPI_KEY'] = key
            os.environ['PMG_MAPI_KEY'] = key
        return key

    # --- UI helper methods (restored) ---
    def choose_fill_color_idx(self, idx: int):
        c = QColorDialog.getColor()
        if c.isValid():
            try:
                self.fill_color_btns[idx].setText(c.name())
            except Exception:
                pass

    def choose_h_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.h_color = c.name()
            try: self.h_color_btn.setText(self.h_color)
            except Exception: pass

    def choose_o_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.o_color = c.name()
            try: self.o_color_btn.setText(self.o_color)
            except Exception: pass

    def choose_label_fill_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            try: self.label_fill_color_btn.setText(c.name())
            except Exception: pass

    def _build_ui_en(self):
        layout = QVBoxLayout()

        def add_row(*widgets):
            row = QHBoxLayout()
            for w in widgets:
                row.addWidget(w)
            layout.addLayout(row)
            return row

        # Elements / ratios
        r = add_row(QLabel('Elements (comma separated):'))
        self.elements_input = QLineEdit('Ti'); r.addWidget(self.elements_input)
        r = add_row(QLabel('Ratios (comma separated):'))
        self.ratios_input = QLineEdit('1.0'); r.addWidget(self.ratios_input)
        # API key
        r = add_row(QLabel('API Key:'))
        self.api_input = QLineEdit(); self.api_input.setEchoMode(QLineEdit.Password); r.addWidget(self.api_input)
        self.api_btn = QPushButton('Get API Key'); self.api_btn.clicked.connect(self.open_api_url); r.addWidget(self.api_btn)
        # Ranges
        r = add_row(QLabel('pH Range (e.g. 0,14):'))
        self.ph_input = QLineEdit('0,14'); r.addWidget(self.ph_input)
        r = add_row(QLabel('Potential Range (e.g. -2,4):'))
        self.e_input = QLineEdit('-2,4'); r.addWidget(self.e_input)
        # Fonts
        r = add_row(QLabel('Ion label font:'))
        self.font_combo = QFontComboBox(); self.font_combo.setCurrentText('Arial'); r.addWidget(self.font_combo)
        r = add_row(QLabel('Ion label font size:'))
        self.fontsize_input = QLineEdit('22'); r.addWidget(self.fontsize_input)
        r = add_row(QLabel('Axis/tick font:'))
        self.axis_font_combo = QFontComboBox(); self.axis_font_combo.setCurrentText('Arial'); r.addWidget(self.axis_font_combo)
        r = add_row(QLabel('Axis/tick font size:'))
        self.axis_fontsize_input = QLineEdit('24'); r.addWidget(self.axis_fontsize_input)
        r = add_row(QLabel('X axis label:'))
        self.xlabel_input = QLineEdit('pH'); r.addWidget(self.xlabel_input)
        r = add_row(QLabel('X axis label size:'))
        self.xlabelsize_input = QLineEdit('28'); r.addWidget(self.xlabelsize_input)
        r = add_row(QLabel('Y axis label:'))
        self.ylabel_input = QLineEdit('E (V vs. SHE)'); r.addWidget(self.ylabel_input)
        r = add_row(QLabel('Y axis label size:'))
        self.ylabelsize_input = QLineEdit('28'); r.addWidget(self.ylabelsize_input)
        # Widths (spine/lines)
        r = add_row(QLabel('Spine width:'), )
        self.spine_width_input = QLineEdit('1.5'); r.addWidget(self.spine_width_input)
        r = add_row(QLabel('Solid line width:'), )
        self.solid_width_input = QLineEdit('2'); r.addWidget(self.solid_width_input)
        r = add_row(QLabel('Stability line width:'), )
        self.dash_width_input = QLineEdit('2'); r.addWidget(self.dash_width_input)
        # Major ticks (direction + length + width)
        self.tick_dir_combo = QComboBox(); self.tick_dir_combo.addItems(['in','out','inout']); self.tick_dir_combo.setCurrentText('out')
        self.tick_length_input = QLineEdit('8')
        self.tick_width_input = QLineEdit('1')
        add_row(QLabel('Major tick direction:'), self.tick_dir_combo, QLabel('Length:'), self.tick_length_input, QLabel('Width:'), self.tick_width_input)
        # Minor ticks (show + length + width)
        self.show_minor_checkbox = QCheckBox(); self.show_minor_checkbox.setChecked(True)
        self.minor_length_input = QLineEdit('4')
        self.minor_width_input = QLineEdit('0.5')
        add_row(QLabel('Show minor ticks:'), self.show_minor_checkbox, QLabel('Length:'), self.minor_length_input, QLabel('Width:'), self.minor_width_input)
        # Labels toggle
        self.show_labels_checkbox = QCheckBox('Show ion labels')
        self.show_labels_checkbox.setChecked(True)
        layout.addWidget(self.show_labels_checkbox)
        # Ion label background fill
        ro = QHBoxLayout()
        self.label_fill_checkbox = QCheckBox('Fill ion label background')
        ro.addWidget(self.label_fill_checkbox)
        self.label_fill_checkbox.setChecked(False)
        ro.addWidget(QLabel('Fill color:'))
        self.label_fill_color_btn = QPushButton(self.label_fill_default)
        self.label_fill_color_btn.clicked.connect(self.choose_label_fill_color)
        ro.addWidget(self.label_fill_color_btn)
        ro.addWidget(QLabel('Alpha:'))
        self.label_fill_alpha_input = QLineEdit('0.6'); self.label_fill_alpha_input.setFixedWidth(50); ro.addWidget(self.label_fill_alpha_input)
        layout.addLayout(ro)
        # Region fill groups
        self.fill_species_inputs = []
        self.fill_checkboxes = []
        self.fill_color_btns = []
        self.fill_alpha_inputs = []
        for i in range(4):
            fr = QHBoxLayout(); fr.addWidget(QLabel(f'Fill species {i+1}:'))
            spec = QLineEdit(); spec.setPlaceholderText('Example: TiO2(s) or Ti[+2]'); fr.addWidget(spec)
            cb = QCheckBox('Fill'); cb.setChecked(i == 0); fr.addWidget(cb)
            fr.addWidget(QLabel('Color:'))
            color_btn = QPushButton(self.fill_color_default); color_btn.clicked.connect(lambda _, idx=i: self.choose_fill_color_idx(idx)); fr.addWidget(color_btn)
            fr.addWidget(QLabel('Alpha:'))
            alpha_in = QLineEdit('0.4'); alpha_in.setFixedWidth(50); fr.addWidget(alpha_in)
            layout.addLayout(fr)
            self.fill_species_inputs.append(spec)
            self.fill_checkboxes.append(cb)
            self.fill_color_btns.append(color_btn)
            self.fill_alpha_inputs.append(alpha_in)
        # Water lines colors
        fr = QHBoxLayout(); fr.addWidget(QLabel('Hydrogen Stability Line:'))
        self.h_color_btn = QPushButton(self.h_color); self.h_color_btn.clicked.connect(self.choose_h_color); fr.addWidget(self.h_color_btn); layout.addLayout(fr)
        fr = QHBoxLayout(); fr.addWidget(QLabel('Oxygen Stability Line:'))
        self.o_color_btn = QPushButton(self.o_color); self.o_color_btn.clicked.connect(self.choose_o_color); fr.addWidget(self.o_color_btn); layout.addLayout(fr)
        # Actions
        self.plot_btn = QPushButton('Generate Pourbaix Diagram'); self.plot_btn.clicked.connect(self.plot_pourbaix); layout.addWidget(self.plot_btn)
        self.export_btn = QPushButton('Export Data'); self.export_btn.clicked.connect(self.export_data); layout.addWidget(self.export_btn)
        self.export_fig_btn = QPushButton('Export Figure Image'); self.export_fig_btn.clicked.connect(self.export_figure); layout.addWidget(self.export_fig_btn)
        # Export options
        fr = QHBoxLayout(); fr.addWidget(QLabel('Export DPI:'))
        self.export_dpi_input = QLineEdit('300'); self.export_dpi_input.setFixedWidth(60); fr.addWidget(self.export_dpi_input)
        self.transparent_check = QCheckBox('Transparent BG'); fr.addWidget(self.transparent_check); layout.addLayout(fr)
        # Diagnostics / species list
        fr = QHBoxLayout(); self.diag_btn = QPushButton('Diagnostics'); self.diag_btn.clicked.connect(self.show_diagnostics); fr.addWidget(self.diag_btn)
        self.clear_cache_btn = QPushButton('Clear Cache'); self.clear_cache_btn.clicked.connect(self.clear_cache); fr.addWidget(self.clear_cache_btn); layout.addLayout(fr)
        fr2 = QHBoxLayout(); self.list_species_btn = QPushButton('Show Available Species Labels'); self.list_species_btn.clicked.connect(self.list_species_labels); fr2.addWidget(self.list_species_btn); layout.addLayout(fr2)
        self.setLayout(layout)

    # Unified error reporting with full traceback (helps diagnose packaged errors like 'NoneType' object has no attribute 'write')
    def _report_error(self, title: str, exc: Exception):
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        try:
            _LOG.error('Exception in %s: %s\n%s', title, exc, tb)
        except Exception:
            pass
        # Show shorter message plus hint for details in log
        msg = f"{exc}\n(See log file for full traceback)"
        try:
            QMessageBox.critical(self, title, msg)
        except Exception:
            pass

    # (Removed legacy duplicated _build_ui and duplicate helper methods.)

    def _parse_inputs_from_ui(self):
        return parse_inputs(
            self.elements_input.text(),
            self.ratios_input.text(),
            self.ph_input.text(),
            self.e_input.text(),
        )

    def _safe_get_entries(self, api_key:str, elements:List[str]):
        start = time.time(); self._last_sanitation_retry = False
        # In frozen GUI builds stdout/stderr may be None; disable tqdm progress bars
        # used internally by mp_api to avoid writing to a None file handle.
        try:
            os.environ.setdefault('TQDM_DISABLE', '1')
        except Exception:
            pass
        # Import MPRester here (deferred) so mp_api/tqdm don't initialize at module
        # import time when sys.stderr may still be None in frozen GUI apps.
        try:
            from mp_api.client import MPRester
        except Exception:
            MPRester = None
        key = tuple(sorted([e.capitalize() for e in elements]))
        cached = self._entries_cache.get(key)
        if cached and (time.time()-cached['ts'] <= self._cache_ttl):
            self._last_entries_count = len(cached['entries']); self._last_fetch_seconds = 0.0; return cached['entries']
        with MPRester(api_key) as mpr:
            result = fetch_pourbaix_entries(mpr, elements)
        entries = result.entries
        self._last_sanitation_retry = result.used_sanitation_retry
        self._entries_cache[key]={'entries':entries,'ts':time.time()}
        self._last_entries_count=len(entries)
        self._last_fetch_seconds=time.time()-start
        return entries

    def _clip_polygon(self, pH, E, pH_min, pH_max, E_min, E_max):
        poly = Polygon(zip(pH,E)); win = box(pH_min,E_min,pH_max,E_max); cl = poly.intersection(win)
        if cl.is_empty: return [], []
        if cl.geom_type=='Polygon': x,y=cl.exterior.coords.xy; return list(x), list(y)
        if cl.geom_type=='MultiPolygon': lg=max(list(cl.geoms), key=lambda p:p.area); x,y=lg.exterior.coords.xy; return list(x), list(y)
        return [], []

    def plot_pourbaix(self):
        self._invalidate_result()
        try:
            parsed = self._parse_inputs_from_ui()
            plt = _ensure_matplotlib()
            elements=list(parsed.elements)
            comp_dict=parsed.comp_dict
            api_key=self._resolve_api_key(); ph_range=list(parsed.ph_range); e_range=list(parsed.potential_range)
            if not api_key: QMessageBox.warning(self,'API Key Required','Enter your Materials Project API key.'); return
            entries=self._safe_get_entries(api_key,elements)
            pbx=PourbaixDiagram(entries, comp_dict=comp_dict); plotter=PourbaixPlotter(pbx); ax=plotter.get_pourbaix_plot(limits=[ph_range,e_range])
            # Update label cache & auto-complete
            self._last_labels = [str(se) for se in pbx.stable_entries]
            if self._last_labels:
                completer = QCompleter(self._last_labels)
                completer.setCaseSensitivity(False)
                for spec_in in self.fill_species_inputs:
                    spec_in.setCompleter(completer)
            for idx in range(4):
                if not self.fill_checkboxes[idx].isChecked(): continue
                target=self.fill_species_inputs[idx].text().strip();
                if not target: continue
                try: alpha=float(self.fill_alpha_inputs[idx].text().strip())
                except Exception: alpha=0.4
                color=self.fill_color_btns[idx].text()
                for entry in pbx.stable_entries:
                    label=str(entry)
                    if target==label or target in label:
                        verts=plotter.domain_vertices(entry)
                        # verts may be a numpy array; avoid ambiguous truth-value by explicit check
                        if verts is not None and len(verts) > 0:
                            pH,E = zip(*verts); pH=list(pH)+[pH[0]]; E=list(E)+[E[0]]
                            pH_c,E_c = self._clip_polygon(pH,E,ph_range[0],ph_range[1],e_range[0],e_range[1])
                            if pH_c: ax.fill(pH_c,E_c,color=color,alpha=alpha,zorder=0)
            fontsize=int(self.fontsize_input.text().strip() or 22); axis_font=self.axis_font_combo.currentText(); axis_fs=int(self.axis_fontsize_input.text().strip() or 24)
            spine_w=float(self.spine_width_input.text().strip() or 1.5); solid_w=float(self.solid_width_input.text().strip() or 2); dash_w=float(self.dash_width_input.text().strip() or 2)
            plt.rcParams['font.family']=axis_font
            for line in ax.lines:
                if line.get_linestyle()=='-': line.set_linewidth(solid_w)
                if line.get_linestyle()=='--' and line.get_color()=='r': line.set_linewidth(dash_w)
            for spine in ax.spines.values(): spine.set_linewidth(spine_w)
            # Remove dashed reference lines at E=0 and pH=7 if present (R1 parity)
            for line in ax.lines[:]:
                try:
                    xdata, ydata = line.get_xdata(), line.get_ydata()
                    if line.get_linestyle() in ('--','-.'):
                        if (all(abs(y) < 1e-9 for y in ydata)) or (all(abs(x-7) < 1e-9 for x in xdata)):
                            line.remove()
                except Exception:
                    pass
            # Identify remaining dashed red (water stability) lines and recolor to user defaults (first hydrogen, second oxygen)
            dashed_red = [ln for ln in ax.lines if ln.get_linestyle() in ('--','-.') and (ln.get_color() in ('r','#ff0000','#FF0000'))]
            if len(dashed_red) >= 2:
                dashed_red_sorted = sorted(dashed_red, key=lambda ln: sum(ln.get_ydata())/len(ln.get_ydata()) if len(ln.get_ydata()) else 0.0)
                # lower average potential = hydrogen stability line
                try:
                    dashed_red_sorted[0].set_color(self.h_color); dashed_red_sorted[0].set_linewidth(dash_w)
                    dashed_red_sorted[1].set_color(self.o_color); dashed_red_sorted[1].set_linewidth(dash_w)
                except Exception:
                    pass
            tick_len=float(self.tick_length_input.text().strip() or 8); tick_w=float(self.tick_width_input.text().strip() or 1)
            ax.tick_params(axis='both', labelsize=axis_fs, length=tick_len, width=tick_w, direction=self.tick_dir_combo.currentText())
            if self.show_minor_checkbox.isChecked(): ax.minorticks_on(); ax.tick_params(axis='both', which='minor', length=float(self.minor_length_input.text()), width=float(self.minor_width_input.text()))
            xlabel=self.xlabel_input.text().strip() or 'pH'; ylabel=self.ylabel_input.text().strip() or 'E (V vs. SHE)'
            ax.set_xlabel(xlabel, fontsize=int(self.xlabelsize_input.text().strip() or axis_fs+4), fontname=axis_font)
            ax.set_ylabel(ylabel, fontsize=int(self.ylabelsize_input.text().strip() or axis_fs+4), fontname=axis_font)
            def beautify(s): s=re.sub(r'([A-Za-z])(\d+)', r'\1$_{\2}$', s); s=re.sub(r'\[([+-]?\d+)\]', r'$^{\1}$', s); return s
            # Apply label beautify & optional background fill
            fill_enabled = self.label_fill_checkbox.isChecked()
            try:
                fill_alpha = float(self.label_fill_alpha_input.text().strip()) if self.label_fill_alpha_input.text().strip() else 0.6
            except Exception:
                fill_alpha = 0.6
            fill_color = self.label_fill_color_btn.text()
            for txt in ax.texts:
                txt.set_text(beautify(txt.get_text()))
                txt.set_fontsize(fontsize)
                txt.set_fontname(self.font_combo.currentText())
                txt.set_visible(self.show_labels_checkbox.isChecked())
                if fill_enabled and self.show_labels_checkbox.isChecked():
                    try:
                        txt.set_bbox(dict(facecolor=fill_color, alpha=fill_alpha, edgecolor='none', pad=0.4))
                    except Exception:
                        pass
                else:
                    try:
                        txt.set_bbox(None)
                    except Exception:
                        pass
            fig=ax.figure; fig.canvas.draw_idle(); fig.show()
            self._last_figure=fig; self._last_elements=elements; self._last_comp_dict=comp_dict
        except Exception as e:
            self._report_error('Error', e)

    def _invalidate_result(self):
        self._last_figure = None
        self._last_elements = []
        self._last_comp_dict = {}

    def list_species_labels(self):
        try:
            parsed = self._parse_inputs_from_ui()
            elements=list(parsed.elements)
            api_key=self._resolve_api_key()
            if not api_key:
                QMessageBox.warning(self,'API Key Required','Enter API key first.'); return
            entries=self._safe_get_entries(api_key, elements)
            pbx=PourbaixDiagram(entries)
            labels=[str(se) for se in pbx.stable_entries]
            if not labels:
                QMessageBox.information(self,'Result','No stable species labels found.'); return
            # Format labels columns (wrap every 4)
            cols=4
            lines=[]
            for i,lbl in enumerate(labels):
                lines.append(lbl)
            text='\n'.join(lines)
            QMessageBox.information(self,'Available Species Labels', f'{len(labels)} labels:\n\n{text}\n\nCopy into Fill species field, e.g.: TiO2(s), Ti[+2]')
            self._last_labels = labels
            # refresh completer
            completer = QCompleter(self._last_labels); completer.setCaseSensitivity(False)
            for spec_in in self.fill_species_inputs: spec_in.setCompleter(completer)
        except Exception as e:
            self._report_error('Error', e)

    def export_data(self):
        try:
            parsed = self._parse_inputs_from_ui()
            elements=list(parsed.elements); comp_dict=parsed.comp_dict; api_key=self._resolve_api_key()
            if not api_key: QMessageBox.warning(self,'API Key Required','Enter your Materials Project API key.'); return
            ph_range=list(parsed.ph_range); e_range=list(parsed.potential_range)
            entries=self._safe_get_entries(api_key,elements); pbx=PourbaixDiagram(entries, comp_dict=comp_dict); plotter=PourbaixPlotter(pbx)
            rows=[]
            for entry in pbx.stable_entries:
                verts=plotter.domain_vertices(entry)
                # Avoid ambiguous truth value for numpy arrays
                if verts is not None and len(verts) > 0:
                    pH,E=zip(*verts); pH=list(pH)+[pH[0]]; E=list(E)+[E[0]]; pH_c,E_c=self._clip_polygon(pH,E,ph_range[0],ph_range[1],e_range[0],e_range[1])
                    for x,y in zip(pH_c,E_c): rows.append({'Entry':str(entry),'pH':x,'E':y})
            if not rows: QMessageBox.warning(self,'No Data','No stable entries found.'); return
            df=pd.DataFrame(rows); suffix=''.join([f"{el}{ratio}" for el, ratio in comp_dict.items()]); default_name=f"pourbaix_boundaries_{suffix}"
            path, sel = QFileDialog.getSaveFileName(self, 'Export Data', default_name, 'CSV (*.csv);;Excel (*.xlsx);;Text (*.txt)')
            if not path:
                return
            # Normalize path and handle possible file: URLs
            try:
                path = os.path.expanduser(path)
                path = os.path.abspath(path)
                if path.startswith('file:'):
                    try:
                        from urllib.parse import urlparse, unquote
                        p = urlparse(path)
                        path = unquote(p.path)
                    except Exception:
                        pass
            except Exception:
                pass

            sel_l = (sel or '').lower()
            ext = os.path.splitext(path)[1].lower()
            try:
                # Ensure parent directory exists
                parent = os.path.dirname(path)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)

                if ext == '.xlsx' or 'excel' in sel_l:
                    df.to_excel(path, index=False)
                elif ext == '.txt' or 'text' in sel_l:
                    df.to_csv(path, sep='\t', index=False)
                else:
                    if ext == '' and not path.lower().endswith('.csv'):
                        path = path + '.csv'
                    df.to_csv(path, index=False)

                # Verify file was created and is non-empty
                if not os.path.exists(path) or os.path.getsize(path) == 0:
                    raise IOError(f'File not created or empty after write: {path}')
                _LOG.info('Data exported to %s (rows=%d)', path, len(df))
                QMessageBox.information(self, 'Done', f'Data exported: {path}')
            except Exception as exc:
                try:
                    _LOG.exception('Failed to export data to %s', path)
                except Exception:
                    pass
                self._report_error('Export Data Error', exc)
        except Exception as e:
            self._report_error('Export Data Error', e)

    def export_figure(self):
        try:
            if not self._last_figure: QMessageBox.warning(self,'No Figure','Generate a diagram first.'); return
            filters='PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;SVG (*.svg)'
            # Build default name with composition if available
            suffix = ''
            try:
                if self._last_elements and self._last_comp_dict:
                    suffix = ''.join([f"{el}{ratio}" for el, ratio in self._last_comp_dict.items()])
            except Exception:
                suffix = ''
            default_name = f"pourbaix_diagram_{suffix}.png" if suffix else 'pourbaix_diagram.png'
            path, sel = QFileDialog.getSaveFileName(self,'Export Figure', default_name, filters)
            if not path: return
            ext=os.path.splitext(path)[1].lower(); fmt='png'
            if ext in ['.jpg','.jpeg']: fmt='jpg'
            elif ext in ['.tif','.tiff']: fmt='tiff'
            elif ext=='.svg': fmt='svg'
            dpi=300
            try:
                d=int(self.export_dpi_input.text().strip());
                if 50<=d<=1200: dpi=d
            except Exception: pass
            transparent=self.transparent_check.isChecked()
            if fmt=='png' and ext=='': path+='.png'
            self._last_figure.savefig(path, format=fmt, dpi=dpi, bbox_inches='tight', transparent=transparent)
            QMessageBox.information(self,'Saved', f'Figure saved: {path}\nFormat={fmt.upper()} DPI={dpi} Transparent={transparent}')
        except Exception as e:
            self._report_error('Export Figure Error', e)

    def show_diagnostics(self):
        try:
            import matplotlib
            versions = runtime_versions()
            msg=(f'APP_VERSION: {APP_VERSION}\n'
                 f'matplotlib backend: {matplotlib.get_backend()}\n'
                 f'mp-api: {versions["mp-api"]}\n'
                 f'pymatgen: {versions["pymatgen"]}\n'
                 f'pymatgen-core: {versions["pymatgen-core"]}\n'
                 f'Last entries count: {self._last_entries_count}\n'
                 f'Last fetch seconds: {self._last_fetch_seconds:.2f}\n'
                 f'Used sanitation retry: {self._last_sanitation_retry}\n'
                 f'Cache items: {len(self._entries_cache)} (TTL {self._cache_ttl}s)')
            QMessageBox.information(self,'Diagnostics', msg)
        except Exception as e:
            self._report_error('Diagnostics Error', e)

    def clear_cache(self):
        self._entries_cache.clear(); QMessageBox.information(self,'Cache','Entries cache cleared.')

def run_self_test():
    import importlib

    critical_modules = (
        'pymatgen.core.entries',
        'pymatgen.analysis.pourbaix_diagram',
        'mp_api.client',
        'PyQt5.QtWidgets',
        'matplotlib',
        'shapely',
        'pandas',
        'openpyxl',
        'certifi',
    )
    for module_name in critical_modules:
        importlib.import_module(module_name)
    print(f'SELF-TEST PASS: Pourbaix GUI {APP_VERSION}; {len(critical_modules)} critical modules imported')
    return 0


def run_gui(smoke=False):
    from PyQt5.QtCore import QTimer

    try:
        QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    except Exception:
        pass
    app = QApplication(sys.argv)
    win = PourbaixApp()
    win.show()
    if smoke:
        QTimer.singleShot(250, app.quit)
    exit_code = app.exec_()
    if smoke:
        print('GUI-SMOKE PASS: window constructed, event loop processed, and application closed')
    return exit_code


if __name__=='__main__':
    # In frozen GUI builds (console=False) sys.stdout/stderr may be None which
    # causes libraries like tqdm to fail when they attempt to write to them.
    try:
        if getattr(sys, 'stdout', None) is None:
            sys.stdout = open(os.devnull, 'w')
        if getattr(sys, 'stderr', None) is None:
            sys.stderr = open(os.devnull, 'w')
    except Exception:
        pass
    if '--self-test' in sys.argv:
        sys.exit(run_self_test())
    sys.exit(run_gui(smoke='--gui-smoke' in sys.argv))
