"""Composition-first editor with explicit advanced scientific options."""
from __future__ import annotations

from PySide6.QtCore import Signal
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

from pourbaix_r4.domain import InputValidationError, parse_calculation_input, parse_formula


class PeriodicTableDialog(QDialog):
    """Searchable multi-select element picker."""

    elements_selected = Signal(object)

    def __init__(self, selected=(), parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose elements")
        self.resize(760, 520)
        self._setting_selection = False
        self._selection_order: list[str] = []
        self.element_buttons: dict[str, QToolButton] = {}

        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by symbol or name, e.g. Fe / Iron")
        self.search_input.textChanged.connect(self._filter_elements)
        layout.addWidget(self.search_input)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        table = QWidget()
        grid = QGridLayout(table)
        grid.setSpacing(5)
        for index, element in enumerate(Element):
            button = QToolButton()
            button.setText(element.symbol)
            button.setToolTip(f"{element.long_name} · Z={element.Z}")
            button.setCheckable(True)
            button.setMinimumSize(54, 38)
            button.toggled.connect(
                lambda checked, symbol=element.symbol: self._selection_toggled(symbol, checked)
            )
            self.element_buttons[element.symbol] = button
            grid.addWidget(button, index // 10, index % 10)
        scroll.setWidget(table)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
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

    def set_selected_symbols(self, symbols) -> None:
        normalized = tuple(dict.fromkeys(Element(str(symbol)).symbol for symbol in symbols))
        self._setting_selection = True
        try:
            for symbol, button in self.element_buttons.items():
                button.setChecked(symbol in normalized)
            self._selection_order = list(normalized)
        finally:
            self._setting_selection = False

    def _filter_elements(self) -> None:
        matches = set(self.matching_symbols())
        for symbol, button in self.element_buttons.items():
            button.setVisible(symbol in matches)

    def _selection_toggled(self, symbol: str, checked: bool) -> None:
        if self._setting_selection:
            return
        if checked and symbol not in self._selection_order:
            self._selection_order.append(symbol)
        elif not checked and symbol in self._selection_order:
            self._selection_order.remove(symbol)

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
        layout.addWidget(QLabel("System composition"))

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

        self.ratio_group = QGroupBox("Composition control")
        self.ratio_form = QFormLayout(self.ratio_group)
        layout.addWidget(self.ratio_group)

        self.advanced_options = QGroupBox("Advanced options")
        self.advanced_options.setCheckable(True)
        self.advanced_options.setChecked(False)
        advanced = QVBoxLayout(self.advanced_options)
        self.filter_solids = QCheckBox("Filter solids")
        self.filter_solids.setChecked(True)
        self.filter_solids.toggled.connect(self.input_changed)
        advanced.addWidget(self.filter_solids)

        concentration_group = QGroupBox("Ion concentrations (M)")
        self.concentration_form = QFormLayout(concentration_group)
        advanced.addWidget(concentration_group)

        range_group = QGroupBox("Diagram range")
        ranges = QFormLayout(range_group)
        self.ph_min, self.ph_max = QLineEdit("0"), QLineEdit("14")
        self.potential_min, self.potential_max = QLineEdit("-2"), QLineEdit("4")
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
        layout.addWidget(self.advanced_options)

        generate = QPushButton("Generate diagram")
        generate.clicked.connect(self.request_calculation)
        layout.addWidget(generate)

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
        self._elements = tuple(
            dict.fromkeys(Element(str(element).strip().capitalize()).symbol for element in elements)
        )
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
