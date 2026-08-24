# Pourbaix Studio R4 Composition and Advanced Options Design

Date: 2026-08-24

## Objective

Replace the confusing formula/apply/ratio workflow with one composition-first
editor inspired by the Materials Project Pourbaix page, while preserving R4's
scientific contract and adding supported pymatgen concentration and solid-filter
controls.

## Confirmed scope

- One primary `System composition` editor accepts a chemical formula such as
  `TiO2`, `Sb2Se3`, `BiVO4`, or `FeNi`. Formula application is immediate on
  editing completion; a separate mandatory Apply step is removed.
- The parsed closed elements appear as removable element chips and can also be
  selected from a searchable periodic-table dialog.
- A composition summary always shows the current closed-element ratio, for
  example `Sb : Se = 2 : 3`, plus the effective pymatgen composition mapping.
- H and O remain open species. They appear in a separate reservoir notice and
  never receive ratio or ion-concentration controls.
- Each closed element receives an ion-concentration field in mol/L. The default
  is `1e-6 M`; accepted values are finite and within `1e-6–5 M` inclusive.
- `Filter solids` defaults on and maps directly to
  `PourbaixDiagram(..., filter_solids=...)`.
- pH and potential limits move into a named `Diagram range` section.
- Advanced options are collapsible and do not compete visually with composition
  and Generate.
- Heatmap and Heatmap Entry are visible as disabled `Coming later` controls.
  They do not alter calculation state, snapshots, exports, or cache keys in this
  release.

## Interaction flow

1. The user enters a formula or selects elements.
2. R4 parses the formula and immediately rebuilds element chips, composition
   ratios, and ion-concentration rows.
3. The user may edit relative ratios and concentrations, then sees a live
   composition summary.
4. Generate validates formula, ratios, concentrations, pH, and potential before
   credential resolution or network access.
5. Calculation passes closed ratios as `comp_dict`, concentrations as
   `conc_dict`, and the solid switch as `filter_solids` to pymatgen.

## Architecture changes

- `CalculationInput` gains immutable `ion_concentrations` and `filter_solids`
  values. H/O exclusion is enforced by the domain layer.
- `parse_calculation_input` accepts optional concentration and filter inputs;
  legacy callers receive `1e-6 M` and `True` defaults.
- `calculate_snapshot` forwards these values to the diagram factory. Appearance,
  language, heatmap placeholders, and layout remain outside the snapshot's
  scientific input.
- `CompositionPanel` is redesigned around one formula editor, chips, composition
  control, concentration control, range control, and collapsible advanced area.

## Error and state behavior

- Invalid or incomplete formula text shows an inline message and does not erase
  the last confirmed editor values until editing is committed.
- Any committed change to elements, ratios, concentrations, filter solids, pH,
  or potential marks the current result stale.
- Concentration errors name the affected element and accepted unit/range.
- No API key or remote request is involved while editing composition options.

## Tests and acceptance

- Domain tests cover TiO2, Sb2Se3, FeNi without O, H/O exclusion, concentration
  defaults/bounds, and filter forwarding.
- UI tests cover immediate formula commit, chip synchronization, periodic-table
  selection, dynamic concentration rows, live summary, collapsible options, and
  disabled heatmap placeholder.
- Calculation tests prove `comp_dict`, `conc_dict`, and `filter_solids` reach the
  diagram constructor exactly once.
- Existing R2/R3/R4 tests remain green. Live Ti-O, Sb-Se, and Fe-Ni validation is
  deferred until the user supplies a runtime API key.
