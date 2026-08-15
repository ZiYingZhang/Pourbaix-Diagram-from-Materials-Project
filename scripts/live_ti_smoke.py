"""Optional live Materials Project Ti workflow for release acceptance."""

import os

from mp_api.client import MPRester
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram

from pourbaix_core import fetch_pourbaix_entries, parse_inputs


def main():
    api_key = next(
        (
            os.environ.get(name, "").strip()
            for name in ("MP_API_KEY", "MAPI_KEY", "PMG_MAPI_KEY")
            if os.environ.get(name, "").strip()
        ),
        "",
    )
    if not api_key:
        raise SystemExit("No Materials Project API key is available.")

    parsed = parse_inputs("Ti", "1.0", "0,14", "-2,4")
    with MPRester(api_key) as mpr:
        result = fetch_pourbaix_entries(mpr, list(parsed.elements))
    diagram = PourbaixDiagram(result.entries, comp_dict=parsed.comp_dict)
    if not diagram.stable_entries:
        raise RuntimeError("The live Ti workflow returned no stable Pourbaix entries.")
    print(f"LIVE-TI PASS: entries={len(result.entries)} stable={len(diagram.stable_entries)}")


if __name__ == "__main__":
    main()

