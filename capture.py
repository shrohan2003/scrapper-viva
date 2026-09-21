"""Capture EVENTIM through the Chrome extension and parse it with Python."""

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from event_parser import extract_event_id


PORT = 8765
MAX_BYTES = 8_000_000


def event_url_error(url):
    """Explain why a URL cannot be used for a single-event capture."""
    try:
        parsed = urlparse(url)
    except (TypeError, ValueError):
        return "Use a valid full EVENTIM event URL."
    if parsed.scheme != "https" or parsed.hostname not in {"www.eventim.de", "eventim.de"}:
        return "Use a full https://www.eventim.de/event/... URL."
    if not parsed.path.startswith("/event/"):
        return (
            "This is not an individual event page. On the tour/artist page, "
            "choose one city and date, then copy its /event/... link."
        )
    if not extract_event_id(url):
        return "The event link must contain its numeric event ID. Copy the full address from Chrome."
    return None


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
            html = payload.get("html")

            # Reject data from a different tab or a non-EVENTIM site.
            valid_page = (
                event_url_error(page_url) is None
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


class CaptureError(RuntimeError):
    """A browser capture could not be acquired."""


def capture_html(url, timeout=45, open_browser=True, prompt=None):
    """Acquire rendered HTML; parsing and output live in separate modules."""
    error = event_url_error(url)
    if error:
        raise CaptureError(error)
    state = {"requested": False, "html": None}
    received = threading.Event()
    lock = threading.Lock()
    handler = build_handler(extract_event_id(url), state, lock, received)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    except OSError as error:
        raise CaptureError(f"Local port {PORT} is unavailable. Close another capture and retry: {error}") from error
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        if open_browser:
            webbrowser.open_new_tab(url)
        print("Open this event in Chrome with Scrapper Viva enabled:", url, flush=True)
        print("If a seating map is offered, open Saalplanbuchung and wait for all colours to load.", flush=True)
        print("If this event has no seating map, wait for its ticket details to load instead.", flush=True)
        (prompt or input)("When ready, return here and press Enter: ")
        with lock:
            state["requested"] = True
        print("Receiving the rendered page...", flush=True)
        if not received.wait(timeout):
            raise CaptureError("Capture timed out. Check the extension/profile and reload the event page.")
        with lock:
            return state["html"]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


if __name__ == "__main__":
    from scrape import main
    raise SystemExit(main())
