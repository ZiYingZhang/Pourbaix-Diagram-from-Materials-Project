from pourbaix_gui_R3 import runtime_versions


def test_runtime_versions_supports_split_pymatgen_distributions():
    versions = runtime_versions()

    assert versions["mp-api"] == "0.46.4"
    assert versions["pymatgen"]
    assert versions["pymatgen-core"]

