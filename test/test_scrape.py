"""Tests for the EVENTIM HTML parser."""

from pathlib import Path

import pytest

from scrape import normalize_availability, parse_event, parse_price


EVENT_URL = (
    "https://www.eventim.de/event/"
    "holiday-on-ice-mirage-merkur-ostseehalle-20995028/"
)

# Small, self-contained HTML: safe to keep in Git later.
TEST_HTML = """
<html>
<head>
  <script type="application/ld+json">
  {
    "@type": "Event",
    "name": "Test Event",
    "startDate": "2026-11-27T19:30:00+01:00",
    "location": {
      "name": "Test Venue",
      "address": {
        "addressLocality": "Kiel",
        "addressCountry": "DE"
      }
    }
  }
  </script>
  <script type="application/configuration">
  {
    "price": {
      "first": {
        "priceCategoryId": "101",
        "number": 1,
        "title": "Category 1",
        "defaultFormattedPrice": "1.234,56 €",
        "ticketTypes": [{"statusText": "verfügbar"}]
      }
    },
    "seatmapOptions": {"evId": "20995028"}
  }
  </script>
</head>
<body>
  <li class="js-dd-pc-item" data-key="101" data-tracking-label="Category 1">
    <span class="js-dd-square" style="background-color: #ff0000"></span>
  </li>
  <svg>
    <g class="block-outlines">
      <path class="bo has-hover" id="bo10" fill="#ff0000"></path>
      <path class="bo" id="bo11" fill="#ebebeb"></path>
    </g>
  </svg>
</body>
</html>
"""


def test_price_conversion():
    """German price text becomes a numeric price and currency."""
    assert parse_price("1.234,56 €") == (1234.56, "EUR")


def test_unavailable_is_not_mistaken_for_available():
    """The negative phrase must be checked first."""
    assert normalize_availability("nicht verfügbar") == "unavailable"


def test_event_and_seating_map():
    """The parser combines JSON-LD, ticket configuration, and SVG."""
    result = parse_event(TEST_HTML, EVENT_URL)

    assert result["event_id"] == "20995028"
    assert result["title"] == "Test Event"
    assert result["venue"]["country"] == "DE"
    assert result["ticket_categories"][0]["price"] == 1234.56
    assert result["seating_map"]["blocks"][0]["id"] == "10"
    assert result["seating_map"]["blocks"][0]["available"] is True
    assert result["seating_map"]["blocks"][1]["available"] is False
    assert result["warnings"] == []


def test_fresh_capture_if_available():
    """Check the current real capture locally; skip if it is absent."""
    capture = Path("eventim_real_capture.html")
    if not capture.exists():
        pytest.skip("Local live capture is not available")

    result = parse_event(capture.read_text(encoding="utf-8"), EVENT_URL)

    assert result["title"] == "Holiday on Ice - MIRAGE"
    assert len(result["ticket_categories"]) == 5
    assert len(result["seating_map"]["blocks"]) == 94
    assert result["warnings"] == []