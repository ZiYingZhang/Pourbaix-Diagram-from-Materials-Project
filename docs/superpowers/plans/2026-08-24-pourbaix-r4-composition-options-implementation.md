# Pourbaix Studio R4 Composition and Advanced Options Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the confusing formula/apply flow with an immediate composition editor and add scientifically supported ion concentration and solid-filter controls.

**Architecture:** Extend immutable `CalculationInput` first, then forward its new values through `calculate_snapshot`, then rebuild `CompositionPanel` around one committed formula editor and collapsible advanced options. Heatmap remains a disabled UI placeholder and never enters scientific state.

**Tech Stack:** CPython 3.13, PySide6/Qt6, pymatgen, pytest.

**Spec:** [Composition and advanced options design](../specs/2026-08-24-pourbaix-r4-composition-options-design.md)

## Global Constraints

- H and O remain open species and never receive ratios or concentrations.
- Ion concentration is finite and within `1e-6–5 M` inclusive; default `1e-6 M`.
- `Filter solids` defaults on and maps directly to pymatgen `filter_solids`.
- Invalid input makes no credential lookup or network request.
- Heatmap controls are disabled placeholders and never alter calculation state.
- Preserve legacy callers with default concentrations and solid filtering.

## File Structure

```text
pourbaix_r4/models.py                 # immutable scientific input additions
pourbaix_r4/domain.py                 # concentration/filter validation
pourbaix_r4/calculation.py            # pymatgen constructor forwarding
pourbaix_r4/ui/composition_panel.py   # redesigned composition editor
tests/r4/test_domain.py               # input contract regressions
tests/r4/test_calculation.py          # forwarding contract
tests/r4/test_ui_composition.py       # editor and advanced-option behavior
```

---

### Task 1: Extend the scientific input contract

**Files:** modify `pourbaix_r4/models.py`, `pourbaix_r4/domain.py`, `tests/r4/test_domain.py`.

**Interfaces:** `CalculationInput.ion_concentrations`, `CalculationInput.filter_solids`, and `parse_calculation_input(..., ion_concentrations=None, filter_solids=True)`.

- [ ] Write failing tests proving defaults, element-specific concentrations, H/O exclusion, and rejection below `1e-6`, above `5`, zero, NaN, missing, or extra keys.

```python
parsed = parse_calculation_input(("Sb", "Se", "O"), {"Sb": 2, "Se": 3}, (0, 14), (-2, 4), ion_concentrations={"Sb": "1e-6", "Se": "0.01"}, filter_solids=False)
assert parsed.conc_dict == {"Sb": 1e-6, "Se": 0.01}
assert parsed.filter_solids is False
```

- [ ] Run `pytest -q tests/r4/test_domain.py` and confirm the new arguments fail.
- [ ] Add frozen tuple storage plus `conc_dict` property; validate exact closed-element keys and range while preserving old-call defaults.
- [ ] Rerun the focused test and `pytest -q tests/r4/test_models_session.py`.
- [ ] Commit `feat: add R4 concentration and solid filter contract`.

### Task 2: Forward options to pymatgen exactly once

**Files:** modify `pourbaix_r4/calculation.py`, `tests/r4/test_calculation.py`.

**Interfaces:** `diagram_factory(entries, comp_dict=..., conc_dict=..., filter_solids=...)`.

- [ ] Extend the stub factory test to capture all constructor keywords:

```python
def diagram_factory(entries, **kwargs):
    received.update(kwargs)
    return StubDiagram(entries, kwargs["comp_dict"])
assert received["conc_dict"] == {"Sb": 1e-6, "Se": 0.01}
assert received["filter_solids"] is False
```

- [ ] Run `pytest -q tests/r4/test_calculation.py` and confirm missing keyword assertions fail.
- [ ] Pass `inputs.comp_dict`, `inputs.conc_dict`, and `inputs.filter_solids` to the diagram factory without changing clipping or labels.
- [ ] Rerun calculation, plotting, and export tests.
- [ ] Commit `feat: forward R4 advanced composition options`.

### Task 3: Replace the composition panel interaction

**Files:** modify `pourbaix_r4/ui/composition_panel.py`, `tests/r4/test_ui_composition.py`, `tests/r4/test_ui_workbench.py`.

**Interfaces:** `apply_formula`, `selected_elements`, `ratio_values`, `concentration_values`, `composition_summary`, and unchanged `calculation_requested` signal.

- [ ] Write failing Qt tests for editing-finished formula commit, `Sb : Se = 2 : 3` summary, chip synchronization, dynamic concentrations, Filter Solids, range section, and disabled heatmap controls.

```python
panel.formula_input.setText("Sb2Se3")
panel.formula_input.editingFinished.emit()
assert panel.composition_summary.text() == "Sb : Se = 2 : 3"
assert panel.concentration_values() == {"Sb": "0.000001", "Se": "0.000001"}
assert panel.heatmap_toggle.isEnabled() is False
```

- [ ] Run `pytest -q tests/r4/test_ui_composition.py tests/r4/test_ui_workbench.py` and confirm missing controls fail.
- [ ] Remove the mandatory Apply button, connect `editingFinished` to formula commit, build element chips and live summary, and rebuild ratio/concentration rows atomically.
- [ ] Add a checkable Advanced Options group containing Filter Solids, concentrations, Diagram Range, and disabled Heatmap/Heatmap Entry placeholders.
- [ ] Ensure every committed scientific change emits `input_changed`; construct `CalculationInput` with concentrations/filter values before emitting `calculation_requested`.
- [ ] Run focused UI tests, `--gui-smoke`, and full `pytest -q`.
- [ ] Commit `feat: redesign R4 composition and advanced options UI`.

## Final Verification

- [ ] `pytest -q` passes including R2/R3 regressions.
- [ ] `python pourbaix_studio_R4.py --gui-smoke` succeeds without credentials or network.
- [ ] TiO2, Sb2Se3, BiVO4, and FeNi editor states show correct closed-element ratios and concentration rows.
- [ ] Appearance, language, and disabled heatmap controls leave `CalculationInput` unchanged.
