"""Pure scientific input validation for Pourbaix GUI R3."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MethodType
from typing import Any
import warnings as _warnings

from pymatgen.core import Element


OPEN_SPECIES = frozenset({"H", "O"})


class InputValidationError(ValueError):
    """A user-correctable error in a named Pourbaix input field."""


@dataclass(frozen=True)
class PourbaixInputs:
    elements: tuple[str, ...]
    comp_dict: dict[str, float]
    ph_range: tuple[float, float]
    potential_range: tuple[float, float]


@dataclass(frozen=True)
class FetchResult:
    entries: list[Any]
    used_sanitation_retry: bool


def _sanitize_ion_record(record: Any) -> Any:
    if not isinstance(record, dict):
        return record
    cleaned = dict(record)
    data = record.get("data") or {}
    if not isinstance(data, dict):
        data = {}
    cleaned_data = {
        key: value
        for key, value in data.items()
        if value not in (None, [], {}, "") or key in {"MajElements", "RefSolid"}
    }
    cleaned["data"] = cleaned_data
    return cleaned


def _is_missing_ion_field_error(exc: BaseException) -> bool:
    return isinstance(exc, KeyError) and bool(exc.args) and exc.args[0] in {
        "data",
        "MajElements",
        "RefSolid",
    }


_CAPTURED_WARNINGS: list[str] = []
_ORIGINAL_SHOWWARNING = _warnings.showwarning


def _record_warning(
    message: Any,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: Any = None,
    line: str | None = None,
) -> None:
    formatted = _warnings.formatwarning(message, category, filename, lineno, line)
    _CAPTURED_WARNINGS.append(formatted.strip())
    try:
        import logging

        logging.getLogger("pourbaix_core.warnings").warning("%s", formatted.strip())
    except Exception:
        pass
    _ORIGINAL_SHOWWARNING(message, category, filename, lineno, file, line)


def install_warning_capture() -> None:
    """Route warnings through the local log so swallowed client errors stay visible."""

    _warnings.showwarning = _record_warning


def last_captured_warning() -> str | None:
    return _CAPTURED_WARNINGS[-1] if _CAPTURED_WARNINGS else None


def fetch_pourbaix_entries(mpr: Any, elements: list[str]) -> FetchResult:
    """Fetch entries, retrying once only for empty or malformed ion data."""

    contribs = getattr(mpr, "contribs", None)
    if contribs is None:
        reason = last_captured_warning() or (
            "MPContribs initialization returned None without a captured warning."
        )
        raise RuntimeError(
            "Materials Project ion reference service (MPContribs) could not be initialized. "
            "Check network access to contribs-api.materialsproject.org and the API key. "
            f"Details: {reason}"
        )

    try:
        entries = mpr.get_pourbaix_entries(elements)
    except Exception as exc:
        if not _is_missing_ion_field_error(exc):
            raise
    else:
        if entries:
            return FetchResult(entries=list(entries), used_sanitation_retry=False)

    sanitized = []
    for record in mpr.get_ion_reference_data() or []:
        cleaned = _sanitize_ion_record(record)
        data = cleaned.get("data", {}) if isinstance(cleaned, dict) else {}
        if data.get("MajElements") and data.get("RefSolid"):
            sanitized.append(cleaned)

    def sanitized_for_chemsys(_this: Any, chemsys: str | list[str]) -> list[dict]:
        requested = chemsys.split("-") if isinstance(chemsys, str) else chemsys
        requested_symbols = {symbol.capitalize() for symbol in requested}
        return [
            record
            for record in sanitized
            if record["data"]["MajElements"].capitalize() in requested_symbols
        ]

    original_selector = mpr.get_ion_reference_data_for_chemsys
    mpr.get_ion_reference_data_for_chemsys = MethodType(sanitized_for_chemsys, mpr)
    try:
        retry_entries = mpr.get_pourbaix_entries(elements)
    finally:
        mpr.get_ion_reference_data_for_chemsys = original_selector

    if not retry_entries:
        raise RuntimeError("No pourbaix entries after sanitation retry.")
    return FetchResult(entries=list(retry_entries), used_sanitation_retry=True)


def _parse_elements(text: str) -> tuple[str, ...]:
    parts = [part.strip() for part in text.split(",")]
    if not parts or any(not part for part in parts):
        raise InputValidationError("Elements: enter one or more comma-separated element symbols.")

    elements = tuple(part.capitalize() for part in parts)
    invalid = [symbol for symbol in elements if not Element.is_valid_symbol(symbol)]
    if invalid:
        raise InputValidationError(f"Elements: invalid element symbol(s): {', '.join(invalid)}.")
    if len(set(elements)) != len(elements):
        raise InputValidationError("Elements: duplicate element symbols are not allowed.")
    if not any(symbol not in OPEN_SPECIES for symbol in elements):
        raise InputValidationError("Elements: include at least one element other than H or O.")
    return elements


def _parse_ratios(text: str, closed_elements: tuple[str, ...]) -> dict[str, float]:
    parts = [part.strip() for part in text.split(",")] if text.strip() else []
    if len(parts) != len(closed_elements) or any(not part for part in parts):
        raise InputValidationError(
            "Ratios: enter exactly one positive ratio per non-H/O element "
            f"({', '.join(closed_elements)}); H and O are open species and take no ratio."
        )
    try:
        values = tuple(float(part) for part in parts)
    except ValueError as exc:
        raise InputValidationError("Ratios: every ratio must be a number.") from exc
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise InputValidationError("Ratios: every ratio must be finite and greater than zero.")
    return dict(zip(closed_elements, values, strict=True))


def _parse_range(text: str, field_name: str) -> tuple[float, float]:
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 2 or any(not part for part in parts):
        raise InputValidationError(f"{field_name}: enter exactly two comma-separated values.")
    try:
        lower, upper = (float(part) for part in parts)
    except ValueError as exc:
        raise InputValidationError(f"{field_name}: both limits must be numbers.") from exc
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise InputValidationError(f"{field_name}: both limits must be finite.")
    if lower >= upper:
        raise InputValidationError(f"{field_name}: lower limit must be less than upper limit.")
    return lower, upper


def parse_inputs(
    elements_text: str,
    ratios_text: str,
    ph_text: str,
    potential_text: str,
) -> PourbaixInputs:
    """Parse and validate all scientific inputs before any network operation."""

    elements = _parse_elements(elements_text)
    closed_elements = tuple(symbol for symbol in elements if symbol not in OPEN_SPECIES)
    return PourbaixInputs(
        elements=elements,
        comp_dict=_parse_ratios(ratios_text, closed_elements),
        ph_range=_parse_range(ph_text, "pH range"),
        potential_range=_parse_range(potential_text, "Potential range"),
    )


install_warning_capture()
