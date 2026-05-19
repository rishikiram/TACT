# Toolkit and Application for Clinical Trials (TACT)

A toolkit for exploring ClinicalTrials.gov data — a Python pipeline for ingesting, cleaning, and analyzing studies into a local SQLite database, paired with a web app for interactive mapping and visualization.

## Python Data Pipeline

### How to run

```bash
cd backend_py
pip install -r requirements.txt

# list available presets
python ingest.py --list

# run a named preset (defined in queries.yaml)
python ingest.py nsclc

# open the EDA notebook
jupyter notebook eda.ipynb
```

### Architecture

The pipeline is independent of the web app. It fetches from CT.gov, cleans the data, and writes to `data/clinical_trials.db`. Ingestion is idempotent — re-runs upsert by NCT ID.

```
backend_py (Python pipeline)  ──►  data/clinical_trials.db (SQLite)
```

Query presets are defined in `backend_py/queries.yaml`. Each preset maps a name (e.g. `nsclc`, `oncology`) to CT.gov v2 API parameters. The `eda.ipynb` notebook reads from the database and produces figures saved to `backend_py/figures/` and `figures/`.

| File | Description |
|---|---|
| `db.py` | database schema and definition |
| `clean.py` | data processing, converting the json from clinicaltrials.gov into database rows|
| `queries.yaml` | yaml file directly defining query to clinicaltrials.gov |
| `injest.py` | script for CLI to run injection |

#### Adding a new preset

Add an entry to `backend_py/queries.yaml` using CT.gov v2 API parameter keys, then run `python ingest.py <your-preset>`.

## Web App

### How to run

| | Command | URL |
|---|---|---|
| Frontend | `npm run dev` in `/frontend` | `http://localhost:5173` |
| Backend | `npm run dev` in `/backend` | `http://localhost:3001` |

### Architecture

The frontend never calls ClinicalTrials.gov directly. All requests go through the Express backend, which forwards them to the CT.gov v2 API and pipes the response back. The `/api/trials/all` endpoint fetches up to 20,000 results and caches responses to disk.

```
frontend (React + Vite)
    │  HTTP
    ▼
backend (Node.js + Express + TypeScript)
    │  CT.gov v2 API
    ▼
ClinicalTrials.gov
```

Preset queries are defined in `frontend/src/api/queries.ts` as named `FetchTrialsParams` objects (e.g. `ONCOLOGY`, `NSCLC`, `RECRUITING_DIABETES`). The user selects one via toggle buttons in `App.tsx`, which drives `useTrials` — a TanStack Query hook wrapping `fetchTrials`.

#### Main Components

**`TrialTable.tsx`** — renders trials as an expandable list. Click a row to see NCT ID, phase, conditions, site count, and brief summary.

**`MapShell.tsx`** — thin MapLibre GL wrapper. Accepts `sources`, `layers`, and an `onLoad` callback that hands back the live map instance.

**`UsStatesMap.tsx`** — choropleth of trials per US state. `aggregateByState` counts trials per state (one count per trial regardless of how many sites it has there), enriches the bundled GeoJSON with that count, and passes it to `MapShell`. Hovering a state shows a popup with the state name and trial count.

**`ScatterMap.tsx`** — plots individual trial sites as points with random jitter for overlapping coordinates.

**`HeatMap.tsx`** — heatmap density view of trial site locations.

## Tech stack

Python 3 · SQLite · pandas · Jupyter · React + Vite · TanStack Query · MapLibre GL JS · Node.js + Express · TypeScript

<!-- ## Tests

- **Backend** (Jest + Supertest): proxy forwards correctly, responds 502 on upstream error
- **Frontend** (Vitest): `fetchTrials` URL and response mapping, `useTrials` success/error/disabled states, `TrialTable` render and expand/collapse, `aggregateByState` count logic -->

## References

- [ClinicalTrials.gov API docs](https://clinicaltrials.gov/data-api/api)

<!-- last updated on commit: 529a1d9 -->
