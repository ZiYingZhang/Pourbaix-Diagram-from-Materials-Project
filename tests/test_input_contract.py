import math

import pytest

from pourbaix_core import InputValidationError, parse_inputs


@pytest.mark.parametrize(
    ("elements", "ratios", "expected_elements", "expected_comp"),
    [
        ("Ti", "1.0", ("Ti",), {"Ti": 1.0}),
        ("Ti,O", "1.0", ("Ti", "O"), {"Ti": 1.0}),
        ("fe, Cr, O, H", "2,1", ("Fe", "Cr", "O", "H"), {"Fe": 2.0, "Cr": 1.0}),
    ],
)
def test_parse_inputs_keeps_api_elements_but_excludes_open_species_from_comp_dict(
    elements, ratios, expected_elements, expected_comp
):
    parsed = parse_inputs(elements, ratios, "0,14", "-2,4")

    assert parsed.elements == expected_elements
    assert parsed.comp_dict == expected_comp
    assert parsed.ph_range == (0.0, 14.0)
    assert parsed.potential_range == (-2.0, 4.0)
    assert all(math.isfinite(value) for value in parsed.comp_dict.values())


@pytest.mark.parametrize(
    ("elements", "ratios", "field"),
    [
        ("", "", "Elements"),
        ("Xx", "1", "Elements"),
        ("Ti,ti", "1,1", "Elements"),
        ("H,O", "", "Elements"),
        ("Ti,O", "1,2", "Ratios"),
        ("Ti", "", "Ratios"),
        ("Ti", "0", "Ratios"),
        ("Ti", "-1", "Ratios"),
        ("Ti", "nan", "Ratios"),
        ("Ti", "inf", "Ratios"),
    ],
)
def test_parse_inputs_rejects_invalid_elements_and_ratios(elements, ratios, field):
    with pytest.raises(InputValidationError, match=field):
        parse_inputs(elements, ratios, "0,14", "-2,4")


@pytest.mark.parametrize(
    ("ph_range", "potential_range", "field"),
    [
        ("0", "-2,4", "pH range"),
        ("0,14,15", "-2,4", "pH range"),
        ("14,0", "-2,4", "pH range"),
        ("0,0", "-2,4", "pH range"),
        ("0,nan", "-2,4", "pH range"),
        ("0,14", "4,-2", "Potential range"),
        ("0,14", "-2,inf", "Potential range"),
        ("0,14", "bad", "Potential range"),
    ],
)
def test_parse_inputs_rejects_malformed_or_unordered_ranges(ph_range, potential_range, field):
    with pytest.raises(InputValidationError, match=field):
        parse_inputs("Ti", "1", ph_range, potential_range)

