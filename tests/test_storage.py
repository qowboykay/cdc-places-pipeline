from __future__ import annotations

import json
from pathlib import Path

from cdc_places_pipeline.storage import save_pages


def _make_pages(
    *batches: list[dict[str, str]],
) -> list[list[dict[str, str]]]:
    return list(batches)


def test_save_pages_creates_page_files(tmp_path: Path) -> None:
    pages = _make_pages(
        [{"locationid": "01001"}, {"locationid": "01003"}],
        [{"locationid": "01005"}],
    )
    manifest_path = save_pages("swc5-untb", iter(pages), base_dir=tmp_path)

    assert manifest_path.exists()
    parent = manifest_path.parent
    assert (parent / "page_0000.json").exists()
    assert (parent / "page_0001.json").exists()


def test_manifest_contains_correct_metadata(tmp_path: Path) -> None:
    pages = _make_pages([{"a": "1"}, {"a": "2"}], [{"a": "3"}])
    manifest_path = save_pages("swc5-untb", iter(pages), base_dir=tmp_path)

    manifest = json.loads(manifest_path.read_text())
    assert manifest["dataset_id"] == "swc5-untb"
    assert manifest["total_records"] == 3
    assert manifest["pages"] == ["page_0000.json", "page_0001.json"]


def test_page_files_contain_valid_json(tmp_path: Path) -> None:
    records = [{"locationid": "01001", "measure": "Arthritis"}]
    manifest_path = save_pages("swc5-untb", iter([records]), base_dir=tmp_path)

    page_file = manifest_path.parent / "page_0000.json"
    loaded = json.loads(page_file.read_text())
    assert loaded == records


def test_empty_dataset_writes_manifest_with_zero_records(tmp_path: Path) -> None:
    manifest_path = save_pages("swc5-untb", iter([]), base_dir=tmp_path)

    manifest = json.loads(manifest_path.read_text())
    assert manifest["total_records"] == 0
    assert manifest["pages"] == []
