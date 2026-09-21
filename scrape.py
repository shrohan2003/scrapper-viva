"""Extract EVENTIM event, ticket, and seating-map data from saved HTML."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup


def extract_event_id(url):
    """Get the numeric event ID from the URL."""
    match = re.search(r"-(\d{7,})/?$", urlparse(url).path)
    return match.group(1) if match else None


def find_event_json(value):
    """Find an Event object inside possibly nested JSON-LD."""
    if isinstance(value, dict):
        event_type = value.get("@type")
        if event_type == "Event" or (
            isinstance(event_type, list) and "Event" in event_type
        ):
            return value

        for child in value.values():
            found = find_event_json(child)
            if found:
                return found

    elif isinstance(value, list):
        for child in value:
            found = find_event_json(child)
            if found:
                return found

    return None


def read_event_json(soup):
    """Read structured Event data when the page provides it."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue

        event = find_event_json(data)
        if event:
            return event

    return {}


def read_configuration(soup):
    """Find EVENTIM's embedded price and seating-map configuration."""
    for script in soup.find_all("script", type="application/configuration"):
        try:
            data = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue

        if isinstance(data, dict) and "price" in data:
            return data

    return {}


def embedded_value(html, key):
    """Read a simple quoted value from embedded page data."""
    pattern = rf'"{re.escape(key)}"\s*:\s*"([^"]+)"'
    match = re.search(pattern, html)
    return match.group(1).strip() if match else None


def extract_country(soup):
    """Read the venue's country code from its map link."""
    link = soup.select_one(".venue-address a.js-maps-link[href]")
    if not link:
        return None

    query = parse_qs(urlparse(link.get("href", "")).query)
    address = query.get("query", [""])[0]

    # Example map address ends in ", DE".
    match = re.search(r",\s*([A-Z]{2})\s*$", address)
    return match.group(1) if match else None


def parse_price(value):
    """Convert a price such as '1.234,56 €' into 1234.56 EUR."""
    if value is None:
        return None, None

    text = str(value).replace("\u00a0", " ").strip()
    currency = "EUR" if "€" in text else None

    match = re.search(r"\d[\d.,\s]*", text)
    if not match:
        return None, currency

    number = match.group().replace(" ", "").strip(".,")

    if "," in number and "." in number:
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        number = number.replace(".", "").replace(",", ".")

    try:
        return float(number), currency
    except ValueError:
        return None, currency


def normalize_availability(value):
    """Standardize German/English availability text."""
    if value is None:
        return None

    text = str(value).strip().lower()

    # Negative phrases must be checked before "verfügbar".
    if any(
        word in text
        for word in ("nicht verfügbar", "ausverkauft", "sold out", "unavailable")
    ):
        return "unavailable"

    if any(
        word in text
        for word in ("verfügbar", "available", "in stock")
    ):
        return "available"

    return None


def extract_categories(config):
    """Read ticket price categories from EVENTIM's configuration."""
    price_map = config.get("price", {})
    if not isinstance(price_map, dict):
        return []

    numbered_categories = []

    for item in price_map.values():
        if not isinstance(item, dict):
            continue

        price, currency = parse_price(item.get("defaultFormattedPrice"))

        if price is None and isinstance(item.get("defaultPriceAsInt"), (int, float)):
            price = item["defaultPriceAsInt"] / 1000

        availability = None
        ticket_types = item.get("ticketTypes") or []

        for ticket_type in ticket_types:
            if not isinstance(ticket_type, dict):
                continue

            availability = normalize_availability(ticket_type.get("statusText"))
            if availability is not None:
                break

        category = {
            "id": (
                str(item["priceCategoryId"])
                if item.get("priceCategoryId")
                else None
            ),
            "name": item.get("title"),
            "price": price,
            "currency": currency or "EUR",
            "availability": availability,
        }

        # Keep the same category order shown by EVENTIM.
        try:
            order = int(item.get("number"))
        except (TypeError, ValueError):
            order = 10000

        numbered_categories.append((order, category))

    numbered_categories.sort(key=lambda pair: pair[0])
    return [category for _, category in numbered_categories]


def extract_color_legend(soup, categories):
    """Match seating-map colours with ticket categories."""
    names_by_id = {
        category["id"]: category["name"]
        for category in categories
        if category["id"]
    }
    legend = {}

    for item in soup.select("li.js-dd-pc-item[data-key]"):
        category_id = item.get("data-key")
        square = item.select_one(".js-dd-square, .category-square")
        style = square.get("style", "") if square else ""

        match = re.search(
            r"background-color\s*:\s*(#[0-9a-fA-F]{3,8})",
            style,
        )
        if match:
            legend[match.group(1).lower()] = {
                "id": category_id,
                "name": (
                    item.get("data-tracking-label")
                    or names_by_id.get(category_id)
                ),
            }

    return legend


def extract_blocks(soup, legend):
    """Read block IDs and availability from the rendered SVG map."""
    blocks = []
    seen_ids = set()
    grey_colors = {
        "#ebebeb",
        "#e5e5e5",
        "#eeeeee",
        "#ddd",
        "#dddddd",
        "#dcdcdc",
    }

    for path in soup.select('g.block-outlines path.bo[id^="bo"]'):
        # EVENTIM uses IDs like "bo53"; the result stores "53".
        block_id = path.get("id", "")[2:]
        if not block_id or block_id in seen_ids:
            continue
        seen_ids.add(block_id)

        color = str(path.get("fill") or "").strip().lower()
        classes = {str(name).lower() for name in path.get("class", [])}
        category = legend.get(color)

        if color in grey_colors:
            available = False
        elif "has-hover" in classes or category is not None:
            available = True
        else:
            available = None  # Unknown is safer than guessing.

        blocks.append({
            "id": block_id,
            "available": available,
            "label": (
                path.get("aria-label")
                or path.get("data-label")
                or path.get("title")
            ),
            "category": category["name"] if category else None,
            "price_category_id": category["id"] if category else None,
        })

    # Sort numeric block IDs so the JSON is easy to inspect.
    blocks.sort(key=lambda block: int(block["id"]) if block["id"].isdigit() else 10**9)
    return blocks


def parse_event(html, url):
    """Combine information from all sources in the captured page."""
    soup = BeautifulSoup(html, "html.parser")
    event = read_event_json(soup)
    config = read_configuration(soup)

    location = event.get("location") or {}
    if not isinstance(location, dict):
        location = {}

    address = location.get("address") or {}
    if not isinstance(address, dict):
        address = {}

    # The live page may omit Event JSON-LD, so use its other embedded data.
    heading = soup.select_one("h1")
    heading_title = heading.get_text(" ", strip=True) if heading else None

    title = (
        event.get("name")
        or config.get("eventName")
        or heading_title
    )
    start_datetime = (
        event.get("startDate")
        or embedded_value(html, "event_date")
    )
    venue_name = (
        location.get("name")
        or embedded_value(html, "venue_name")
    )
    city = (
        address.get("addressLocality")
        or embedded_value(html, "event_city_name")
    )
    country = (
        address.get("addressCountry")
        or extract_country(soup)
    )

    categories = extract_categories(config)
    legend = extract_color_legend(soup, categories)
    blocks = extract_blocks(soup, legend)

    seatmap_options = config.get("seatmapOptions") or {}
    seatmap_present = bool(blocks or seatmap_options)

    warnings = []
    if not title:
        warnings.append("Event title was not found.")
    if not start_datetime:
        warnings.append("Event date/time was not found.")
    if not venue_name:
        warnings.append("Venue name was not found.")
    if not city:
        warnings.append("Venue city was not found.")
    if not country:
        warnings.append("Venue country was not found.")
    if not categories:
        warnings.append("Ticket categories were not found.")
    if seatmap_present and not blocks:
        warnings.append("Seating map exists, but rendered blocks were not found.")

    return {
        "event_id": extract_event_id(url),
        "title": title,
        "start_datetime": start_datetime,
        "venue": {
            "name": venue_name,
            "city": city,
            "country": country,
        },
        "ticket_categories": categories,
        "seating_map": {
            "present": seatmap_present,
            "blocks": blocks,
        },
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "warnings": warnings,
    }


def main():
    """Parse a saved HTML file and write the extracted JSON."""
    parser = argparse.ArgumentParser(description="Parse a saved EVENTIM page")
    parser.add_argument("--url", required=True, help="EVENTIM event URL")
    parser.add_argument("--html", required=True, help="Saved HTML file")
    parser.add_argument("--output", default="result.json", help="Output JSON file")
    args = parser.parse_args()

    html = Path(args.html).read_text(encoding="utf-8")
    result = parse_event(html, args.url)

    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Saved:", args.output)
    print("Event:", result["event_id"], result["title"])
    print("Date/time:", result["start_datetime"])
    print("Venue:", result["venue"])
    print("Ticket categories:", len(result["ticket_categories"]))
    print("Seating blocks:", len(result["seating_map"]["blocks"]))
    print("Warnings:", result["warnings"])


if __name__ == "__main__":
    main()