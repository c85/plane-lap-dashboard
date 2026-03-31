# Claude Code Guide — Plane Lap Dashboard

## Project Overview

Single-file Streamlit app (`plane_lap_dashboard.py`) that reads lap time data from Snowflake and renders it as a live-refreshing dashboard. All Snowflake connection and query logic lives directly in the main file.

## Architecture

- **`plane_lap_dashboard.py`** — the entire app: Snowflake connection helpers, SQL queries, and Streamlit UI
- **`requirements.txt`** — pip dependencies
- **`.streamlit/secrets.toml`** — credentials (never commit this)

## Snowflake

Connection is configured via `st.secrets["snowflake"]`. The `role` key is optional. Queries target:

- `CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_LAP_TIMES`
- `CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_TEAM_MEMBERS`

## Key Conventions

- Keep all logic in `plane_lap_dashboard.py` — do not split into separate modules
- SQL queries are defined as module-level string constants, not constructed inline
- `run_query` always closes the connection in a `finally` block
- The dashboard auto-refreshes every 15 seconds via `st_autorefresh`

## Running Locally

```bash
pip install -r requirements.txt
streamlit run plane_lap_dashboard.py
```

## Security Note

`.streamlit/secrets.toml` must never be committed. Verify with `git ls-files .streamlit/` — it should return nothing.
