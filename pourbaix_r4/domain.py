"""Pure parsing and validation for R4 chemical-system inputs."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

from pymatgen.core import Composition, Element

from pourbaix_r4.models import CalculationInput


_OPEN_SPECIES = frozenset({"H", "O"})
_FORMULA_PATTERN = re.compile(r"(?:[A-Z][a-z]?(?:\d+(?:\.\d+)?)?)+")


class InputValidationError(ValueError):
    """Raised when a user-visible R4 calculation field is invalid."""


def _canonical_symbol(raw_symbol: object, field: str) -> str:
    if not isinstance(raw_symbol, str) or not raw_symbol.strip():
        raise InputValidationError(f"{field} contains an empty element symbol")
    symbol = raw_symbol.strip().capitalize()
    try:
        return Element(symbol).symbol
    except (TypeError, ValueError) as error:
        raise InputValidationError(f"{field} contains invalid element symbol '{raw_symbol}'") from error


def _validate_elements(selected_elements: Sequence[str]) -> tuple[str, ...]:
    if isinstance(selected_elements, str):
        raise InputValidationError("Elements must be a sequence of element symbols")
    elements = tuple(_canonical_symbol(symbol, "Elements") for symbol in selected_elements)
    if not elements:
        raise InputValidationError("Elements must include at least one non-H/O element")
    if len(set(elements)) != len(elements):
        raise InputValidationError("Elements must not contain duplicates")
    if not any(symbol not in _OPEN_SPECIES for symbol in elements):
        raise InputValidationError("Elements must include at least one non-H/O element")
    return elements


def _parse_positive_ratio(value: object) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise InputValidationError("Ratios must be finite positive numbers") from error
    if not math.isfinite(parsed) or parsed <= 0:
        raise InputValidationError("Ratios must be finite positive numbers")
    return parsed


def _parse_concentration(element: str, value: object) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise InputValidationError(f"Ion concentration for {element} must be a number in M") from error
    if not math.isfinite(parsed) or not 1e-6 <= parsed <= 5.0:
        raise InputValidationError(f"Ion concentration for {element} must be between 1e-6 and 5 M")
    return parsed


def _parse_range(raw_range: Sequence[object], field: str) -> tuple[float, float]:
    if isinstance(raw_range, str) or len(raw_range) != 2:
        raise InputValidationError(f"{field} must contain a lower and upper value")
    try:
        lower, upper = (float(str(value).strip()) for value in raw_range)
    except (TypeError, ValueError) as error:
        raise InputValidationError(f"{field} must contain finite numeric values") from error
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise InputValidationError(f"{field} lower bound must be less than its upper bound")
    return lower, upper


def parse_formula(formula: str) -> tuple[tuple[str, ...], dict[str, float]]:
    """Parse a simple formula into selected elements and editable closed ratios."""
    normalized = formula.strip() if isinstance(formula, str) else ""
    if not normalized or not _FORMULA_PATTERN.fullmatch(normalized):
        raise InputValidationError("Formula must be a non-empty simple chemical formula")
    try:
        composition = Composition(normalized)
    except (TypeError, ValueError) as error:
        raise InputValidationError("Formula contains invalid elements or amounts") from error

    symbols_in_order: list[str] = []
    for raw_symbol in re.findall(r"[A-Z][a-z]?", normalized):
        symbol = _canonical_symbol(raw_symbol, "Formula")
        if symbol not in symbols_in_order:
            symbols_in_order.append(symbol)
    try:
        elements = _validate_elements(symbols_in_order)
    except InputValidationError as error:
        raise InputValidationError(f"Formula is invalid: {error}") from error
    amounts = composition.get_el_amt_dict()
    ratios = {
        element: float(amounts[element])
        for element in elements
        if element not in _OPEN_SPECIES
    }
    return elements, ratios


def parse_calculation_input(
    selected_elements: Sequence[str],
    ratios: Mapping[str, str | float],
    ph_range: tuple[str | float, str | float],
    potential_range: tuple[str | float, str | float],
    ion_concentrations: Mapping[str, str | float] | None = None,
    filter_solids: bool = True,
) -> CalculationInput:
    """Validate UI state before credential resolution or a network request."""
    elements = _validate_elements(selected_elements)
    closed_elements = tuple(element for element in elements if element not in _OPEN_SPECIES)
    canonical_ratios: dict[str, object] = {}
    for raw_symbol, value in ratios.items():
        symbol = _canonical_symbol(raw_symbol, "Ratios")
        if symbol in canonical_ratios:
            raise InputValidationError("Ratios must not contain duplicate elements")
        canonical_ratios[symbol] = value
    if any(symbol in _OPEN_SPECIES for symbol in canonical_ratios):
        raise InputValidationError("Ratios must not include open H/O species")
    if set(canonical_ratios) != set(closed_elements):
        raise InputValidationError("Ratios must provide one value for each non-H/O element")

    parsed_ratios = tuple((element, _parse_positive_ratio(canonical_ratios[element])) for element in closed_elements)
    raw_concentrations = ({element: 1e-6 for element in closed_elements} if ion_concentrations is None else ion_concentrations)
    canonical_concentrations: dict[str, object] = {}
    for raw_symbol, value in raw_concentrations.items():
        symbol = _canonical_symbol(raw_symbol, "Ion concentration")
        canonical_concentrations[symbol] = value
    if set(canonical_concentrations) != set(closed_elements):
        raise InputValidationError("Ion concentration must provide one value for each non-H/O element")
    parsed_concentrations = tuple(
        (element, _parse_concentration(element, canonical_concentrations[element])) for element in closed_elements
    )
    return CalculationInput(
        elements=elements,
        closed_element_ratios=parsed_ratios,
        ph_range=_parse_range(ph_range, "pH range"),
        potential_range=_parse_range(potential_range, "Potential range"),
        ion_concentrations=parsed_concentrations,
        filter_solids=bool(filter_solids),
    )


def import_legacy_element_ratio_text(elements_text: str, ratios_text: str) -> tuple[tuple[str, ...], dict[str, float]]:
    """Accept R2/R3 comma text and conventional colon-delimited ratios."""
    raw_elements = tuple(part.strip() for part in elements_text.split(",")) if isinstance(elements_text, str) else ()
    elements = _validate_elements(raw_elements)
    closed_elements = tuple(element for element in elements if element not in _OPEN_SPECIES)
    ratio_separator = ":" if isinstance(ratios_text, str) and "," not in ratios_text else ","
    raw_ratios = tuple(part.strip() for part in ratios_text.split(ratio_separator)) if isinstance(ratios_text, str) else ()
    if len(raw_ratios) != len(closed_elements):
        raise InputValidationError("Ratios must provide one value for each non-H/O element")
    parsed_ratios = {element: _parse_positive_ratio(value) for element, value in zip(closed_elements, raw_ratios)}
    return elements, parsed_ratios
