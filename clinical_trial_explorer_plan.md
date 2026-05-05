# Adding a Database for Cleaned Data

I want to add data cleaning processes and store them in a database. Right now the goals are simplicity and to test things with prototypes.

## How to implement

### 1. Convert backend to Python
- [ ] Create a new `backend_py/` directory alongside the existing TypeScript backend
- [ ] Keep the TypeScript backend running — the Python backend will be separate, focused only on data ingestion and cleaning (not serving the frontend API yet)
- [ ] Use **FastAPI** for a lightweight API if needed later, or run scripts standalone for now
- [ ] Dependencies: `requests`, `sqlite3` (stdlib), `pandas` for cleaning, `python-dotenv` for config

### 2. Add a SQLite database
- [ ] Create `clinical_trials.db` in the project root (or `data/`)
- [ ] Define a schema for the cleaned studies table. Start with key fields:
  - `nct_id` (primary key)
  - `title`, `status`, `phase`
  - `start_date`, `completion_date`
  - `sponsor`, `sponsor_type`
  - `conditions` (pipe-separated or JSON array)
  - `interventions` (pipe-separated or JSON array)
  - `enrollment`, `enrollment_type`
  - `locations` (JSON array of city/state/country)
  - `lat`, `lon` (for mapping, if geocoded)
  - `ingested_at` timestamp
- [ ] Write a `db.py` module to initialize the database and provide helper functions (insert, upsert, query)
- [ ] Use `upsert` (INSERT OR REPLACE) so re-running ingestion is idempotent

### 3. Add data cleaning functions
- [ ] Write a `clean.py` module with individual, testable cleaning functions:
  - Normalize dates to ISO format
  - Normalize status/phase values to consistent strings
  - Parse nested CT.gov JSON fields (e.g., `protocolSection.sponsorCollaboratorsModule`) into flat columns
  - Drop studies missing critical fields (e.g., no NCT ID, no title)
  - Extract primary location (first US site or overall facility)
- [ ] Use `pandas` DataFrames as the intermediate representation during cleaning
- [ ] Cleaning is separate from ingestion — raw → clean as a distinct step

### 4. Add ingestion and EDA scripts
- [ ] `ingest.py` — fetches from CT.gov API (port logic from `ctgov.ts`), stores raw JSON in a `raw/` folder or raw table, then runs cleaning and writes to SQLite
- [ ] `eda.ipynb` — a Jupyter notebook for exploratory analysis:
  - Load cleaned data from SQLite into a DataFrame
  - Summary stats: phase distribution, status breakdown, enrollment histograms
  - Time-series: trials opened per year
  - Geographic: trials by state/country
- [ ] `query.py` — reusable helper to load the SQLite DB into a DataFrame for use in notebooks and scripts

### 5. Keep current functionality
- [ ] The TypeScript backend (`backend/`) and React frontend continue to run independently
- [ ] The SQLite database can eventually be queried by the TypeScript backend (they share the same `.db` file)
- [ ] No changes to the existing API routes during this phase

## File layout (target state)

```
MACT/
  backend/          ← existing TypeScript API (unchanged)
  backend_py/
    db.py           ← SQLite init and helpers
    clean.py        ← cleaning functions
    ingest.py       ← fetch from CT.gov + write to DB
    query.py        ← load DB into DataFrame
    eda.ipynb       ← exploratory analysis notebook
    requirements.txt
  data/
    clinical_trials.db
    raw/            ← optional: cached raw JSON responses
  frontend/         ← unchanged
```
