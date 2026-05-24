from __future__ import annotations

import json
import logging
from pathlib import Path

import boto3

logger = logging.getLogger(__name__)


def upload_manifest(manifest_path: Path, bucket: str, prefix: str = "raw") -> str:
    """Upload all pages for a manifest to S3.

    Files land at s3://<bucket>/<prefix>/<dataset_id>/<timestamp>/.
    Returns the stage-relative path (dataset_id/timestamp) for use
    with the Snowflake external stage whose URL is s3://<bucket>/<prefix>/.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_id: str = manifest["dataset_id"]
    ts: str = manifest["extract_timestamp"]
    s3_dir = f"{prefix}/{dataset_id}/{ts}"

    s3 = boto3.client("s3")
    out_dir = manifest_path.parent

    for page_file in manifest["pages"]:
        s3_key = f"{s3_dir}/{page_file}"
        s3.upload_file(str(out_dir / page_file), bucket, s3_key)
        logger.info("Uploaded s3://%s/%s", bucket, s3_key)

    manifest_key = f"{s3_dir}/manifest.json"
    s3.upload_file(str(manifest_path), bucket, manifest_key)
    logger.info("Uploaded s3://%s/%s", bucket, manifest_key)

    stage_path = f"{dataset_id}/{ts}"
    logger.info("Upload complete. Stage-relative path: %s", stage_path)
    return stage_path
