from __future__ import annotations

import json
import logging
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RAW_BASE = Path("data") / "raw"


def save_pages(
    dataset_id: str,
    pages: Generator[list[dict[str, Any]], None, None],
    base_dir: Path = RAW_BASE,
) -> Path:
    """Write raw pages to disk and return the path to the manifest file.

    Directory layout:
        <base_dir>/<dataset_id>/<timestamp>/page_NNNN.json
        <base_dir>/<dataset_id>/<timestamp>/manifest.json
    """
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = base_dir / dataset_id / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    page_files: list[str] = []
    total_records = 0

    for i, page in enumerate(pages):
        page_path = out_dir / f"page_{i:04d}.json"
        page_path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
        page_files.append(page_path.name)
        total_records += len(page)
        logger.debug("Wrote %s (%d records)", page_path.name, len(page))

    manifest: dict[str, Any] = {
        "dataset_id": dataset_id,
        "extract_timestamp": ts,
        "total_records": total_records,
        "pages": page_files,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(
        "Saved %d records across %d pages to %s",
        total_records,
        len(page_files),
        out_dir,
    )
    return manifest_path
