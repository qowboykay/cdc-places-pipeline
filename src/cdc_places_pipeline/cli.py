from __future__ import annotations

import logging
import os
from pathlib import Path

import click
from dotenv import load_dotenv

from cdc_places_pipeline.extract import iter_dataset
from cdc_places_pipeline.load_duckdb import DEFAULT_DB, load_from_manifest
from cdc_places_pipeline.load_snowflake import load_from_stage
from cdc_places_pipeline.storage import RAW_BASE, save_pages
from cdc_places_pipeline.upload_s3 import upload_manifest

load_dotenv()

# Maps CLI dataset names to Socrata 4x4 dataset IDs.
DATASETS: dict[str, str] = {
    "places_county": "swc5-untb",
}


def _configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


@click.group()
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """CDC PLACES ELT pipeline."""
    _configure_logging(debug)
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@cli.command()
@click.option(
    "--dataset",
    required=True,
    type=click.Choice(list(DATASETS)),
    help="Dataset to extract.",
)
def extract(dataset: str) -> None:
    """Pull a PLACES dataset from the Socrata API and save raw JSON locally."""
    dataset_id = DATASETS[dataset]
    app_token = os.getenv("SOCRATA_APP_TOKEN") or None
    manifest_path = save_pages(dataset_id, iter_dataset(dataset_id, app_token))
    click.echo(f"Manifest: {manifest_path}")


@cli.command()
@click.option(
    "--dataset",
    required=True,
    type=click.Choice(list(DATASETS)),
    help="Dataset to load.",
)
@click.option(
    "--manifest",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    help="Path to manifest.json. Defaults to the most recent extract.",
)
def load(dataset: str, manifest: Path | None) -> None:
    """Load raw JSON pages into DuckDB."""
    dataset_id = DATASETS[dataset]
    db_path = Path(os.getenv("DUCKDB_PATH", str(DEFAULT_DB)))

    if manifest is None:
        dataset_dir = RAW_BASE / dataset_id
        if not dataset_dir.exists():
            raise click.ClickException(
                f"No extracts found for '{dataset}'. Run 'extract' first."
            )
        latest = max(dataset_dir.iterdir(), key=lambda p: p.name)
        manifest = latest / "manifest.json"

    count = load_from_manifest(manifest, db_path)
    click.echo(f"Loaded {count:,} rows into {db_path}")


@cli.command()
@click.option(
    "--dataset",
    required=True,
    type=click.Choice(list(DATASETS)),
    help="Dataset to upload.",
)
@click.option(
    "--manifest",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    help="Path to manifest.json. Defaults to the most recent extract.",
)
def upload(dataset: str, manifest: Path | None) -> None:
    """Upload a local extract to S3."""
    dataset_id = DATASETS[dataset]
    bucket = os.environ["S3_BUCKET_NAME"]

    if manifest is None:
        dataset_dir = RAW_BASE / dataset_id
        if not dataset_dir.exists():
            raise click.ClickException(
                f"No extracts found for '{dataset}'. Run 'extract' first."
            )
        latest = max(dataset_dir.iterdir(), key=lambda p: p.name)
        manifest = latest / "manifest.json"

    stage_path = upload_manifest(manifest, bucket)
    click.echo(f"Stage path: {stage_path}")


@cli.command("snowflake-load")
@click.option(
    "--dataset",
    required=True,
    type=click.Choice(list(DATASETS)),
    help="Dataset to load into Snowflake.",
)
@click.option(
    "--stage-path",
    required=True,
    help="Stage-relative path returned by the 'upload' command.",
)
def snowflake_load(dataset: str, stage_path: str) -> None:
    """COPY INTO Snowflake from the S3 external stage."""
    dataset_id = DATASETS[dataset]
    count = load_from_stage(dataset_id, stage_path)
    click.echo(f"Loaded {count:,} rows into Snowflake")


if __name__ == "__main__":
    cli()
