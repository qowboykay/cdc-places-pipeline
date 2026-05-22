from __future__ import annotations

import os

import pytest

from cdc_places_pipeline.extract import iter_dataset

COUNTY_DATASET_ID = "swc5-untb"


@pytest.mark.integration
def test_county_extract_returns_records() -> None:
    """Fetch one small page from the live Socrata API and verify records exist."""
    app_token = os.getenv("SOCRATA_APP_TOKEN") or None
    pages = list(iter_dataset(COUNTY_DATASET_ID, app_token=app_token, page_size=100))

    assert len(pages) >= 1, "Expected at least one page of results"
    assert len(pages[0]) > 0, "Expected records in the first page"

    first = pages[0][0]
    assert "locationid" in first, "Expected 'locationid' field in records"
    assert "measure" in first, "Expected 'measure' field in records"
