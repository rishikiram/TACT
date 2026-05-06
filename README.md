# Mapping Application for Clinical Trials (MACT)

A local web app that fetches clinical trial data from ClinicalTrials.gov and displays it as an interactive list and maps. Includes a Python pipeline for ingesting and cleaning studies into a local SQLite database.

## How it runs

### Web app (two terminals)

| | Command | URL |
|---|---|---|
| Frontend | `npm run dev` in `/frontend` | `http://localhost:3000` |
| Backend | `npm run dev` in `/backend` | `http://localhost:3001` |

### Data pipeline

```bash
cd backend_py
pip install -r requirements.txt
python ingest.py --condition "lung cancer" --status RECRUITING
jupyter notebook eda.ipynb
```

## Architecture

The frontend never calls ClinicalTrials.gov directly. All requests go through the Express backend, which forwards them to the CT.gov v2 API and pipes the response back. The `/api/trials/all` endpoint fetches up to 20,000 results and caches responses to disk.

Preset queries are defined in `frontend/src/api/queries.ts` as named `FetchTrialsParams` objects (e.g. `ONCOLOGY`, `NSCLC`, `RECRUITING_DIABETES`). The user selects one via toggle buttons in `App.tsx`, which drives `useTrials` — a TanStack Query hook wrapping `fetchTrials`.

The Python pipeline (`backend_py/`) fetches from CT.gov, cleans the data, and writes to `data/clinical_trials.db`. Ingestion is idempotent — re-runs upsert by NCT ID.

## Components

**`TrialTable.tsx`** — renders trials as an expandable list. Click a row to see NCT ID, phase, conditions, site count, and brief summary.

**`MapShell.tsx`** — thin MapLibre GL wrapper. Accepts `sources`, `layers`, and an `onLoad` callback that hands back the live map instance.

**`UsStatesMap.tsx`** — choropleth of trials per US state. `aggregateByState` counts trials per state (one count per trial regardless of how many sites it has there), enriches the bundled GeoJSON with that count, and passes it to `MapShell`. Hovering a state shows a popup with the state name and trial count.

**`ScatterMap.tsx`** — plots individual trial sites as points with random jitter for overlapping coordinates.

**`HeatMap.tsx`** — heatmap density view of trial site locations.

## Adding a new map

Create a new file in `frontend/src/components/maps/`. Accept `trials: Trial[]` as a prop, transform the data, and pass GeoJSON sources and MapLibre layer configs to `MapShell`.

## Tech stack

React + Vite · TanStack Query · MapLibre GL JS · Node.js + Express · TypeScript · Python 3 · SQLite · pandas · Jupyter

## Tests

- **Backend** (Jest + Supertest): proxy forwards correctly, responds 502 on upstream error
- **Frontend** (Vitest): `fetchTrials` URL and response mapping, `useTrials` success/error/disabled states, `TrialTable` render and expand/collapse, `aggregateByState` count logic

## References

- [ClinicalTrials.gov API docs](https://clinicaltrials.gov/data-api/api)

<!-- last updated on commit: f1204e1 -->
