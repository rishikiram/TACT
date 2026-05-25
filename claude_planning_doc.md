# TACT: Landing Page + FastAPI Backend Plan

## Goal

Restructure the frontend to have a landing page that routes users to two separate explorer pages:

1. **Live Explorer** — the current page (map + table), fetching live data from ClinicalTrials.gov via the existing TypeScript/Express backend.
2. **Database Explorer** — a new page with the same map + table UI, but fetching from the local SQLite database via a new **FastAPI** Python backend.

---

## Architecture Overview

```
User
 │
 ▼
Landing Page (React Router)
 ├──► /live    → LiveExplorer (existing UI, calls TypeScript backend :3001)
 └──► /db      → DbExplorer   (same UI, calls FastAPI backend :8000)

TypeScript Backend (:3001)   ← proxies ClinicalTrials.gov API
FastAPI Backend (:8000)      ← reads from SQLite (data/clinical_trials.db)
```

---

## Phase 1: Add React Router + Landing Page

### 1.1 Install React Router

```bash
npm install react-router-dom
```

### 1.2 Create Landing Page Component

File: `frontend/src/pages/LandingPage.tsx`

- Two large cards/buttons:
  - **"Live Explorer"** → navigates to `/live`
    - Description: "Search ClinicalTrials.gov in real time"
  - **"Database Explorer"** → navigates to `/db`
    - Description: "Browse trials stored in the local database"
- Minimal styling, consistent with existing `App.css`

### 1.3 Restructure App.tsx into a Page Component

- Rename or move current `App.tsx` content into `frontend/src/pages/LiveExplorer.tsx`
- Keep all existing logic unchanged (presets, map toggle, `useAllTrials`, etc.)
- `App.tsx` becomes the router shell:

```tsx
// App.tsx (new)
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LiveExplorer from './pages/LiveExplorer'
import DbExplorer from './pages/DbExplorer'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/live" element={<LiveExplorer />} />
        <Route path="/db" element={<DbExplorer />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### 1.4 Create DbExplorer Placeholder

File: `frontend/src/pages/DbExplorer.tsx`

- Clone `LiveExplorer.tsx` as starting point
- Swap data-fetching hooks/API calls to point at `/db-api` (the FastAPI proxy)
- Keep same preset selector, map toggle, `TrialTable`, and map components
- Add a "Back" link to `/`

---

## Phase 2: FastAPI Backend

### 2.1 New File Structure

```
backend_py/
├── api.py            ← NEW: FastAPI app (main entry point)
├── db.py             ← existing: database helpers (reuse query())
├── clean.py          ← existing: data cleaning utilities
├── ctgov.py          ← existing: CT.gov client (not needed by API)
├── ingest.py         ← existing: ingestion CLI (unchanged)
└── queries.yaml      ← existing: preset definitions
```

### 2.2 Dependencies

Add to `backend_py/requirements.txt` (or create it):

```
fastapi
uvicorn[standard]
```

### 2.3 FastAPI App (`backend_py/api.py`)

**Base URL:** `http://localhost:8000`

**CORS:** Allow `http://localhost:3000` (frontend dev server)

#### Endpoints

---

**`GET /db/presets`**

Returns the list of available preset names from `queries.yaml`.

Response:
```json
{ "presets": ["oncology", "nsclc", "nsclc_adenocarcinoma", "recruiting_diabetes"] }
```

---

**`GET /db/trials`**

Returns all trials for a given preset (or raw filters) from SQLite.

Query params:
- `preset` (string, optional) — load filter params from `queries.yaml`
- `condition` (string, optional) — filter by condition (LIKE match on `conditions` JSON column)
- `status` (string, optional) — filter by `status`
- `phase` (string, optional) — comma-separated phases (e.g., `"2,3"`)

Response schema mirrors the TypeScript backend's `Trial` interface so the frontend components can be reused without modification:

```json
{
  "trials": [
    {
      "nctId": "NCT...",
      "briefTitle": "...",
      "overallStatus": "RECRUITING",
      "phase1": false,
      "phase2": true,
      "phase3": true,
      "phase4": false,
      "phases": ["PHASE2", "PHASE3"],
      "conditions": ["Non-Small Cell Lung Cancer"],
      "conditionKeywords": [...],
      "interventions": [...],
      "armGroups": [...],
      "locations": [
        { "facility": "...", "city": "...", "state": "...", "country": "...", "geoPoint": { "lat": 0.0, "lon": 0.0 } }
      ],
      "sponsor": "...",
      "startDate": "...",
      "completionDate": "...",
      "primaryOutcomes": [...],
      "secondaryOutcomes": [...],
      "enrollment": 120,
      "enrollmentType": "ESTIMATED"
    }
  ],
  "totalCount": 450
}
```

**Implementation notes:**
- Parse `conditions`, `locations`, `interventions`, etc. from JSON strings (stored as TEXT in SQLite)
- Re-use `db.query()` from `db.py`
- Construct WHERE clause dynamically based on provided filters
- If `preset` is provided, load the corresponding params from `queries.yaml` and translate to SQL filters

---

**`GET /db/trial/{nct_id}`**

Returns a single trial by NCT ID.

Response: same `Trial` shape as above (single object, not array)

---

### 2.4 Preset-to-SQL Translation

`queries.yaml` uses CT.gov API parameters (`query.cond`, `query.term`, `filter.advanced`). These need to be translated to SQLite WHERE clauses for the DB explorer:

| CT.gov param | SQLite column | Match strategy |
|---|---|---|
| `query.cond` | `conditions` (JSON TEXT) | `conditions LIKE '%<value>%'` |
| `query.term` | `condition_keywords` or `title` | `condition_keywords LIKE '%<value>%' OR title LIKE '%<value>%'` |
| `filter.overallStatus` | `status` | exact match |
| `filter.advanced` (PHASE2, etc.) | `phase2`, `phase3` columns | boolean column = 1 |

---

## Phase 3: Wire Frontend DbExplorer to FastAPI

### 3.1 Vite Proxy

Add a second proxy entry in `frontend/vite.config.ts`:

```ts
proxy: {
  '/api': 'http://localhost:3001',
  '/db-api': {
    target: 'http://localhost:8000',
    rewrite: (path) => path.replace(/^\/db-api/, '')
  }
}
```

### 3.2 New API Client

File: `frontend/src/api/dbTrials.ts`

- `fetchDbPresets(): Promise<string[]>` — calls `GET /db-api/db/presets`
- `fetchDbTrials(params): Promise<{ trials: Trial[], totalCount: number }>` — calls `GET /db-api/db/trials`
- Returns the same `Trial` type as `trials.ts` (no frontend interface changes needed)

### 3.3 New React Query Hook

File: `frontend/src/hooks/useDbTrials.ts`

- Mirrors `useAllTrials.ts` but calls `fetchDbTrials()`
- Uses a different query key prefix (`['dbTrials', params]`) to avoid cache collisions

### 3.4 DbExplorer Page

`frontend/src/pages/DbExplorer.tsx`:

- Loads preset list from `fetchDbPresets()` (dynamic, from DB content)
- Uses `useDbTrials()` hook instead of `useAllTrials()`
- All map components and `TrialTable` are reused without change
- Add a visible label ("Database Explorer — local SQLite") to distinguish from live view

---

## Phase 4: Developer Experience

### 4.1 Run Scripts

Update `package.json` or add a root-level `Makefile`/`scripts` to start both backends:

```bash
# Start TypeScript backend
cd backend && npx ts-node server.ts

# Start FastAPI backend
cd backend_py && uvicorn api:app --reload --port 8000

# Start frontend
cd frontend && npm run dev
```

Consider a `Makefile` with a `make dev` target that starts all three in parallel.

### 4.2 Environment Awareness

The FastAPI backend should fail fast with a clear error if `data/clinical_trials.db` doesn't exist or is empty, with a helpful message pointing to `ingest.py`.

---

## Implementation Order

1. **Phase 2 first** — Build and test FastAPI backend independently with `curl`/Swagger UI (`/docs`)
2. **Phase 1** — Add React Router, create landing page, move existing App content to `LiveExplorer.tsx`
3. **Phase 3** — Wire `DbExplorer.tsx` to FastAPI; test full stack
4. **Phase 4** — Polish dev scripts

---

## Files Created / Modified

| File | Action |
|---|---|
| `frontend/src/App.tsx` | Modified — becomes router shell |
| `frontend/src/pages/LandingPage.tsx` | Created |
| `frontend/src/pages/LiveExplorer.tsx` | Created — existing App content moved here |
| `frontend/src/pages/DbExplorer.tsx` | Created — DB-backed explorer |
| `frontend/src/api/dbTrials.ts` | Created — FastAPI client |
| `frontend/src/hooks/useDbTrials.ts` | Created — React Query hook for DB data |
| `frontend/vite.config.ts` | Modified — add `/db-api` proxy |
| `backend_py/api.py` | Created — FastAPI app |
| `backend_py/requirements.txt` | Created (or updated) |

**Unchanged:** All existing backend files, `TrialTable.tsx`, all map components, `useAllTrials.ts`, `trials.ts`, `queries.ts`, `geoPoints.ts`

---

## Key Constraints

- The `Trial` TypeScript interface must remain stable — FastAPI response must serialize to match it exactly so map/table components work without changes.
- SQLite JSON columns (`conditions`, `locations`, etc.) need `json.loads()` in the FastAPI route before returning.
- The DB explorer preset list is driven by what data is actually in the database (queried from `queries.yaml` keys), not hardcoded in the frontend.
