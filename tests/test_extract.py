from __future__ import annotations

from unittest.mock import MagicMock, patch

from cdc_places_pipeline.extract import iter_dataset


def _make_client(
    mock_cls: MagicMock, side_effect: list[list[dict[str, str]]]
) -> MagicMock:
    client = MagicMock()
    mock_cls.return_value = client
    client.get.side_effect = side_effect
    client.close.return_value = None
    return client


def test_single_partial_page_stops_after_one_call() -> None:
    """A page smaller than page_size signals end of dataset; no second fetch."""
    records = [{"locationid": "01001", "measure": "Arthritis"}]
    with patch("cdc_places_pipeline.extract.Socrata") as mock_cls:
        _make_client(mock_cls, [records])
        pages = list(iter_dataset("swc5-untb", page_size=1_000))

    assert pages == [records]
    mock_cls.return_value.get.assert_called_once()


def test_full_page_followed_by_empty_paginates_correctly() -> None:
    """A full page triggers a second fetch; an empty second page stops iteration."""
    page1 = [{"locationid": str(i)} for i in range(3)]
    with patch("cdc_places_pipeline.extract.Socrata") as mock_cls:
        _make_client(mock_cls, [page1, []])
        pages = list(iter_dataset("swc5-untb", page_size=3))

    assert pages == [page1]
    assert mock_cls.return_value.get.call_count == 2


def test_two_full_pages_then_partial() -> None:
    """Two full pages followed by a partial page yields all three pages."""
    page1 = [{"r": "a"}, {"r": "b"}]
    page2 = [{"r": "c"}, {"r": "d"}]
    page3 = [{"r": "e"}]
    with patch("cdc_places_pipeline.extract.Socrata") as mock_cls:
        _make_client(mock_cls, [page1, page2, page3])
        pages = list(iter_dataset("swc5-untb", page_size=2))

    assert pages == [page1, page2, page3]


def test_close_called_even_on_exception() -> None:
    """The Socrata client is always closed, even if iteration raises."""
    with patch("cdc_places_pipeline.extract.Socrata") as mock_cls:
        client = MagicMock()
        mock_cls.return_value = client
        client.get.side_effect = RuntimeError("network error")
        client.close.return_value = None

        try:
            list(iter_dataset("swc5-untb"))
        except RuntimeError:
            pass

    client.close.assert_called_once()
