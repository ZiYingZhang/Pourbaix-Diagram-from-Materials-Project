"""Composition-first input widget with H/O as open species."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QPushButton, QVBoxLayout, QWidget
from pymatgen.core import Element

from pourbaix_r4.domain import InputValidationError, parse_calculation_input, parse_formula


class CompositionPanel(QWidget):
    calculation_requested = Signal(object)
    input_changed = Signal()
    validation_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elements: tuple[str, ...] = ()
        self._ratio_inputs: dict[str, QLineEdit] = {}
        layout = QVBoxLayout(self)
        self.formula_input = QLineEdit()
        self.formula_input.setObjectName("formulaInput")
        apply_formula = QPushButton("Apply formula")
        apply_formula.clicked.connect(lambda: self.apply_formula(self.formula_input.text()))
        layout.addWidget(self.formula_input)
        layout.addWidget(apply_formula)
        self.open_species_notice = QLineEdit("H and O are an open reservoir; they do not take ratios.")
        self.open_species_notice.setReadOnly(True)
        layout.addWidget(self.open_species_notice)
        self.ratio_group = QGroupBox("Ratios")
        self.ratio_form = QFormLayout(self.ratio_group)
        layout.addWidget(self.ratio_group)
        self.ph_min, self.ph_max = QLineEdit("0"), QLineEdit("14")
        self.potential_min, self.potential_max = QLineEdit("-2"), QLineEdit("4")
        conditions = QFormLayout()
        conditions.addRow("pH min", self.ph_min); conditions.addRow("pH max", self.ph_max)
        conditions.addRow("Potential min", self.potential_min); conditions.addRow("Potential max", self.potential_max)
        layout.addLayout(conditions)
        generate = QPushButton("Generate diagram")
        generate.clicked.connect(self.request_calculation)
        layout.addWidget(generate)

    def available_element_symbols(self) -> tuple[str, ...]:
        return tuple(element.symbol for element in Element)

    def selected_elements(self) -> tuple[str, ...]:
        return self._elements

    def ratio_values(self) -> dict[str, str]:
        return {element: input_field.text() for element, input_field in self._ratio_inputs.items()}

    def _rebuild_ratio_rows(self, values: dict[str, str]) -> None:
        while self.ratio_form.rowCount():
            self.ratio_form.removeRow(0)
        self._ratio_inputs = {}
        for element in self._elements:
            if element in {"H", "O"}:
                continue
            field = QLineEdit(values.get(element, "1.0"))
            field.textChanged.connect(self.input_changed)
            self._ratio_inputs[element] = field
            self.ratio_form.addRow(element, field)

    def set_selected_elements(self, elements) -> None:
        previous = self.ratio_values()
        canonical = tuple(Element(str(element).strip().capitalize()).symbol for element in elements)
        self._elements = canonical
        self._rebuild_ratio_rows(previous)
        self.input_changed.emit()

    def set_ratio_value(self, element: str, value: str) -> None:
        self._ratio_inputs[element].setText(value)

    def apply_formula(self, formula: str) -> None:
        try:
            elements, ratios = parse_formula(formula)
        except InputValidationError as error:
            self.validation_failed.emit(str(error)); return
        self._elements = elements
        self._rebuild_ratio_rows({element: str(value) for element, value in ratios.items()})
        self.input_changed.emit()

    def request_calculation(self) -> None:
        try:
            parsed = parse_calculation_input(
                self._elements, self.ratio_values(), (self.ph_min.text(), self.ph_max.text()),
                (self.potential_min.text(), self.potential_max.text()),
            )
        except InputValidationError as error:
            self.validation_failed.emit(str(error)); return
        self.calculation_requested.emit(parsed)
