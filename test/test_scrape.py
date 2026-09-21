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


def test_linked_area_map():
    """Read linked areas without counting decorative background shapes."""
    html = TEST_HTML.replace(
        '<g class="block-outlines">',
        '<g class="unused-background">',
    ).replace("</svg>", """
      <g class="linked-blocks">
        <g class="block">
          <path id="134217740" class="lb has-hover" fill="#fa6dd5"/>
          <text>Block A</text>
        </g>
        <g class="block">
          <path id="134218319" class="lb has-hover" fill="#ebebeb"/>
          <text>Front of Stage</text>
        </g>
        <g class="block">
          <path id="315" class="lb has-hover" fill="#b99297"/>
          <text>Stehplatz</text><text>Block H hinten</text>
          <title>Info Feld</title>
        </g>
        <g class="block">
          <path id="999" class="lb" fill="#123456"/>
        </g>
      </g>
    </svg>""")
    result = parse_event(html, EVENT_URL)
    blocks = {block["id"]: block for block in result["seating_map"]["blocks"]}
    assert set(blocks) == {"134217740", "134218319", "315", "999"}
    assert blocks["134217740"]["available"] is True
    assert blocks["134217740"]["label"] == "Block A"
    assert blocks["134218319"]["available"] is False
    assert blocks["315"]["label"] == "Stehplatz Block H hinten"
    assert blocks["999"]["available"] is None


@pytest.mark.parametrize(
    "form, expected",
    [
        ('<form name="pk101"><div class="ticket-type-wrapper '
         'ticket-type-item-wrapper-unavailable">zurzeit nicht verfügbar'
         '</div></form>', "unavailable"),
        ('<form name="pk999"><div class="ticket-type-wrapper '
         'ticket-type-item-wrapper-unavailable"></div></form>', None),
        ('<form name="pk101"><div class="ticket-type-wrapper '
         'ticket-type-item-wrapper-unavailable"></div>'
         '<div class="ticket-type-wrapper"></div></form>', None),
        ("", None),
    ],
)
def test_category_without_ticket_types_uses_its_own_status(form, expected):
    html = TEST_HTML.replace(
        '[{"statusText": "verfügbar"}]', "[]"
    ).replace("</body>", form + "</body>")
    result = parse_event(html, EVENT_URL)
    assert result["ticket_categories"][0]["availability"] == expected
