# Plane Lap Times Dashboard

A Streamlit dashboard that displays real-time plane assembly lap times pulled from Snowflake. It auto-refreshes every 15 seconds and shows build status and per-assembly-line timing data for each operator.

## Features

- **Plane Build Status** — shows each plane's completion status and total build time once all assembly lines have recorded a time
- **Per-assembly-line tables** — lap times broken down by operator for each of the six assembly lines
- Auto-refreshes every 15 seconds

## Assembly Lines

- White Assembly
- Black Assembly
- Color Assembly
- Fuselage Assembly
- Wing Assembly
- Final Assembly

## Requirements

- Python 3.9+
- Snowflake account with access to `CLASS_PROJECT.OT_PLANE_PROJECT`

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create `.streamlit/secrets.toml` with your Snowflake credentials:

   ```toml
   [snowflake]
   account   = "your-account-identifier"
   user      = "your-username"
   password  = "your-password"
   database  = "CLASS_PROJECT"
   schema    = "OT_PLANE_PROJECT"
   warehouse = "your-warehouse"
   role      = "your-role"   # optional
   ```

   > **Do not commit this file.** Ensure `.streamlit/secrets.toml` is in your `.gitignore`.

3. Run the app:

   ```bash
   streamlit run plane_lap_dashboard.py
   ```

## Snowflake Tables

| Table | Purpose |
|---|---|
| `OT_PLANE_LAP_TIMES` | Lap time records per operator and plane |
| `OT_PLANE_TEAM_MEMBERS` | Maps operators to assembly lines |
