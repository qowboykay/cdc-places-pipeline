# cdc-places-pipeline

ELT pipeline ingesting CDC PLACES public health data via the Socrata API into Snowflake, transformed with dbt, and surfaced through a Streamlit dashboard.

[![CI](https://github.com/qowboykay/cdc-places-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/qowboykay/cdc-places-pipeline/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-Phase%203%20complete-green)

---

## Architecture

> Full diagram coming in Phase 4. Planned data flow:

```
Socrata Open Data API  (data.cdc.gov)
        |
        v
  AWS S3  (raw JSON, partitioned by dataset + extract timestamp)
        |
        v
  Snowflake RAW schema  (COPY INTO via external stage)
        |
        v
  dbt  (STAGING layer -> MARTS layer)
        |
        v
  Streamlit dashboard  (choropleth maps, KPI cards, filterable tables)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Extract | Python, `sodapy`, `requests` |
| Raw storage | AWS S3 (`boto3`) |
| Warehouse | Snowflake (production), DuckDB (local dev) |
| Transform | `dbt-core`, `dbt-snowflake`, `dbt-duckdb` |
| Dashboard | Streamlit, Plotly |
| Testing | `pytest` |
| Linting / formatting | `ruff` |
| Type checking | `mypy` |
| Package manager | `uv` |

---

## Setup

> Full setup instructions coming after Phase 1. Quick start below.

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), AWS credentials, Snowflake account (Phase 4+).

```bash
# Clone and install dependencies
git clone https://github.com/qowboykay/cdc-places-pipeline.git
cd cdc-places-pipeline
uv sync --all-groups

# Copy environment template and fill in values
cp .env.example .env

# Install pre-commit hooks
uv run pre-commit install

# Run the pipeline (local DuckDB, no cloud required)
uv run python -m cdc_places_pipeline.cli extract --dataset places_county
uv run python -m cdc_places_pipeline.cli load --dataset places_county

# Run dbt transformations
uv run dbt build --project-dir dbt --profiles-dir dbt
```

---

## Dashboard

The Streamlit dashboard visualizes age-adjusted prevalence estimates for 40 health measures across 3,100+ US counties.

**Run locally:**

```bash
uv run streamlit run app/dashboard.py
```

Open `http://localhost:8501` in your browser.

**Features:**

- Sidebar filters: year, measure category, and specific measure
- KPI cards: county count, coverage, average and peak prevalence
- Choropleth map with county-level shading
- Top-20 counties bar chart
- Sortable data table with CSV export

![Choropleth map](docs/screenshots/choropleth.png)
![Top 20 bar chart](docs/screenshots/bar_chart.png)
![Data table](docs/screenshots/data_table.png)

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | Repo scaffolding | Done |
| 1 | Local extract + load to DuckDB | Done |
| 2 | dbt transformations (DuckDB target) | Done |
| 3 | Streamlit dashboard (DuckDB-backed) | Done |
| 4 | Promote to AWS + Snowflake | Pending |
| 5 | CI/CD for cloud pipeline | Pending |
| 6 | Performance tuning and monitoring | Pending |
| 7 | Polish, docs, tagged release | Pending |

---

## Related Project

[cdc-places-nl-sql](https://github.com/qowboykay/cdc-places-nl-sql): Natural-language SQL assistant built on top of the Snowflake schema produced by this pipeline.
