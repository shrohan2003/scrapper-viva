"""Exercise the local bridge and failures that previously confused users."""

from http.server import ThreadingHTTPServer
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from capture import build_handler, event_url_error


URL = "https://www.eventim.de/event/test-21626750/"


@pytest.mark.parametrize("url", [
    URL, URL + "?affiliate=EVE", URL.replace("www.eventim.de", "eventim.de"),
])
def test_individual_event_urls(url):
    assert event_url_error(url) is None


@pytest.mark.parametrize("url", [
    "https://www.eventim.de/artist/santiano/tour-4149637/",
    "https://example.com/event/test-21626750/",
    "http://www.eventim.de/event/test-21626750/",
    "https://www.eventim.de/event/test/",
])
def test_reject_unsupported_urls(url):
    assert event_url_error(url)


def test_bridge_requires_request_and_matching_event():
    state = {"requested": False, "html": None}
    received = threading.Event()
    lock = threading.Lock()
    server = ThreadingHTTPServer(("127.0.0.1", 0), build_handler("21626750", state, lock, received))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def post(url):
        request = Request(base + "/capture", data=json.dumps({"url": url, "html": "<html>test</html>"}).encode(), headers={"Content-Type": "application/json"})
        return urlopen(request, timeout=3)

    try:
        with urlopen(base + "/status", timeout=3) as response:
            assert json.load(response) == {"capture": False, "event_id": "21626750"}
        with pytest.raises(HTTPError) as error:
            post(URL)
        assert error.value.code == 409
        with lock:
            state["requested"] = True
        for wrong_url in [URL.replace("21626750", "21626751"), URL.replace("/event/", "/artist/")]:
            with pytest.raises(HTTPError) as error:
                post(wrong_url)
            assert error.value.code == 400
            assert not received.is_set()
        with post(URL) as response:
            assert json.load(response) == {"ok": True}
        assert received.wait(1)
        assert state["html"] == "<html>test</html>"
        assert state["requested"] is False
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
