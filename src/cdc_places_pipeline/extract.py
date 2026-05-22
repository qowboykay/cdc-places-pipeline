from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from sodapy import Socrata

logger = logging.getLogger(__name__)

SOCRATA_DOMAIN = "data.cdc.gov"
DEFAULT_PAGE_SIZE = 1_000


def iter_dataset(
    dataset_id: str,
    app_token: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Generator[list[dict[str, Any]], None, None]:
    """Yield pages of records from a Socrata dataset.

    Paginates until the API returns an empty page or a partial page,
    which signals the end of the dataset.
    """
    client = Socrata(SOCRATA_DOMAIN, app_token, timeout=60)
    offset = 0
    total = 0
    try:
        while True:
            logger.debug(
                "Fetching dataset=%s offset=%d limit=%d", dataset_id, offset, page_size
            )
            page: list[dict[str, Any]] = client.get(
                dataset_id, limit=page_size, offset=offset
            )
            if not page:
                break
            yield page
            total += len(page)
            logger.info("Fetched %d records (running total: %d)", len(page), total)
            if len(page) < page_size:
                break
            offset += page_size
    finally:
        client.close()
