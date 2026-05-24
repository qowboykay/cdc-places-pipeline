from __future__ import annotations

import logging
import os

import snowflake.connector

logger = logging.getLogger(__name__)

_TABLE_FOR_DATASET: dict[str, str] = {
    "swc5-untb": "CDC_PLACES.RAW.PLACES_COUNTY",
}

_STAGE = "CDC_PLACES.RAW.s3_raw"

_COLUMNS = [
    "year",
    "stateabbr",
    "statedesc",
    "locationname",
    "locationid",
    "datasource",
    "category",
    "categoryid",
    "measure",
    "measureid",
    "short_question_text",
    "data_value_type",
    "datavaluetypeid",
    "data_value_unit",
    "data_value",
    "low_confidence_limit",
    "high_confidence_limit",
    "totalpopulation",
    "totalpop18plus",
    "data_value_footnote_symbol",
    "data_value_footnote",
]


def _connect() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ["SNOWFLAKE_ROLE"],
    )


def load_from_stage(dataset_id: str, stage_path: str) -> int:
    """COPY INTO Snowflake from the S3 external stage.

    stage_path is the dataset_id/timestamp portion relative to the stage URL,
    as returned by upload_s3.upload_manifest().

    The target table is truncated before each load (full-refresh pattern).
    Returns the number of rows in the table after loading.
    """
    table = _TABLE_FOR_DATASET[dataset_id]
    col_list = ", ".join(_COLUMNS)
    src_list = ", ".join(f"$1:{c}::VARCHAR" for c in _COLUMNS)
    stage_ref = f"@{_STAGE}/{stage_path.rstrip('/')}/"

    copy_sql = f"""
        COPY INTO {table} ({col_list})
        FROM (
            SELECT {src_list}
            FROM {stage_ref}
        )
        FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)
        ON_ERROR = 'CONTINUE'
    """

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(f"TRUNCATE TABLE {table}")
        logger.info("Truncated %s", table)
        cur.execute(copy_sql)
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row = cur.fetchone()
        count: int = row[0] if row else 0
        logger.info("Loaded %d rows into %s", count, table)
        return count
    finally:
        conn.close()
