"""Saved HTML regression tests. No live site or optional fixture is needed."""

from datetime import datetime
import json
from pathlib import Path

import pytest

from event_parser import normalize_availability, normalize_datetime, parse_event, parse_price

FIXTURES = Path(__file__).parent / "fixtures"
EVENT_URL = "https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/"


def parsed(name):
    return parse_event((FIXTURES / name).read_text(encoding="utf-8"), EVENT_URL)


def test_real_holiday_snapshot():
    result = parsed("holiday_on_ice.html")
    timestamp = datetime.fromisoformat(result.pop("scraped_at"))
    assert timestamp.utcoffset().total_seconds() == 0
    expected = json.loads((FIXTURES / "holiday_on_ice.expected.json").read_text(encoding="utf-8"))
    assert result == expected
    assert result["start_datetime"] == "2026-11-27T19:30:00+01:00"
    assert [c["price"] for c in result["ticket_categories"]] == [98, 84, 73, 62, 46]
    blocks = result["seating_map"]["blocks"]
    assert len(blocks) == 94
    assert sum(b["available"] is True for b in blocks) == 37
    assert sum(b["available"] is False for b in blocks) == 57
    assert result["warnings"] == []


def test_saved_german_prices_and_category_availability():
    categories = parsed("edge_cases.html")["ticket_categories"]
    assert categories[0]["price"] == 1234.56
    assert categories[0]["currency"] == "EUR"
    assert [c["availability"] for c in categories] == [
        "available", "unavailable", None, "available", None, "unavailable",
    ]
    assert categories[2]["price"] == 0
    assert categories[4]["price"] == 73


def test_saved_linked_map_and_unknown_state():
    result = parsed("edge_cases.html")
    blocks = {b["id"]: b for b in result["seating_map"]["blocks"]}
    assert set(blocks) == {"134217740", "134218319", "315", "999"}
    assert blocks["134217740"]["available"] is True
    assert blocks["134217740"]["label"] == "Block A"
    assert blocks["134218319"]["available"] is False  # Grey overrides has-hover.
    assert blocks["315"]["label"] == "Stehplatz Block H hinten"
    assert blocks["999"]["available"] is None
    assert any("blocks[999].available" in warning for warning in result["warnings"])


def test_missing_fields_are_null_with_specific_warnings():
    result = parsed("missing_fields.html")
    assert result["start_datetime"] is None  # No invented timezone.
    assert result["venue"] == {"name": None, "city": None, "country": None}
    assert result["seating_map"] == {"present": True, "blocks": None}
    assert result["ticket_categories"][0]["price"] is None
    for field in ("start_datetime", "venue.name", "venue.city", "venue.country",
                  "ticket_categories[1].price", "ticket_categories[1].currency",
                  "ticket_categories[1].availability", "seating_map.blocks"):
        assert any(w.startswith(field + ":") for w in result["warnings"])


def test_malformed_page_does_not_crash_or_guess():
    result = parsed("malformed.html")
    assert result["title"] == "Fallback title"
    assert result["ticket_categories"][0]["name"] is None
    assert result["ticket_categories"][1]["price"] is None
    assert result["seating_map"]["blocks"][0]["id"] is None
    assert result["seating_map"]["blocks"][0]["available"] is None
    assert any("malformed JSON" in w for w in result["warnings"])
    assert any("ticketTypes: malformed" in w for w in result["warnings"])
    json.dumps(result, allow_nan=False)


def test_map_absent_is_distinct_from_not_loaded():
    result = parsed("no_map.html")
    assert result["seating_map"] == {"present": False, "blocks": []}
    assert result["warnings"] == []
    empty = parse_event("", EVENT_URL)
    assert empty["ticket_categories"] is None
    assert empty["seating_map"] == {"present": None, "blocks": None}
    assert empty["warnings"]


def test_map_evidence_is_kept_when_event_metadata_is_missing():
    fixture = (FIXTURES / "malformed.html").read_text(encoding="utf-8")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(fixture, "html.parser")
    result = parse_event(str(soup.svg), EVENT_URL)
    assert result["title"] is None
    assert result["seating_map"]["present"] is True
    assert len(result["seating_map"]["blocks"]) == 1


@pytest.mark.parametrize("value, expected", [
    ("1.234,56 €", (1234.56, "EUR")), ("1.234 €", (1234.0, "EUR")),
    ("98,00 EUR", (98.0, "EUR")), ("1\u202f234,56 €", (1234.56, "EUR")),
    ("0,00 €", (0.0, "EUR")), ("98.50", (98.5, None)),
    (None, (None, None)), ({}, (None, None)), (True, (None, None)),
    ("-5,00 €", (None, "EUR")), ("unknown", (None, None)),
])
def test_price_normalization(value, expected):
    assert parse_price(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("nicht verfügbar", "unavailable"), ("currently unavailable", "unavailable"),
    ("verfügbar", "available"), ("mystery", None), ({}, None),
])
def test_availability_phrases(value, expected):
    assert normalize_availability(value) == expected


@pytest.mark.parametrize("value", [None, {}, "tomorrow", "2026-11-27", "2026-11-27T19:30:00"])
def test_datetime_requires_valid_timezone(value):
    assert normalize_datetime(value) is None
