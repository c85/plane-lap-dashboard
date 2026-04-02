import streamlit as st
import pandas as pd
import snowflake.connector
from streamlit_autorefresh import st_autorefresh
from datetime import date

def get_connection():
    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"].get("role", None),
    )

def run_query(query: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        columns = [col[0] for col in cur.description]
        rows = cur.fetchall()
        return columns, rows
    finally:
        conn.close()

st.set_page_config(page_title="Plane Lap Dashboard", page_icon="✈️", layout="wide")

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
}

.stApp {
    background: #0d0f14;
    color: #e0e6f0;
}

.section-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #5c6b80;
    margin-bottom: 0.5rem;
    margin-top: 1rem;
}

.assembly-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #00e5ff;
    margin-bottom: 0.25rem;
    margin-top: 0;
}

.stDataFrame {
    border-radius: 6px;
    overflow: hidden;
}

hr { border-color: #1e2433; margin: 1.25rem 0; }

div[data-testid="stAlert"] {
    background: rgba(92, 107, 128, 0.08);
    border: 1px solid rgba(92, 107, 128, 0.25);
    color: #5c6b80;
    border-radius: 4px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9rem;
    letter-spacing: 0.06em;
}
</style>
""", unsafe_allow_html=True)

def get_current_round() -> str:
    today = date.today()
    if today <= date(2026, 3, 28):
        return "OT_ROUND_1"
    elif today <= date(2026, 4, 4):
        return "OT_ROUND_2"
    elif today <= date(2026, 4, 11):
        return "OT_ROUND_3"
    else:
        return "OT_ROUND_4"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h2 style='text-align:center; font-family:Rajdhani; font-weight:700; "
    "letter-spacing:0.18em; color:#e0e6f0; text-transform:uppercase; "
    "margin-bottom:0;'>✈ Plane Lap Times Dashboard</h2>",
    unsafe_allow_html=True,
)
_round_label = get_current_round().replace("OT_", "").replace("_", " ").title()
st.markdown(
    f"<p style='text-align:center; font-family:Rajdhani; font-size:1.25em; color:#a0aab8; "
    f"margin-top:0.25em; margin-bottom:0;'>{_round_label}</p>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='margin-top:0.5em; margin-bottom:0.25rem;'>", unsafe_allow_html=True)

# Auto-refresh every 60 seconds
st_autorefresh(interval=60_000, key="lap_dashboard_refresh")

ASSEMBLY_LINES = [
    "White Assembly",
    "Black Assembly",
    "Color Assembly",
    "Fuselage Assembly",
    "Wing Assembly",
    "Final Assembly",
]

QUERY_TEMPLATE = """
SELECT
    A.PLANE_ID,
    A.OPERATOR,
    B.ASSEMBLY_LINE,
    A.TIME,
    A.SECONDS,
    A.LOGGED_AT
FROM CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_LAP_TIMES A
LEFT JOIN CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_TEAM_MEMBERS B
    ON A.OPERATOR = B.OPERATOR
WHERE B.ASSEMBLY_LINE = '{assembly_line}'
QUALIFY ROW_NUMBER() OVER (PARTITION BY PLANE_ID, A.OPERATOR, ASSEMBLY_LINE ORDER BY LOGGED_AT DESC) = 1
"""


def fetch_assembly_data(assembly_line: str) -> pd.DataFrame:
    query = QUERY_TEMPLATE.format(assembly_line=assembly_line)
    columns, rows = run_query(query)
    return pd.DataFrame(rows, columns=columns)


PLANE_STATUS_QUERY = """
WITH ALL_LINES AS (
    SELECT COUNT(DISTINCT ASSEMBLY_LINE) AS TOTAL_LINES
    FROM CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_TEAM_MEMBERS
),

PLANE_STATS AS (
    SELECT
        B.PLANE_ID,
        COUNT(DISTINCT A.ASSEMBLY_LINE)  AS LINES_WITH_TIME,
        SUM(B.SECONDS)                   AS TOTAL_BUILD_TIME
    FROM CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_TEAM_MEMBERS A
    INNER JOIN CLASS_PROJECT.OT_PLANE_PROJECT.OT_PLANE_LAP_TIMES B
        ON A.OPERATOR = B.OPERATOR
    WHERE B.PLANE_ID IS NOT NULL
      AND B.TIME    IS NOT NULL
    GROUP BY B.PLANE_ID
)

SELECT
    CAST(RND.PLANE_ID AS INT) AS PLANE_ID,
    RND.MODEL,
    RND.COLOR,
    RND.TIME_DUE,
    CASE
        WHEN PS.LINES_WITH_TIME = AL.TOTAL_LINES THEN 'Complete'
        ELSE 'Incomplete'
    END AS PLANE_STATUS,
    CASE
        WHEN PS.LINES_WITH_TIME = AL.TOTAL_LINES THEN PS.TOTAL_BUILD_TIME
        ELSE NULL
    END AS TOTAL_BUILD_TIME
FROM {round_table} RND
LEFT JOIN PLANE_STATS PS
ON CAST(RND.PLANE_ID AS INT) = PS.PLANE_ID
CROSS JOIN ALL_LINES AL
ORDER BY CAST(RND.PLANE_ID AS INT)
"""

st.markdown("<div class='assembly-title' style='margin-top:-0.75rem;'>Plane Build Status</div>", unsafe_allow_html=True)
try:
    columns, rows = run_query(PLANE_STATUS_QUERY.format(round_table=get_current_round()))
    df_status = pd.DataFrame(rows, columns=columns)
    if df_status.empty:
        st.info("No plane status data found.")
    else:
        def _color_status(val):
            if val == "Complete":
                return "color: #00c853"
            elif val == "Incomplete":
                return "color: #ff3d00"
            return ""

        COLOR_MAP = {
            "Minion":     "color: #ffd600",
            "Sonic":      "color: #1565c0",
            "Wazowski":   "color: #2e7d32",
            "Daffy":      "color: #e65100",
            "Psylocke":   "color: #6a1b9a",
            "Red Baron":  "color: #c62828",
        }

        def _color_plane_color(val):
            return COLOR_MAP.get(val, "")

        styled_status = (
            df_status.style
            .map(_color_status, subset=["PLANE_STATUS"])
            .map(_color_plane_color, subset=["COLOR"])
        )
        st.dataframe(
            styled_status,
            width='stretch',
            hide_index=True,
            column_config={
                "PLANE_ID":        st.column_config.NumberColumn(width="small"),
                "PLANE_STATUS":    st.column_config.TextColumn(width="medium"),
                "TOTAL_BUILD_TIME": st.column_config.NumberColumn(format="%.3f s", width="medium"),
            },
        )
except Exception as e:
    st.error(f"Error loading plane build status: {e}")
st.markdown("<hr>", unsafe_allow_html=True)

for assembly_line in ASSEMBLY_LINES:
    st.markdown(f"<div class='assembly-title'>{assembly_line}</div>", unsafe_allow_html=True)
    try:
        df = fetch_assembly_data(assembly_line)
        if df.empty:
            st.info(f"No data found for {assembly_line}.")
        else:
            st.dataframe(
                df,
                width='stretch',
                hide_index=True,
                column_config={
                    "PLANE_ID":      st.column_config.NumberColumn(width="small"),
                    "OPERATOR":      st.column_config.TextColumn(width="medium"),
                    "ASSEMBLY_LINE": st.column_config.TextColumn(width="medium"),
                    "TIME":          st.column_config.TextColumn(width="medium"),
                    "SECONDS":       st.column_config.NumberColumn(format="%.3f s", width="medium"),
                    "LOGGED_AT":     st.column_config.TextColumn(width="medium"),
                },
            )
    except Exception as e:
        st.error(f"Error loading {assembly_line}: {e}")
    st.markdown("<hr>", unsafe_allow_html=True)
