import pytest

from pourbaix_r4.figure_size import (
    FIGURE_SIZE_PRESETS_CM,
    convert_length,
    pixel_dimensions,
)


def test_length_units_round_trip_through_inches():
    assert convert_length(25.4, "mm", "inch") == pytest.approx(1.0)
    assert convert_length(2.54, "cm", "inch") == pytest.approx(1.0)
    assert convert_length(1.0, "inch", "cm") == pytest.approx(2.54)


def test_pixel_dimensions_use_physical_size_and_dpi():
    assert pixel_dimensions(4.0, 3.0, 300) == (1200, 900)


def test_origin_style_presets_include_journal_and_presentation_sizes():
    assert FIGURE_SIZE_PRESETS_CM["Journal single column"] == (8.5, 6.0)
    assert FIGURE_SIZE_PRESETS_CM["Journal double column"] == (18.0, 12.0)
    width, height = FIGURE_SIZE_PRESETS_CM["Presentation 16:9"]
    assert width / height == pytest.approx(16 / 9, rel=1e-3)
