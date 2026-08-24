"""Composition-first editor with explicit advanced scientific options."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from pymatgen.core import Element

from pourbaix_r4.domain import MAX_CLOSED_ELEMENTS, InputValidationError, parse_calculation_input, parse_formula, validate_selected_elements


_PERIODIC_TABLE_ROWS = (
    ("H", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "He"),
    ("Li", "Be", None, None, None, None, None, None, None, None, None, None, "B", "C", "N", "O", "F", "Ne"),
    ("Na", "Mg", None, None, None, None, None, None, None, None, None, None, "Al", "Si", "P", "S", "Cl", "Ar"),
    ("K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"),
    ("Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"),
    ("Cs", "Ba", None, "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"),
    ("Fr", "Ra", None, "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"),
)
_LANTHANIDES = ("La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu")
_ACTINIDES = ("Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr")


class PeriodicTableDialog(QDialog):
    """Searchable multi-select element picker."""

    elements_selected = Signal(object)

    def __init__(self, selected=(), parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose elements")
        self.resize(1040, 620)
        self._setting_selection = False
        self._selection_order: list[str] = []
        self.element_buttons: dict[str, QToolButton] = {}

        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by symbol or name, e.g. Fe / Iron")
        self.search_input.textChanged.connect(self._filter_elements)
        layout.addWidget(self.search_input)
        self.selection_limit_notice = QLabel("Select up to 4 closed elements. H and O are open reservoirs.")
        layout.addWidget(self.selection_limit_notice)
        self.selection_count = QLabel()
        self.selection_count.setObjectName("periodicSelectionCount")
        layout.addWidget(self.selection_count)
        self.selection_chips = QWidget()
        self.selection_chip_layout = QHBoxLayout(self.selection_chips)
        self.selection_chip_layout.setContentsMargins(0, 0, 0, 0)
        self.selection_chip_layout.addStretch(1)
        layout.addWidget(self.selection_chips)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        table = QWidget()
        self.periodic_grid = QGridLayout(table)
        self.periodic_grid.setSpacing(4)
        positions: dict[str, tuple[int, int]] = {}
        for row, symbols in enumerate(_PERIODIC_TABLE_ROWS):
            for column, symbol in enumerate(symbols):
                if symbol is not None:
                    positions[symbol] = (row, column)
        for offset, symbol in enumerate(_LANTHANIDES):
            positions[symbol] = (7, offset + 2)
        for offset, symbol in enumerate(_ACTINIDES):
            positions[symbol] = (8, offset + 2)
        self.periodic_grid.addWidget(QLabel("57–71"), 5, 2)
        self.periodic_grid.addWidget(QLabel("89–103"), 6, 2)
        self.periodic_grid.addWidget(QLabel("Lanthanides"), 7, 0, 1, 2)
        self.periodic_grid.addWidget(QLabel("Actinides"), 8, 0, 1, 2)
        for element in Element:
            button = QToolButton()
            button.setText(element.symbol)
            open_reservoir = element.symbol in {"H", "O"}
            reservoir_note = " · OPEN RESERVOIR" if open_reservoir else ""
            button.setToolTip(f"{element.long_name} · Z={element.Z}{reservoir_note}")
            button.setProperty("openReservoir", open_reservoir)
            button.setCheckable(True)
            button.setMinimumSize(45, 36)
            button.toggled.connect(
                lambda checked, symbol=element.symbol: self._selection_toggled(symbol, checked)
            )
            self.element_buttons[element.symbol] = button
            row, column = positions[element.symbol]
            self.periodic_grid.addWidget(button, row, column)
        scroll.setWidget(table)
        layout.addWidget(scroll)

        self.clear_selection_button = QPushButton("Clear")
        self.clear_selection_button.clicked.connect(lambda: self.set_selected_symbols(()))
        layout.addWidget(self.clear_selection_button)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Apply selection")
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setStyleSheet(
            """
            QToolButton[openReservoir="true"] { background-color: #D9EEF8; border: 2px solid #2D83A7; }
            QToolButton:checked { background-color: #8FD3E8; border: 2px solid #156B8A; font-weight: 700; }
            QToolButton[searchMatch="true"] { background-color: #FFF2B3; border: 2px solid #D79A00; }
            QToolButton[searchDimmed="true"] { color: #8A949F; background-color: #E5E8EC; }
            #periodicSelectionCount { font-weight: 700; color: #1F4F66; }
            """
        )
        self.set_selected_symbols(selected)

    def matching_symbols(self) -> tuple[str, ...]:
        query = self.search_input.text().strip().casefold()
        return tuple(
            element.symbol
            for element in Element
            if not query
            or query in element.symbol.casefold()
            or query in element.long_name.casefold()
        )

    def selected_symbols(self) -> tuple[str, ...]:
        return tuple(self._selection_order)

    def selected_chip_texts(self) -> tuple[str, ...]:
        return tuple(
            self.selection_chip_layout.itemAt(index).widget().text()
            for index in range(self.selection_chip_layout.count())
            if self.selection_chip_layout.itemAt(index).widget() is not None
        )

    def set_selected_symbols(self, symbols) -> None:
        normalized = tuple(dict.fromkeys(Element(str(symbol)).symbol for symbol in symbols))
        self._setting_selection = True
        try:
            for symbol, button in self.element_buttons.items():
                button.setChecked(symbol in normalized)
            self._selection_order = list(normalized)
        finally:
            self._setting_selection = False
        self._refresh_selection_display()

    def _filter_elements(self) -> None:
        matches = set(self.matching_symbols())
        has_query = bool(self.search_input.text().strip())
        for symbol, button in self.element_buttons.items():
            button.setProperty("searchMatch", has_query and symbol in matches)
            button.setProperty("searchDimmed", has_query and symbol not in matches)
            button.setEnabled(not has_query or symbol in matches)
            button.style().unpolish(button)
            button.style().polish(button)

    def _selection_toggled(self, symbol: str, checked: bool) -> None:
        if self._setting_selection:
            return
        closed_count = sum(item not in {"H", "O"} for item in self._selection_order)
        if checked and symbol not in {"H", "O"} and closed_count >= MAX_CLOSED_ELEMENTS:
            button = self.element_buttons[symbol]
            button.blockSignals(True)
            button.setChecked(False)
            button.blockSignals(False)
            self.selection_limit_notice.setText("Up to 4 non-H/O elements can be selected")
            return
        if checked and symbol not in self._selection_order:
            self._selection_order.append(symbol)
        elif not checked and symbol in self._selection_order:
            self._selection_order.remove(symbol)
        self.selection_limit_notice.setText("Select up to 4 closed elements. H and O are open reservoirs.")
        self._refresh_selection_display()

    def _refresh_selection_display(self) -> None:
        while self.selection_chip_layout.count() > 1:
            item = self.selection_chip_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for symbol in self._selection_order:
            chip = QToolButton()
            chip.setText(symbol)
            chip.setToolTip(f"Remove {symbol}")
            chip.clicked.connect(lambda _checked=False, item=symbol: self.element_buttons[item].setChecked(False))
            self.selection_chip_layout.insertWidget(self.selection_chip_layout.count() - 1, chip)
        closed_count = sum(symbol not in {"H", "O"} for symbol in self._selection_order)
        reservoirs = [symbol for symbol in self._selection_order if symbol in {"H", "O"}]
        reservoir_text = ", ".join(reservoirs) if reservoirs else "none"
        self.selection_count.setText(f"Closed elements: {closed_count}/4 · Open reservoirs: {reservoir_text}")

    def _accept_selection(self) -> None:
        self.elements_selected.emit(self.selected_symbols())
        self.accept()


class CompositionPanel(QWidget):
    calculation_requested = Signal(object)
    input_changed = Signal()
    validation_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elements = ()
        self._ratio_inputs = {}
        self._concentration_inputs = {}
        self._chip_labels = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("SYSTEM COMPOSITION"))

        formula_row = QHBoxLayout()
        self.formula_input = QLineEdit()
        self.formula_input.setObjectName("formulaInput")
        self.formula_input.setPlaceholderText("Formula: TiO2, Sb2Se3, FeNi")
        self.formula_input.editingFinished.connect(
            lambda: self.apply_formula(self.formula_input.text())
        )
        formula_row.addWidget(self.formula_input)
        self.choose_elements_button = QPushButton("Choose elements…")
        self.choose_elements_button.clicked.connect(self.open_periodic_table)
        formula_row.addWidget(self.choose_elements_button)
        layout.addLayout(formula_row)

        self.chip_row = QHBoxLayout()
        layout.addLayout(self.chip_row)
        self.composition_summary = QLabel("Enter a formula to define the system.")
        layout.addWidget(self.composition_summary)
        self.open_species_notice = QLabel(
            "H and O are an open reservoir; they do not take ratios or concentrations."
        )
        self.open_species_notice.setWordWrap(True)
        layout.addWidget(self.open_species_notice)

        self.ratio_group = QGroupBox("COMPOSITION CONTROL")
        self.ratio_form = QFormLayout(self.ratio_group)
        self._configure_form(self.ratio_form)
        layout.addWidget(self.ratio_group)

        self.advanced_options = QGroupBox("ADVANCED OPTIONS — OPTIONAL")
        advanced_box = QVBoxLayout(self.advanced_options)
        toggle_row = QHBoxLayout()
        self.advanced_options_toggle = QCheckBox("Enable advanced options")
        self.advanced_options_toggle.setObjectName("advancedOptionsToggle")
        self.advanced_options_toggle.setMinimumHeight(34)
        self.advanced_options_status = QLabel("OPTIONAL · OFF")
        self.advanced_options_status.setObjectName("advancedOptionsStatus")
        toggle_row.addWidget(self.advanced_options_toggle, 1)
        toggle_row.addWidget(self.advanced_options_status)
        advanced_box.addLayout(toggle_row)
        help_text = QLabel("Enable to edit solid filtering, ion concentrations, diagram range, and future heatmap options.")
        help_text.setWordWrap(True)
        advanced_box.addWidget(help_text)
        self.advanced_options_content = QWidget()
        self.advanced_options_content.setEnabled(False)
        advanced = QVBoxLayout(self.advanced_options_content)
        advanced.setContentsMargins(0, 0, 0, 0)
        self.filter_solids = QCheckBox("Filter solids")
        self.filter_solids.setChecked(True)
        self.filter_solids.toggled.connect(self.input_changed)
        advanced.addWidget(self.filter_solids)

        concentration_group = QGroupBox("ION CONCENTRATIONS (M)")
        self.concentration_form = QFormLayout(concentration_group)
        self._configure_form(self.concentration_form)
        advanced.addWidget(concentration_group)

        range_group = QGroupBox("DIAGRAM RANGE")
        ranges = QFormLayout(range_group)
        self._configure_form(ranges)
        self.ph_min, self.ph_max = QLineEdit("-2"), QLineEdit("16")
        self.potential_min, self.potential_max = QLineEdit("-4"), QLineEdit("4")
        for label, field in (
            ("pH min", self.ph_min),
            ("pH max", self.ph_max),
            ("Potential min", self.potential_min),
            ("Potential max", self.potential_max),
        ):
            field.textChanged.connect(self.input_changed)
            ranges.addRow(label, field)
        advanced.addWidget(range_group)

        self.heatmap_toggle = QCheckBox("Show heatmap — Coming later")
        self.heatmap_toggle.setEnabled(False)
        self.heatmap_entry = QComboBox()
        self.heatmap_entry.addItem("Heatmap entry — Coming later")
        self.heatmap_entry.setEnabled(False)
        advanced.addWidget(self.heatmap_toggle)
        advanced.addWidget(self.heatmap_entry)
        advanced_box.addWidget(self.advanced_options_content)
        self.advanced_options_toggle.toggled.connect(self._set_advanced_options_enabled)
        layout.addWidget(self.advanced_options)

        generate = QPushButton("Generate diagram")
        generate.clicked.connect(self.request_calculation)
        layout.addWidget(generate)

    @staticmethod
    def _configure_form(form: QFormLayout) -> None:
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(10)

    def available_element_symbols(self):
        return tuple(element.symbol for element in Element)

    def selected_elements(self):
        return self._elements

    def element_chip_texts(self):
        return tuple(label.text() for label in self._chip_labels)

    def ratio_values(self):
        return {element: field.text() for element, field in self._ratio_inputs.items()}

    def concentration_values(self):
        return {
            element: field.text() for element, field in self._concentration_inputs.items()
        }

    def _clear(self, form):
        while form.rowCount():
            form.removeRow(0)

    def _set_advanced_options_enabled(self, enabled: bool) -> None:
        self.advanced_options_content.setEnabled(enabled)
        self.advanced_options_status.setText("OPTIONAL · ON" if enabled else "OPTIONAL · OFF")

    def _rebuild(self, ratios, concentrations):
        self._clear(self.ratio_form)
        self._clear(self.concentration_form)
        while self.chip_row.count():
            widget = self.chip_row.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self._ratio_inputs = {}
        self._concentration_inputs = {}
        self._chip_labels = []
        for element in self._elements:
            chip = QToolButton()
            chip.setText(element)
            chip.setToolTip(f"Remove {element}")
            chip.clicked.connect(lambda _checked=False, symbol=element: self.remove_element(symbol))
            self._chip_labels.append(chip)
            self.chip_row.addWidget(chip)
            if element in {"H", "O"}:
                continue
            ratio = QLineEdit(ratios.get(element, "1.0"))
            concentration = QLineEdit(concentrations.get(element, "0.000001"))
            ratio.textChanged.connect(self._changed)
            concentration.textChanged.connect(self.input_changed)
            self._ratio_inputs[element] = ratio
            self._concentration_inputs[element] = concentration
            self.ratio_form.addRow(element, ratio)
            self.concentration_form.addRow(element, concentration)
        self._update_summary()

    def _changed(self):
        self._update_summary()
        self.input_changed.emit()

    def _update_summary(self):
        if not self._ratio_inputs:
            self.composition_summary.setText("Enter a formula to define the system.")
            return
        elements = " : ".join(self._ratio_inputs)
        values = " : ".join(self._display_ratio(field.text()) for field in self._ratio_inputs.values())
        self.composition_summary.setText(f"{elements} = {values}")

    @staticmethod
    def _display_ratio(value):
        try:
            return f"{float(value):g}"
        except (TypeError, ValueError):
            return "?"

    def open_periodic_table(self):
        dialog = PeriodicTableDialog(self._elements, self)
        dialog.elements_selected.connect(self.apply_element_selection)
        dialog.exec()

    def apply_element_selection(self, elements):
        self.set_selected_elements(elements)
        self.formula_input.setText("".join(self._elements))

    def set_selected_elements(self, elements):
        ratios, concentrations = self.ratio_values(), self.concentration_values()
        try:
            canonical = tuple(dict.fromkeys(Element(str(element).strip().capitalize()).symbol for element in elements))
            validated = validate_selected_elements(canonical)
        except (InputValidationError, TypeError, ValueError) as error:
            self.validation_failed.emit(str(error))
            return
        self._elements = validated
        self._rebuild(ratios, concentrations)
        self.input_changed.emit()

    def remove_element(self, element):
        self.apply_element_selection(item for item in self._elements if item != element)

    def set_ratio_value(self, element, value):
        self._ratio_inputs[element].setText(value)

    def apply_formula(self, formula):
        try:
            elements, ratios = parse_formula(formula)
        except InputValidationError as error:
            self.validation_failed.emit(str(error))
            return
        self._elements = elements
        self._rebuild({element: str(value) for element, value in ratios.items()}, {})
        self.input_changed.emit()

    def request_calculation(self):
        try:
            parsed = parse_calculation_input(
                self._elements,
                self.ratio_values(),
                (self.ph_min.text(), self.ph_max.text()),
                (self.potential_min.text(), self.potential_max.text()),
                ion_concentrations=self.concentration_values(),
                filter_solids=self.filter_solids.isChecked(),
            )
        except InputValidationError as error:
            self.validation_failed.emit(str(error))
            return
        self.calculation_requested.emit(parsed)
