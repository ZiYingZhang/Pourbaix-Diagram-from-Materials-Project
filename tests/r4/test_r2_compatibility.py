from pourbaix_r4.models import AppearanceSettings


def test_r4_appearance_model_retains_all_r2_display_control_categories():
    appearance = AppearanceSettings()

    for field in (
        "show_ion_labels", "ion_label_font", "ion_label_font_size", "fill_ion_label_background",
        "ion_label_background_color", "ion_label_background_alpha", "axis_tick_font", "axis_tick_font_size",
        "x_axis_label", "x_axis_label_size", "y_axis_label", "y_axis_label_size", "spine_width",
        "solid_line_width", "stability_line_width", "major_tick_direction", "major_tick_length",
        "major_tick_width", "show_minor_ticks", "minor_tick_length", "minor_tick_width",
        "hydrogen_line_color", "oxygen_line_color",
    ):
        assert hasattr(appearance, field)
