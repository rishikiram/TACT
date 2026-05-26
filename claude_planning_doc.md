# Data Dictionary — Prototype Plan

## Goal

Add a live Data Dictionary page to the app that introspects the database and shows per-column schema info and statistics. Manual annotations (source, derivation, plain description) are stored in a `DataDictionary` table, populated by a bootstrap function and editable in place.

The database layer is structured so that switching from SQLite to another relational database (e.g. PostgreSQL) requires changes only in isolated, clearly marked locations — not in `api.py` or any higher-level code.

---

## Architecture

```
Landing Page
 └──► /dictionary  → DataDictionary page (React)
                          │
                          ▼
                    GET /db-api/db/dictionary
                          │
                          ▼
                    FastAPI (api.py)
                          │
                          ▼
                    dictionary_repo.py       ← all DataDictionary SQL ops
                          │
                          ▼
                    db.py                    ← connection factory + dialect helpers
                    (SQLite today, swappable tomorrow)
```

---

## Isolation Strategy

Swapping to PostgreSQL (or another RDBMS) should touch only two files:

| File | Role | What changes for PostgreSQL |
|---|---|---|
| `db.py` | Connection factory + dialect-specific helpers | `connect()` uses `psycopg2`; `get_table_columns()` queries `information_schema` instead of `PRAGMA`; placeholder `?` becomes `%s` |
| `dictionary_repo.py` | All SQL against `DataDictionary` | `INSERT OR IGNORE` becomes `INSERT ... ON CONFLICT DO NOTHING` |
| `api.py` | FastAPI routes | No changes |

### Key dialect helpers isolated in `db.py`

**`get_table_columns(conn, table_name)`** — abstracts schema introspection:
- SQLite: `PRAGMA table_info('<table>')`
- PostgreSQL replacement: `SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s`

All other SQL in `dictionary_repo.py` is standard ANSI SQL except for the one upsert, which is clearly commented.

---

## Phase 0: DataDictionary Table + Repository

### Schema (added to `db.py`)

```sql
CREATE TABLE IF NOT EXISTS DataDictionary (
    table_name        TEXT NOT NULL,
    column_name       TEXT NOT NULL,
    source            TEXT NOT NULL DEFAULT '',
    derivation        TEXT NOT NULL DEFAULT '',
    plain_description TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (table_name, column_name)
);
```

### New file: `backend_py/dictionary_repo.py`

Contains all operations against the `DataDictionary` table. Accepts a connection object — no calls to `connect()` inside, so the caller controls the connection.

```python
def ensure_table(conn) -> None:
    """Create DataDictionary table if it doesn't exist."""

def build_from_table(conn, table_name: str = "studies") -> int:
    """
    Populate DataDictionary with one row per column in table_name.
    Idempotent — existing rows are left untouched.
    Returns the number of columns registered.

    DIALECT NOTE: uses INSERT OR IGNORE (SQLite).
    PostgreSQL equivalent: INSERT ... ON CONFLICT (table_name, column_name) DO NOTHING
    """

def get_annotations(conn, table_name: str) -> dict[str, dict]:
    """
    Returns {column_name: {source, derivation, plain_description}}
    for all rows matching table_name. Pure ANSI SQL.
    """
```

`build_from_table` calls `get_table_columns(conn, table_name)` from `db.py` to get the column list — keeping the `PRAGMA` call in the one place that already owns dialect concerns.

### Bootstrap entry point in `db.py`

```python
def build_data_dictionary(table_name: str = "studies") -> None:
    """
    Called from CLI or init_db(). Delegates entirely to dictionary_repo.
    To switch databases: change connect() above; nothing else here changes.
    """
    from dictionary_repo import ensure_table, build_from_table
    with connect() as conn:
        ensure_table(conn)
        n = build_from_table(conn, table_name)
    print(f"[db] DataDictionary built for '{table_name}' — {n} columns registered")
```

**When to call it:**
- `make dict-init` (new Makefile target)
- `python -c "from db import build_data_dictionary; build_data_dictionary()"`
- Optionally hooked into `init_db()` to run automatically on startup

**Editing annotations directly:**
```bash
sqlite3 data/clinical_trials.db \
  "UPDATE DataDictionary SET plain_description='The unique trial ID' WHERE column_name='nct_id'"
```

A future `PATCH /db/dictionary/{column_name}` endpoint could expose editing via the API.

---

## Phase 1: FastAPI Endpoint

### Endpoint

**`GET /db/dictionary`**

Returns schema metadata, live statistics, and annotations for every column in the `studies` table.

### Response Shape

```json
{
  "table": "studies",
  "totalRows": 450,
  "columns": [
    {
      "name": "nct_id",
      "type": "TEXT",
      "nullable": false,
      "nullCount": 0,
      "nullPct": 0.0,
      "uniqueCount": 450,
      "sampleValues": ["NCT02387216", "NCT04513054", "NCT03521154"],
      "source": "CT.gov API v2 — protocolSection.identificationModule.nctId",
      "derivation": "Direct field extraction, no transformation",
      "plainDescription": "The unique ID assigned to this trial by ClinicalTrials.gov"
    }
  ]
}
```

### Implementation (four passes)

1. **Schema pass** — `get_table_columns(conn, table_name)` from `db.py` (dialect-isolated).

2. **Stats pass** — single query computing null count and unique count for all columns:
   ```sql
   SELECT
     COUNT(*) as total,
     SUM(CASE WHEN nct_id IS NULL THEN 1 ELSE 0 END) as nct_id_nulls,
     COUNT(DISTINCT nct_id) as nct_id_unique,
     ...
   FROM studies
   ```

3. **Sample values pass** — per column, 3 distinct non-null values:
   ```sql
   SELECT DISTINCT nct_id FROM studies WHERE nct_id IS NOT NULL LIMIT 3
   ```

4. **Annotations pass** — `get_annotations(conn, table_name)` from `dictionary_repo.py`.

`api.py` calls these four steps and merges the results. It has no knowledge of `PRAGMA`, `INSERT OR IGNORE`, or any other dialect detail.

---

## Phase 2: Frontend DataDictionary Page

### Route

Add `/dictionary` to `App.tsx` routes and a third card to `LandingPage.tsx`.

### Component: `frontend/src/pages/DataDictionary.tsx`

**Layout:**
- Header: "Data Dictionary" + badge showing total row count (e.g. "450 records")
- Fixed back link top-left, consistent with other pages
- Search input — filters by column name or any annotation field as you type
- Each column is a row; clicking expands it to show annotations

**Collapsed row (always visible):**

| Column Name | Type | Nulls | Unique | Sample Values |
|---|---|---|---|---|
| nct_id | TEXT | 0 (0%) | 450 | NCT02387216, … |
| phase2 | BOOLEAN | 0 (0%) | 2 | true, false |

**Expanded row (on click):**
- **Source:** CT.gov API v2 — protocolSection.identificationModule.nctId
- **Derivation:** Direct field extraction, no transformation
- **Plain description:** The unique ID assigned to this trial by ClinicalTrials.gov

Empty annotation fields show a faint "—" placeholder.

**UX details:**
- JSON array columns show `[array]` in sample values instead of raw JSON
- Graceful error state if FastAPI is unreachable
- "Loading…" while fetching

### API client addition (`frontend/src/api/dbTrials.ts`)

```ts
export interface DictionaryColumn {
  name: string;
  type: string;
  nullable: boolean;
  nullCount: number;
  nullPct: number;
  uniqueCount: number;
  sampleValues: string[];
  source: string;
  derivation: string;
  plainDescription: string;
}

export interface DictionaryResult {
  table: string;
  totalRows: number;
  columns: DictionaryColumn[];
}

export async function fetchDictionary(): Promise<DictionaryResult> {
  const res = await fetch("/db-api/db/dictionary");
  if (!res.ok) throw new Error(`Failed to fetch dictionary: ${res.status}`);
  return res.json();
}
```

---

## Phase 3: Landing Page Card

```ts
{
  title: "Data Dictionary",
  description: "Live schema reference: column types, null rates, and sample values from the database.",
  route: "/dictionary",
  badge: "Schema",
  badgeColor: "#6a1b9a",
}
```

---

## Files Changed

| File | Change |
|---|---|
| `backend_py/db.py` | Add `DataDictionary` schema, `get_table_columns()` helper, `build_data_dictionary()` entry point |
| `backend_py/dictionary_repo.py` | New — all SQL ops against `DataDictionary` table |
| `backend_py/api.py` | Add `GET /db/dictionary` endpoint |
| `frontend/src/pages/DataDictionary.tsx` | New page component |
| `frontend/src/api/dbTrials.ts` | Add `fetchDictionary()` + types |
| `frontend/src/App.tsx` | Add `/dictionary` route |
| `frontend/src/pages/LandingPage.tsx` | Add third card |
| `Makefile` | Add `dict-init` target |

---

## Implementation Order

1. `dictionary_repo.py` + additions to `db.py` — run `make dict-init`, verify rows in DB
2. FastAPI endpoint — test with `curl http://localhost:8010/db/dictionary`
3. Frontend types + `fetchDictionary()` in `dbTrials.ts`
4. `DataDictionary.tsx` page with expandable rows
5. Wire up route + landing page card
