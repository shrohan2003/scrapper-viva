"""Capture EVENTIM through the Chrome extension and parse it with Python."""

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from scrape import extract_event_id, parse_event


PORT = 8765
MAX_BYTES = 8_000_000


def build_handler(expected_id, state, lock, received):
    """Create a local HTTP handler for one capture run."""

    class BridgeHandler(BaseHTTPRequestHandler):
        def send_json(self, status, value):
            data = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            """Tell the extension whether Enter has been pressed."""
            if self.path != "/status":
                self.send_json(404, {"error": "Not found"})
                return

            with lock:
                requested = state["requested"]

            self.send_json(
                200,
                {"capture": requested, "event_id": expected_id},
            )

        def do_POST(self):
            """Receive the rendered HTML from the extension."""
            if self.path != "/capture":
                self.send_json(404, {"error": "Not found"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0

            if not 0 < length <= MAX_BYTES:
                self.send_json(413, {"error": "Capture size is invalid"})
                return

            try:
                payload = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_json(400, {"error": "Invalid JSON"})
                return

            if not isinstance(payload, dict):
                self.send_json(400, {"error": "Invalid capture"})
                return

            page_url = str(payload.get("url", ""))
            parsed_url = urlparse(page_url)
            html = payload.get("html")

            # Reject data from a different tab or a non-EVENTIM site.
            valid_page = (
                parsed_url.scheme == "https"
                and parsed_url.hostname in {"www.eventim.de", "eventim.de"}
                and extract_event_id(page_url) == expected_id
            )
            if not valid_page or not isinstance(html, str) or not html:
                self.send_json(400, {"error": "Wrong page or empty HTML"})
                return

            with lock:
                if not state["requested"]:
                    self.send_json(409, {"error": "Capture was not requested"})
                    return

                state["html"] = html
                state["requested"] = False
                received.set()

            self.send_json(200, {"ok": True})

        def log_message(self, format_string, *args):
            """Hide routine local-server requests from the terminal."""
            return

    return BridgeHandler


def complete_result(result):
    """Check required data before replacing result.json."""
    venue = result["venue"]
    categories = result["ticket_categories"]
    blocks = result["seating_map"]["blocks"]

    return bool(
        result["event_id"]
        and result["title"]
        and result["start_datetime"]
        and all(venue.get(key) for key in ("name", "city", "country"))
        and categories
        and all(
            row.get("name")
            and row.get("price") is not None
            and row.get("currency")
            and row.get("availability")
            for row in categories
        )
        and blocks
        and all(block.get("available") is not None for block in blocks)
    )


def main():
    """Open a tab, wait for Enter, receive the page, and write JSON."""
    parser = argparse.ArgumentParser(
        description="Capture and parse an EVENTIM event"
    )
    parser.add_argument(
        "--url",
        help="EVENTIM event URL; prompted if omitted",
    )
    parser.add_argument(
        "--output",
        default="result.json",
        help="Output JSON file",
    )
    args = parser.parse_args()

    # Running "python capture.py" prompts for the URL like START_HERE.
    url = (args.url or input("Paste the EVENTIM event URL: ")).strip()
    parsed_url = urlparse(url)
    event_id = extract_event_id(url)

    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in {"www.eventim.de", "eventim.de"}
        or not event_id
    ):
        parser.error("Enter a full https://www.eventim.de/event/... URL")

    state = {"requested": False, "html": None}
    lock = threading.Lock()
    received = threading.Event()
    handler = build_handler(event_id, state, lock, received)

    # Bind only to this computer; the raw HTML is kept in memory.
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    except OSError as error:
        parser.error(f"Local capture port {PORT} is unavailable: {error}")

    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    try:
        # Request a new tab in the existing default-browser window.
        if not webbrowser.open_new_tab(url):
            print("Could not open a tab automatically. Open this URL:")
            print(url)

        print("Open the coloured seating map in the new Chrome tab.")
        input("When the map is visible, return here and press Enter: ")

        with lock:
            state["requested"] = True

        print("Receiving the rendered page from the extension...")
        if not received.wait(timeout=45):
            print(
                "Capture timed out. Check that the extension is enabled "
                "and the coloured map is visible."
            )
            return 2

        with lock:
            html = state["html"]

        result = parse_event(html, url)
        output = Path(args.output)

        if not complete_result(result):
            error_path = output.with_name(
                output.stem + ".capture_error.json"
            )
            error_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Incomplete capture. Diagnostic: {error_path}")
            print("Existing result.json was not overwritten.")
            print("Warnings:", result["warnings"])
            return 2

        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        print("Saved:", output)
        print("Event:", result["event_id"], result["title"])
        print("Ticket categories:", len(result["ticket_categories"]))
        print("Seating blocks:", len(result["seating_map"]["blocks"]))
        print("Warnings:", result["warnings"])
        return 0

    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())