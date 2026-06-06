# AACT Table Guide

## `design_groups`
Protocol-section arm definitions — what the sponsor *planned* at registration time.

| Column | Notes |
|---|---|
| `nct_id` | Trial identifier |
| `group_type` | Arm role: `'Experimental'`, `'Active Comparator'`, `'Placebo Comparator'`, `'Sham Comparator'`, `'No Intervention'`, `'Other'` |
| `title` | Arm label as registered |
| `description` | Free-text description of the arm |

**Gotcha:** titles can drift between registration and results submission, so `design_groups.title` does not reliably match `result_groups.title`. Use `result_groups.group_type` directly when filtering by arm role in results queries.

---

## `result_groups`
Results-section arm definitions — one row per arm per result type per trial.

| Column | Notes |
|---|---|
| `nct_id` | Trial identifier |
| `result_type` | `'Baseline'`, `'Outcome'`, or `'Reported Event'` — each arm gets a separate row for each type |
| `ctgov_group_code` | Short code (`'O1'`, `'O2'`, `'B1'`, `'E1'`, …) — join key to `outcome_measurements` and `reported_events` |
| `group_type` | Same vocabulary as `design_groups.group_type` |
| `title` | Arm label as reported in results (may differ from `design_groups.title`) |
| `description` | Free-text description |

**Key pattern:** to get measurements for a specific arm type, filter `result_groups` on `group_type` and `result_type = 'Outcome'`, then join to `outcome_measurements` on `(nct_id, ctgov_group_code)`.

---

## `outcomes`
One row per reported outcome measure per trial (the measure definition, not the numbers).

| Column | Notes |
|---|---|
| `id` | Primary key — join target for `outcome_measurements.outcome_id` |
| `nct_id` | Trial identifier |
| `outcome_type` | `'Primary'` or `'Secondary'` |
| `title` | Measure name (e.g. "Overall Survival") |
| `description` | Full measure description |
| `timeframe` | When the measurement was taken |
| `population` | Analysis population description |
| `measure` | Statistical measure used (sometimes duplicates `title`) |

---

## `outcome_measurements`
One row per arm × outcome cell — the actual numbers.

| Column | Notes |
|---|---|
| `nct_id` | Trial identifier |
| `outcome_id` | FK → `outcomes.id` |
| `ctgov_group_code` | FK → `result_groups.ctgov_group_code` (scoped to same `nct_id` and `result_type = 'Outcome'`) |
| `param_type` | Statistic type: `'Mean'`, `'Median'`, `'Number'`, `'Least Squares Mean'`, etc. |
| `param_value` | The reported statistic (stored as text) |
| `dispersion_type` | `'Standard Deviation'`, `'95% Confidence Interval'`, `'Inter-Quartile Range'`, etc. |
| `dispersion_value` | Spread value (stored as text; CI stored as `'lower limit, upper limit'`) |
| `units` | Unit of measure |

**Join pattern:**
```sql
result_groups rg
  JOIN outcome_measurements om ON om.nct_id = rg.nct_id AND om.ctgov_group_code = rg.ctgov_group_code
  JOIN outcomes o              ON o.id = om.outcome_id
WHERE rg.result_type = 'Outcome'
```
