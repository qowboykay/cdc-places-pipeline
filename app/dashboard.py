"""CDC PLACES county health dashboard backed by DuckDB (Phase 4: Snowflake)."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import urlopen

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Measure catalog: category -> {display label -> Socrata measureid}
# ---------------------------------------------------------------------------

MEASURES: dict[str, dict[str, str]] = {
    "Health Outcomes": {
        "Arthritis": "ARTHRITIS",
        "High Blood Pressure": "BPHIGH",
        "Cancer (non-skin / melanoma)": "CANCER",
        "Current Asthma": "CASTHMA",
        "Coronary Heart Disease": "CHD",
        "COPD": "COPD",
        "Depression": "DEPRESSION",
        "Diabetes": "DIABETES",
        "High Cholesterol": "HIGHCHOL",
        "Obesity": "OBESITY",
        "Stroke": "STROKE",
        "All Teeth Lost": "TEETHLOST",
    },
    "Health Risk Behaviors": {
        "Binge Drinking": "BINGE",
        "Current Cigarette Smoking": "CSMOKING",
        "Physical Inactivity": "LPA",
        "Short Sleep Duration": "SLEEP",
    },
    "Health Status": {
        "Poor General Health": "GHLTH",
        "Frequent Mental Distress": "MHLTH",
        "Frequent Physical Distress": "PHLTH",
    },
    "Disability": {
        "Any Disability": "DISABILITY",
        "Cognitive Disability": "COGNITION",
        "Hearing Disability": "HEARING",
        "Independent Living Disability": "INDEPLIVE",
        "Mobility Disability": "MOBILITY",
        "Self-care Disability": "SELFCARE",
        "Vision Disability": "VISION",
    },
    "Health-Related Social Needs": {
        "Lack of Social / Emotional Support": "EMOTIONSPT",
        "Food Insecurity": "FOODINSECU",
        "Food Stamps": "FOODSTAMP",
        "Housing Insecurity": "HOUSINSECU",
        "Transportation Barriers": "LACKTRPT",
        "Loneliness": "LONELINESS",
        "Utility Services Threat": "SHUTUTILITY",
    },
    "Prevention": {
        "No Health Insurance": "ACCESS2",
        "High BP Medication": "BPMED",
        "Annual Checkup": "CHECKUP",
        "Cholesterol Screening": "CHOLSCREEN",
        "Colorectal Cancer Screening": "COLON_SCREEN",
        "Dental Visit": "DENTAL",
        "Mammography Use": "MAMMOUSE",
    },
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _db_path() -> str:
    return os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")


@st.cache_data(ttl=3600)
def load_years() -> list[int]:
    with duckdb.connect(_db_path(), read_only=True) as conn:
        rows = conn.execute(
            "SELECT DISTINCT year"
            " FROM main_intermediate.int_places_measures"
            " ORDER BY year DESC"
        ).fetchall()
        return [int(r[0]) for r in rows]


@st.cache_data(ttl=3600)
def load_measure_data(year: int, measureid: str) -> pd.DataFrame:
    """Return one row per county for the selected year and measure."""
    with duckdb.connect(_db_path(), read_only=True) as conn:
        return conn.execute(
            """
            SELECT
                locationid,
                locationname,
                stateabbr,
                statedesc,
                totalpopulation,
                data_value
            FROM main_intermediate.int_places_measures
            WHERE year = ? AND measureid = ?
            ORDER BY data_value DESC NULLS LAST
            """,
            [year, measureid],
        ).df()


@st.cache_data(show_spinner="Loading county boundaries...")
def load_county_geojson() -> dict[str, Any]:
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    with urlopen(url) as resp:
        return json.load(resp)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="CDC PLACES County Health",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("CDC PLACES County Health Dashboard")
st.caption(
    "Age-adjusted prevalence estimates for 40 health measures"
    " across 3,100+ US counties. Source: CDC PLACES 2025 release (data.cdc.gov)."
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Filters")

    years = load_years()
    selected_year: int = st.selectbox("Year", years)

    selected_category: str = st.selectbox("Category", list(MEASURES.keys()))

    measure_map = MEASURES[selected_category]
    selected_label: str = st.selectbox("Measure", list(measure_map.keys()))
    selected_measureid = measure_map[selected_label]

    st.divider()
    st.caption("CDC PLACES 2025 release")
    st.caption("data.cdc.gov")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

df = load_measure_data(selected_year, selected_measureid)
valid = df.dropna(subset=["data_value"])

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)
c1.metric("Counties", f"{len(df):,}")
c2.metric("With Data", f"{len(valid):,}")
c3.metric(
    "Avg Prevalence",
    f"{valid['data_value'].mean():.1f}%" if len(valid) > 0 else "N/A",
)
c4.metric(
    "Highest County",
    f"{valid['data_value'].max():.1f}%" if len(valid) > 0 else "N/A",
)

st.divider()

# ---------------------------------------------------------------------------
# Choropleth map
# ---------------------------------------------------------------------------

st.subheader(f"{selected_label} by County ({selected_year})")

counties_geo = load_county_geojson()

p05 = float(valid["data_value"].quantile(0.05))
p95 = float(valid["data_value"].quantile(0.95))

fig_map = px.choropleth(
    valid,
    geojson=counties_geo,
    locations="locationid",
    color="data_value",
    color_continuous_scale="YlOrRd",
    range_color=(p05, p95),
    scope="usa",
    hover_name="locationname",
    hover_data={
        "stateabbr": True,
        "data_value": ":.1f",
        "totalpopulation": ":,",
        "locationid": False,
    },
    labels={
        "data_value": "Prevalence (%)",
        "stateabbr": "State",
        "totalpopulation": "Population",
    },
)
fig_map.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    coloraxis_colorbar={"title": "Prevalence (%)"},
)
st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------------------------------
# Top 20 bar chart
# ---------------------------------------------------------------------------

st.subheader(f"Top 20 Counties -- {selected_label} ({selected_year})")

top20 = valid.head(20).copy()
top20["county_label"] = top20["locationname"] + ", " + top20["stateabbr"]

fig_bar = px.bar(
    top20,
    x="data_value",
    y="county_label",
    orientation="h",
    color="data_value",
    color_continuous_scale="YlOrRd",
    text_auto=".1f",
    labels={"data_value": "Prevalence (%)", "county_label": ""},
)
fig_bar.update_layout(
    yaxis={"categoryorder": "total ascending"},
    coloraxis_showscale=False,
    margin={"l": 220},
)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Data table + CSV download
# ---------------------------------------------------------------------------

st.subheader("County Data")

display_df = df.rename(
    columns={
        "locationid": "FIPS",
        "locationname": "County",
        "stateabbr": "State",
        "statedesc": "State Name",
        "totalpopulation": "Population",
        "data_value": "Prevalence (%)",
    }
)

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.download_button(
    label="Download CSV",
    data=display_df.to_csv(index=False),
    file_name=f"cdc_places_{selected_measureid}_{selected_year}.csv",
    mime="text/csv",
)
