from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from cdc_places_pipeline.load_duckdb import load_from_manifest

SAMPLE_RECORDS = [
    {
        "year": "2023",
        "stateabbr": "AL",
        "locationname": "Autauga County",
        "locationid": "01001",
        "measure": "Arthritis among adults",
        "data_value": "32.1",
    },
    {
        "year": "2023",
        "stateabbr": "AL",
        "locationname": "Baldwin County",
        "locationid": "01003",
        "measure": "Arthritis among adults",
        "data_value": "29.8",
    },
]


def _write_extract(base: Path, records: list[dict[str, str]]) -> Path:
    """Write a minimal single-page extract and return the manifest path."""
    page_dir = base / "swc5-untb" / "20240101T000000Z"
    page_dir.mkdir(parents=True)
    (page_dir / "page_0000.json").write_text(json.dumps(records), encoding="utf-8")
    manifest = {
        "dataset_id": "swc5-untb",
        "extract_timestamp": "20240101T000000Z",
        "total_records": len(records),
        "pages": ["page_0000.json"],
    }
    manifest_path = page_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_load_inserts_correct_row_count(tmp_path: Path) -> None:
    manifest_path = _write_extract(tmp_path / "raw", SAMPLE_RECORDS)
    db_path = tmp_path / "test.duckdb"

    count = load_from_manifest(manifest_path, db_path)

    assert count == len(SAMPLE_RECORDS)


def test_load_creates_raw_schema_and_table(tmp_path: Path) -> None:
    manifest_path = _write_extract(tmp_path / "raw", SAMPLE_RECORDS)
    db_path = tmp_path / "test.duckdb"

    load_from_manifest(manifest_path, db_path)

    conn = duckdb.connect(str(db_path))
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw'"
    ).fetchall()
    conn.close()
    assert ("places_county",) in rows


def test_load_is_idempotent(tmp_path: Path) -> None:
    """Running load twice replaces the table rather than appending."""
    manifest_path = _write_extract(tmp_path / "raw", SAMPLE_RECORDS)
    db_path = tmp_path / "test.duckdb"

    load_from_manifest(manifest_path, db_path)
    count = load_from_manifest(manifest_path, db_path)

    assert count == len(SAMPLE_RECORDS)


def test_unknown_dataset_raises(tmp_path: Path) -> None:
    page_dir = tmp_path / "unknown-id" / "20240101T000000Z"
    page_dir.mkdir(parents=True)
    manifest = {"dataset_id": "unknown-id", "total_records": 0, "pages": []}
    manifest_path = page_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="No table mapping"):
        load_from_manifest(manifest_path, tmp_path / "test.duckdb")
