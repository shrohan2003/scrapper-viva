"""Verify offline CLI behavior, warning logs and atomic output preservation."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

import scrape
from capture import CaptureError

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/"


def test_offline_cli_runs_from_another_directory_without_live_capture(tmp_path):
    output = tmp_path / "result with spaces.json"
    run = subprocess.run([
        sys.executable, str(ROOT / "scrape.py"), "--url", URL,
        "--html", str(ROOT / "test/fixtures/holiday_on_ice.html"),
        "--output", str(output),
    ], cwd=tmp_path, text=True, capture_output=True, timeout=15)
    assert run.returncode == 0, run.stderr
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["event_id"] == "20995028"
    assert len(result["seating_map"]["blocks"]) == 94
    assert result["warnings"] == []


def test_missing_fields_are_written_and_logged(tmp_path, monkeypatch, caplog):
    def unexpected(*args, **kwargs):
        pytest.fail("Offline parsing must not acquire a live page")
    monkeypatch.setattr(scrape, "capture_html", unexpected)
    output = tmp_path / "partial.json"
    assert scrape.main(["--url", URL, "--html", str(ROOT / "test/fixtures/missing_fields.html"),
                        "--output", str(output)]) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["venue"]["name"] is None
    assert result["warnings"]
    assert all(warning in caplog.text for warning in result["warnings"])


def test_live_capture_failure_preserves_existing_result(tmp_path, monkeypatch):
    output = tmp_path / "result.json"
    original = '{"previous":"keep me"}\n'
    output.write_text(original, encoding="utf-8")
    def fail(*args, **kwargs):
        raise CaptureError("Capture timed out")
    monkeypatch.setattr(scrape, "capture_html", fail)
    assert scrape.main(["--url", URL, "--no-open", "--output", str(output)]) == 1
    assert output.read_text(encoding="utf-8") == original


def test_invalid_json_cannot_truncate_previous_output(tmp_path):
    output = tmp_path / "result.json"
    output.write_text("previous", encoding="utf-8")
    with pytest.raises(ValueError):
        scrape.write_result({"price": float("nan")}, output)
    assert output.read_text(encoding="utf-8") == "previous"
    assert list(tmp_path.iterdir()) == [output]
