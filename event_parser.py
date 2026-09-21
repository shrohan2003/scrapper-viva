"""Pure EVENTIM HTML parsing: no browser, network, or filesystem access."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import math
import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

# Keep site-specific selectors together so page changes are easy to review.
SELECTORS = {
    "configuration": 'script[type="application/configuration"]',
    "json_ld": 'script[type="application/ld+json"]',
    "blocks": "g.block-outlines path.bo, g.linked-blocks path.lb",
    "legend": "li.js-dd-pc-item[data-key]",
    "legend_swatch": ".js-dd-square, .category-square",
    "venue_map": ".venue-address a.js-maps-link[href]",
    "unavailable_rows": ".ticket-type-wrapper",
}
GREY_COLORS = {"#ebebeb", "#e5e5e5", "#eeeeee", "#ddd", "#dddddd", "#dcdcdc"}


def text_value(value):
    """Reject objects/numbers where a nonempty text field is expected."""
    return value.strip() if isinstance(value, str) and value.strip() else None


def extract_event_id(url):
    try:
        match = re.search(r"-(\d{7,})/?$", urlparse(url).path)
    except (TypeError, ValueError, AttributeError):
        return None
    return match.group(1) if match else None


def find_event_json(value):
    if isinstance(value, dict):
        kind = value.get("@type")
        if kind == "Event" or isinstance(kind, list) and "Event" in kind:
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


def read_json_scripts(soup, selector, warnings):
    for index, script in enumerate(soup.select(selector), 1):
        try:
            yield json.loads(script.string or script.get_text())
        except (ValueError, TypeError, RecursionError):
            warnings.append(f"Ignored malformed JSON in {selector}, script {index}.")


def read_event_json(soup, warnings=None):
    warnings = warnings if warnings is not None else []
    for value in read_json_scripts(soup, SELECTORS["json_ld"], warnings):
        try:
            event = find_event_json(value)
        except RecursionError:
            warnings.append("Ignored excessively nested JSON-LD.")
            continue
        if event:
            return event
    return {}


def read_configuration(soup, warnings=None):
    warnings = warnings if warnings is not None else []
    for value in read_json_scripts(soup, SELECTORS["configuration"], warnings):
        if isinstance(value, dict) and "price" in value:
            return value
    return {}


def embedded_value(html, key):
    match = re.search(rf'"{re.escape(key)}"\s*:\s*("(?:\\.|[^"\\])*")', html)
    if match:
        try:
            return text_value(json.loads(match.group(1)))
        except ValueError:
            pass
    return None


def extract_country(soup):
    link = soup.select_one(SELECTORS["venue_map"])
    if link:
        try:
            query = parse_qs(urlparse(link.get("href", "")).query)
            match = re.search(r",\s*([A-Z]{2})\s*$", query.get("query", [""])[0])
            return match.group(1) if match else None
        except ValueError:
            pass
    return None


def parse_price(value):
    """Normalize German amounts with Decimal before emitting a JSON number."""
    if not isinstance(value, (str, int, float, Decimal)) or isinstance(value, bool):
        return None, None
    raw = str(value).replace("\u00a0", " ").replace("\u202f", " ").strip()
    currency = "EUR" if "€" in raw or re.search(r"\bEUR\b", raw, re.I) else None
    match = re.search(r"-?\d[\d.,\s]*", raw)
    if not match:
        return None, currency
    number = re.sub(r"\s+", "", match.group())
    if "," in number and "." in number:
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        number = number.replace(",", ".")
    elif isinstance(value, str) and re.fullmatch(r"\d{1,3}(?:\.\d{3})+", number):
        number = number.replace(".", "")
    try:
        price = Decimal(number)
        numeric = float(price)
        if price.is_finite() and price >= 0 and math.isfinite(numeric):
            return numeric, currency
    except (InvalidOperation, ValueError, OverflowError):
        pass
    return None, currency


def normalize_availability(value):
    value = text_value(value)
    if not value:
        return None
    value = re.sub(r"\s+", " ", value.lower())
    if any(word in value for word in ("nicht verfügbar", "ausverkauft", "sold out", "unavailable", "not available", "out of stock")):
        return "unavailable"
    if any(word in value for word in ("verfügbar", "available", "in stock")):
        return "available"
    return None


def normalize_datetime(value):
    """Require an explicit timezone; never invent one for a partial date."""
    value = text_value(value)
    if value:
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if date.tzinfo is not None and date.utcoffset() is not None:
                return date.isoformat(timespec="seconds")
        except (ValueError, OverflowError):
            pass
    return None


def extract_categories(config, soup=None, warnings=None):
    warnings = warnings if warnings is not None else []
    prices = config.get("price")
    if not isinstance(prices, dict) or not prices:
        warnings.append("ticket_categories: missing or malformed; recorded null.")
        return None
    categories = []
    for position, item in enumerate(prices.values(), 1):
        if not isinstance(item, dict):
            warnings.append(f"ticket_categories[{position}]: malformed category; fields recorded null.")
            item = {}
        category_id = item.get("priceCategoryId")
        category_id = str(category_id) if isinstance(category_id, (str, int)) and not isinstance(category_id, bool) else None
        price, currency = parse_price(item.get("defaultFormattedPrice"))
        raw_price = item.get("defaultPriceAsInt")
        if price is None and isinstance(raw_price, (int, float)) and not isinstance(raw_price, bool):
            try:
                # EVENTIM stores this particular field in thousandths of a euro.
                candidate = float(Decimal(str(raw_price)) / 1000)
                if math.isfinite(candidate) and candidate >= 0:
                    price = candidate
            except (InvalidOperation, ValueError, OverflowError):
                pass
        if not currency:
            explicit = item.get("currency") or config.get("currency")
            currency = "EUR" if isinstance(explicit, str) and explicit.upper() == "EUR" else None
        ticket_types = item.get("ticketTypes") or []
        if not isinstance(ticket_types, list):
            warnings.append(f"ticket_categories[{position}].ticketTypes: malformed; ignored.")
            ticket_types = []
        statuses = [normalize_availability(t.get("statusText")) if isinstance(t, dict) else None for t in ticket_types]
        availability = "available" if "available" in statuses else None
        if statuses and all(status == "unavailable" for status in statuses):
            availability = "unavailable"
        if availability is None and soup is not None and category_id:
            form = soup.find("form", attrs={"name": f"pk{category_id}"})
            rows = form.select(SELECTORS["unavailable_rows"]) if form else []
            if rows and all("ticket-type-item-wrapper-unavailable" in row.get("class", []) for row in rows):
                availability = "unavailable"
        category = {
            "id": category_id,
            "name": text_value(item.get("title")),
            "price": price,
            "currency": currency,
            "availability": availability,
        }
        for field in ("name", "price", "currency", "availability"):
            if category[field] is None:
                warnings.append(f"ticket_categories[{position}].{field}: missing or unknown; recorded null.")
        try:
            order = int(item.get("number"))
        except (TypeError, ValueError, OverflowError):
            order = 10000 + position
        categories.append((order, category))
    return [category for _, category in sorted(categories, key=lambda pair: pair[0])]


def extract_color_legend(soup, categories):
    names = {c["id"]: c["name"] for c in categories or [] if c["id"]}
    legend = {}
    for item in soup.select(SELECTORS["legend"]):
        swatch = item.select_one(SELECTORS["legend_swatch"])
        style = swatch.get("style", "") if swatch else ""
        match = re.search(r"background-color\s*:\s*(#[0-9a-fA-F]{3,8})", style)
        if match:
            category_id = item.get("data-key")
            legend[match.group(1).lower()] = {"id": category_id, "name": item.get("data-tracking-label") or names.get(category_id)}
    return legend


def extract_blocks(soup, legend, warnings=None):
    warnings = warnings if warnings is not None else []
    blocks, seen = [], set()
    for path in soup.select(SELECTORS["blocks"]):
        block_id = text_value(path.get("id"))
        if block_id and block_id.startswith("bo"):
            block_id = block_id[2:] or None
        if block_id and block_id in seen:
            continue
        if block_id:
            seen.add(block_id)
        classes = set(path.get("class", []))
        color = str(path.get("fill") or "").strip().lower()
        category = legend.get(color)
        available = False if color in GREY_COLORS else True if "has-hover" in classes or category else None
        label = path.get("aria-label") or path.get("data-label") or path.get("title")
        if not label and "lb" in classes:
            label = " ".join(t.get_text(" ", strip=True) for t in path.parent.find_all("text", recursive=False)) or None
        if block_id is None:
            warnings.append("seating_map.blocks: a section has no identifier; recorded null.")
        if available is None:
            warnings.append(f"seating_map.blocks[{block_id}].available: unknown map colour/state; recorded null.")
        blocks.append({"id": block_id, "label": label, "available": available,
                       "category": category["name"] if category else None,
                       "price_category_id": category["id"] if category else None})
    blocks.sort(key=lambda b: (0, int(b["id"])) if b["id"] and b["id"].isdigit() else (1, b["id"] or ""))
    return blocks


def parse_event(html, url):
    """Return JSON-ready values and warnings even when page fields are absent."""
    warnings = []
    soup = BeautifulSoup(html, "html.parser")
    event = read_event_json(soup, warnings)
    config = read_configuration(soup, warnings)
    location = event.get("location")
    location = location if isinstance(location, dict) else {}
    address = location.get("address")
    address = address if isinstance(address, dict) else {}
    heading = soup.select_one("h1")
    country = address.get("addressCountry")
    if isinstance(country, dict):
        country = country.get("name")
    title = text_value(event.get("name")) or text_value(config.get("eventName")) or (heading.get_text(" ", strip=True) or None if heading else None)
    date = normalize_datetime(event.get("startDate")) or normalize_datetime(embedded_value(html, "event_date"))
    venue = {
        "name": text_value(location.get("name")) or embedded_value(html, "venue_name"),
        "city": text_value(address.get("addressLocality")) or embedded_value(html, "event_city_name"),
        "country": text_value(country) or extract_country(soup),
    }
    event_id = extract_event_id(url)
    for field, value in {"event_id": event_id, "title": title, "start_datetime": date, **{f"venue.{k}": v for k, v in venue.items()}}.items():
        if value is None:
            suffix = " (an ISO datetime with timezone is required)" if field == "start_datetime" else ""
            warnings.append(f"{field}: missing or malformed{suffix}; recorded null.")
    categories = extract_categories(config, soup, warnings)
    blocks = extract_blocks(soup, extract_color_legend(soup, categories), warnings)
    map_hint = bool(config.get("seatmapOptions") or soup.select_one("svg.seatmap-svg, g.block-outlines, g.linked-blocks"))
    present = True if blocks or map_hint else False if event or config or heading else None
    if map_hint and not blocks:
        warnings.append("seating_map.blocks: map present but sections were not rendered; recorded null.")
        blocks = None
    if present is None:
        warnings.append("seating_map.present: page lacks event/map evidence; recorded null.")
        blocks = None
    return {
        "event_id": event_id, "title": title, "start_datetime": date,
        "venue": venue, "ticket_categories": categories,
        "seating_map": {"present": present, "blocks": blocks},
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "warnings": warnings,
    }
