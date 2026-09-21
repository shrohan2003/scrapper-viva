"""Command-line entry point for live or offline EVENTIM scraping."""

import argparse
import json
import logging
import os
from pathlib import Path
import tempfile

from capture import CaptureError, capture_html, event_url_error
from event_parser import parse_event

LOGGER = logging.getLogger("scrapper_viva")


def write_result(result, output):
    """Atomically save JSON, including null values and warnings for partial data."""
    output = Path(output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         prefix=f".{output.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape an EVENTIM event into structured JSON")
    parser.add_argument("--url", help="Full EVENTIM event URL; prompted if omitted")
    parser.add_argument("--output", default="result.json", help="JSON output file")
    parser.add_argument("--html", type=Path, help="Parse a saved HTML fixture without browser/network access")
    parser.add_argument("--no-open", action="store_true", help="Use an event already open in Chrome")
    parser.add_argument("--timeout", type=float, default=45, help="Seconds to wait after Enter (default: 45)")
    parser.add_argument("--save-html", type=Path, help="Optional raw HTML debug file; do not commit session data")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if not 0 < args.timeout <= 600:
        parser.error("--timeout must be between 0 and 600 seconds")
    try:
        url = (args.url or input("Paste the individual EVENTIM event URL: ")).strip()
        error = event_url_error(url)
        if error:
            parser.error(error)
        if args.html:
            html = args.html.read_text(encoding="utf-8")
        else:
            html = capture_html(url, timeout=args.timeout, open_browser=not args.no_open)
        if args.save_html:
            args.save_html.write_text(html, encoding="utf-8")
        result = parse_event(html, url)
        for warning in result["warnings"]:
            LOGGER.warning(warning)
        write_result(result, args.output)
        print(f"Saved: {Path(args.output).resolve()}")
        print("Event:", result["event_id"], result["title"])
        print("Ticket categories:", len(result["ticket_categories"] or []))
        print("Seating sections:", len(result["seating_map"]["blocks"] or []))
        print("Warnings:", len(result["warnings"]))
        if result["warnings"]:
            print("Partial data saved: missing values are null. See warnings in the JSON and log above.")
        return 0
    except (CaptureError, OSError, UnicodeError) as error:
        LOGGER.error("%s", error)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCapture cancelled.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
