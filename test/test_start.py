"""Check portability and that failed setup never launches a capture."""

from pathlib import Path
from types import SimpleNamespace

import pytest

import start


def test_platform_environment_paths():
    folder = Path("Project With Spaces") / ".venv"
    assert start.environment_python(folder, windows=True) == folder / "Scripts" / "python.exe"
    assert start.environment_python(folder, windows=False) == folder / "bin" / "python"


def test_foreign_environment_is_not_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(start, "ROOT", tmp_path)
    (tmp_path / ".venv").mkdir()
    marker = tmp_path / ".venv" / "keep-me"
    marker.write_text("existing environment")
    with pytest.raises(RuntimeError, match="another operating system"):
        start.prepare_environment()
    assert marker.read_text() == "existing environment"


def test_setup_failure_does_not_start_capture(monkeypatch):
    def fail():
        raise RuntimeError("Package installation did not finish")
    monkeypatch.setattr(start, "prepare_environment", fail)
    def unexpected(*args, **kwargs):
        pytest.fail("Capture must not start after failed setup")
    monkeypatch.setattr(start.subprocess, "run", unexpected)
    assert start.main([]) == 1


def test_launcher_forwards_args_as_separate_values(tmp_path, monkeypatch):
    python = tmp_path / "with spaces" / "python"
    monkeypatch.setattr(start, "prepare_environment", lambda: python)
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=2)
    monkeypatch.setattr(start.subprocess, "run", run)
    assert start.main(["--output", "folder with spaces/result.json"]) == 2
    assert calls[0][0] == [str(python), str(start.ROOT / "capture.py"), "--output", "folder with spaces/result.json"]
