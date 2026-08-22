import math

import pytest

from pourbaix_r4.domain import (
    InputValidationError,
    import_legacy_element_ratio_text,
    parse_calculation_input,
    parse_formula,
)


@pytest.mark.parametrize(
    ("formula", "expected_elements", "expected_ratios"),
    [
        ("Sb2Se3", ("Sb", "Se"), {"Sb": 2.0, "Se": 3.0}),
        ("BiVO4", ("Bi", "V", "O"), {"Bi": 1.0, "V": 1.0}),
        ("FeNi", ("Fe", "Ni"), {"Fe": 1.0, "Ni": 1.0}),
        ("TiO2", ("Ti", "O"), {"Ti": 1.0}),
    ],
)
def test_parse_formula_populates_only_closed_element_ratios(formula, expected_elements, expected_ratios):
    elements, ratios = parse_formula(formula)

    assert elements == expected_elements
    assert ratios == expected_ratios


@pytest.mark.parametrize("formula", ["", "Qq2", "H2O", "Sb(Se)"])
def test_parse_formula_rejects_empty_invalid_or_open_only_formulas(formula):
    with pytest.raises(InputValidationError, match="Formula"):
        parse_formula(formula)


def test_parse_calculation_input_keeps_hydrogen_and_oxygen_open():
    parsed = parse_calculation_input(
        selected_elements=("Sb", "Se", "O", "H"),
        ratios={"Sb": "2", "Se": "3"},
        ph_range=("0", "14"),
        potential_range=("-2", "4"),
    )

    assert parsed.elements == ("Sb", "Se", "O", "H")
    assert parsed.comp_dict == {"Sb": 2.0, "Se": 3.0}
    assert all(math.isfinite(value) for value in parsed.comp_dict.values())


def test_parse_calculation_input_accepts_aqueous_alloys_without_selected_oxygen():
    parsed = parse_calculation_input(
        selected_elements=("Fe", "Ni"),
        ratios={"Fe": "1", "Ni": "1"},
        ph_range=(0, 14),
        potential_range=(-2, 4),
    )

    assert parsed.comp_dict == {"Fe": 1.0, "Ni": 1.0}


@pytest.mark.parametrize(
    ("elements", "ratios", "ph_range", "potential_range", "field"),
    [
        (("Sb", "Sb"), {"Sb": "1"}, (0, 14), (-2, 4), "Elements"),
        (("H", "O"), {}, (0, 14), (-2, 4), "Elements"),
        (("Sb", "Se"), {"Sb": "2"}, (0, 14), (-2, 4), "Ratios"),
        (("Sb",), {"Sb": "0"}, (0, 14), (-2, 4), "Ratios"),
        (("Sb",), {"Sb": "nan"}, (0, 14), (-2, 4), "Ratios"),
        (("Sb", "O"), {"Sb": "1", "O": "2"}, (0, 14), (-2, 4), "Ratios"),
        (("Sb",), {"Sb": "1"}, (14, 0), (-2, 4), "pH range"),
        (("Sb",), {"Sb": "1"}, (0, 14), (4, -2), "Potential range"),
    ],
)
def test_parse_calculation_input_rejects_invalid_systems_and_ranges(
    elements, ratios, ph_range, potential_range, field
):
    with pytest.raises(InputValidationError, match=field):
        parse_calculation_input(elements, ratios, ph_range, potential_range)


@pytest.mark.parametrize("ratios_text", ["2, 3", "2:3", "0.4:0.6"])
def test_import_legacy_text_excludes_open_species_from_ratio_mapping(ratios_text):
    elements, ratios = import_legacy_element_ratio_text("Sb, Se, O, H", ratios_text)

    assert elements == ("Sb", "Se", "O", "H")
    expected_ratios = {"Sb": 0.4, "Se": 0.6} if ratios_text == "0.4:0.6" else {"Sb": 2.0, "Se": 3.0}
    assert ratios == expected_ratios
