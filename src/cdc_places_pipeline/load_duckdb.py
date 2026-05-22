from __future__ import annotations

import json
import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

DEFAULT_DB = Path("data") / "warehouse.duckdb"

# Maps Socrata dataset IDs to their target table in DuckDB (schema.table).
_TABLE_FOR_DATASET: dict[str, str] = {
    "swc5-untb": "raw.places_county",
}


def load_from_manifest(
    manifest_path: Path,
    db_path: Path = DEFAULT_DB,
) -> int:
    """Load raw JSON pages described by a manifest into DuckDB.

    Drops and recreates the target table on each run so re-running is safe.
    Returns the number of rows loaded.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_id: str = manifest["dataset_id"]
    page_dir = manifest_path.parent

    table = _TABLE_FOR_DATASET.get(dataset_id)
    if table is None:
        raise ValueError(f"No table mapping for dataset_id={dataset_id!r}")

    # Forward slashes work on all platforms for DuckDB glob patterns.
    glob_pattern = (page_dir / "page_*.json").as_posix()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    try:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"""
            CREATE TABLE {table} AS
            SELECT * FROM read_json(
                '{glob_pattern}',
                format = 'array',
                union_by_name = true,
                auto_detect = true
            )
        """)
        result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        assert result is not None
        count = int(result[0])
        logger.info("Loaded %d rows into %s at %s", count, table, db_path)
        return count
    finally:
        conn.close()
