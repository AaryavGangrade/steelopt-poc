# SteelOpt — synthetic nesting + offcut recovery POC

An **educational, executable decision-support prototype** accompanying an FDE case study for a structural-steel fabricator. **No client data is included.** This is not a CNC tool, a validated optimizer, an AI model, a STRUMIS integration, or a claim of factory savings.

## Why this prototype?

The client uses STRUMIS/PLM, currently nests manually despite having an automatic option, and wants to understand wastage and reusable offcuts. Before writing bespoke AI, a credible FDE should validate actual waste accounting and compare native capabilities on identical production jobs. This small demonstrator makes that evaluation concrete, including constraints that can veto apparently attractive allocations.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
jupyter notebook demo.ipynb
```

Open `demo.ipynb` from the repository root and run all cells. A synthetic plot is written to `outputs/nesting-comparison.png`. `src/steelopt.py` contains all logic; `tests/` contains validation tests.

## What actually runs

- Loads fully **synthetic** plate inventory, offcuts, projects and required rectangular parts from `data/`.
- Creates two comparable **toy** 2D shelf layouts, using input order and sorted order, and reports utilization, unallocated area and **unplaced parts**.
- Validates identity, allowed rotations, material grade/thickness, bounds and conservative pairwise kerf clearance.
- Suggests offcut candidates subject to availability, traceability, thickness, grade, rotation and geometric fit.
- Flags cross-project suggestions as `PENDING_COST_CONTROL_APPROVAL`, never auto-transfers stock.
- Rejects wrong-thickness, wrong-grade, quarantined and untraceable stock.
- Reports theoretical material-area value only; *realized_savings* stays unknown.

## Important interpretation of metrics

`utilization_pct = area of placed parts / plate area`. This is **not** factory yield or avoidable scrap; remaining space may include saleable offcuts, unusable islands, and kerf. If either illustrative algorithm leaves jobs unplaced, comparing utilization alone is misleading. The optional `illustrative_area_value` is based on a synthetic cost/m², not evidence of purchasing avoidance. A value outcome would require matching the inventory withdrawal with actual avoided replenishment, while accounting for costs and project ownership.

## Integration stance

There is **no asserted STRUMIS API**, no database credentials, and no automatic writes to ERP/PLM/CNC. A real pilot should first confirm export capabilities with the customer's IT/vendor and compare **manual / existing STRUMIS auto / any proposed augmentation** on identical, released production jobs. Nesters and factory staff sign off on cut feasibility; Cost Control authorizes inter-project cost allocation; procurement/yard validates physical offcuts.

## Boundaries / not production-ready

Only axis-aligned rectangular 2D stock/parts. No structural profile nesting, arbitrary contours, irregular offcuts, heat/lot tracking, actual NC toolpaths, machine constraints, kerf optimization, cutting times, rolling direction, weld/quality criteria, or scheduling. All geometry/money is synthetic. No autonomous CNC instructions. No quantitative claim that this algorithm outperforms current STRUMIS features.

## Ownership and use

Prepared as an optional technical appendix for a hiring case study; not for client deployment. Synthetic illustrative fixtures carry no confidential client information.
