# Numerical Contract

## Pending scientific semantics

No unresolved scientific semantics block R3. External clean-machine portability is a release acceptance gate, not a scientific-semantic question.

## Variables and units

| Name | Meaning | Canonical unit | Rules |
|---|---|---|---|
| `elements` | Chemical system supplied to Materials Project | element symbols | Valid unique symbols; at least one non-H/O element |
| `ratios` | Relative amounts of closed composition dimensions | dimensionless | One finite positive value per non-H/O element |
| `comp_dict` | Closed-system composition passed to pymatgen | dimensionless mapping | Must never contain H or O |
| `pH_range` | Horizontal plot/export limits | dimensionless | Two finite values with lower < upper |
| `potential_range` | Vertical plot/export limits | V versus SHE | Two finite values with lower < upper |
| boundary `pH` | Domain-vertex coordinate | dimensionless | Produced by pinned pymatgen, clipped to requested window |
| boundary `E` | Domain-vertex coordinate | V versus SHE | Produced by pinned pymatgen, clipped to requested window |

## Formula and authority

Pourbaix thermodynamics, stability domains, and ratio normalization are delegated unchanged to the exact versions in `requirements-lock-py313-win64.txt`. R3 adds no energy model. Polygon/window intersection is delegated to pinned Shapely; exported vertices are closed-domain boundaries returned from pymatgen and clipped to the user window.

## Numerical rules

- Inputs must be finite; NaN and infinities are rejected.
- Ranges are ordered strictly and are not silently swapped.
- Duplicate elements and missing ratios are rejected.
- Positive ratios may be normalized by pymatgen; R3 does not normalize independently.
- No interpolation, extrapolation, integration, or silent clipping of finite raw inputs is introduced.
- Plot fonts, colors, widths, labels, DPI, transparency, and viewport decoration do not alter boundary data.

## Reference and tolerance

Contract tests use exact literals for parsing and H/O exclusion. Scientific construction is verified by import/integration smoke against the pinned pymatgen environment rather than by copying old R2 numeric outputs. Boundary export/plot separation is a structural invariant; no new floating-point approximation is asserted by R3.

## Invariants

- H/O are open species and never keys of `comp_dict`.
- Invalid input makes no network call.
- A failed calculation invalidates the previous figure and associated metadata.
- Styling cannot change exported boundary coordinates.
- API keys never enter logs, manifests, dependencies, or archives.

