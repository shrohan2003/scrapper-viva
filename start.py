"""Set up this computer's Python environment, then run the scraper."""

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
MIN_PYTHON = (3, 11)


def environment_python(folder, windows=None):
    """Return the platform-specific interpreter inside a virtual environment."""
    if windows is None:
        windows = os.name == "nt"
    return folder / ("Scripts/python.exe" if windows else "bin/python")


def requirements_ready(python, requirements):
    """Check installed versions without contacting the internet."""
    expected = dict(
        line.strip().split("==", 1)
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    check = (
        "import importlib.metadata as m,json,sys; "
        "expected=json.loads(sys.argv[1]); "
        "sys.exit(0 if all(m.version(k)==v for k,v in expected.items()) else 1)"
    )
    result = subprocess.run(
        [str(python), "-c", check, json.dumps(expected)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return result.returncode == 0


def prepare_environment():
    folder = ROOT / ".venv"
    python = environment_python(folder)
    requirements = ROOT / "requirements.txt"
    if not folder.exists():
        print("First run: creating a Python environment for this computer...", flush=True)
        try:
            import venv
            venv.EnvBuilder(with_pip=True).create(folder)
        except (ImportError, OSError, subprocess.SubprocessError) as error:
            raise RuntimeError(
                "Could not create .venv. Check that this folder is writable. "
                "On Debian/Ubuntu, install the python3-venv package matching "
                "your Python version. If .venv is incomplete, rename it and retry."
            ) from error
    if not python.is_file():
        raise RuntimeError(
            "The .venv folder is incomplete or belongs to another operating system. "
            "Rename it to .venv-old and run the launcher again. "
            "Do not copy .venv between computers."
        )
    try:
        version_check = subprocess.run(
            [str(python), "-c", "import sys; sys.exit(sys.version_info < (3, 11))"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    except OSError as error:
        raise RuntimeError(
            "The saved Python environment cannot run. Rename .venv to "
            ".venv-old and run the launcher again."
        ) from error
    if version_check.returncode:
        raise RuntimeError(
            "The saved environment needs Python 3.11 or newer. "
            "Rename .venv to .venv-old and run the launcher again."
        )
    if not requirements_ready(python, requirements):
        print("Installing the required packages (internet needed on first run)...", flush=True)
        result = subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check",
             "-r", str(requirements)], cwd=ROOT, check=False,
        )
        if result.returncode or not requirements_ready(python, requirements):
            raise RuntimeError(
                "Package installation did not finish. Check your internet "
                "connection and the message above, then run the launcher again."
            )
    return python


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if sys.version_info < MIN_PYTHON:
        print("Python 3.11 or newer is required. Install it from https://www.python.org/downloads/.")
        return 1
    try:
        python = prepare_environment()
        if args in (["--setup-only"], ["--check"]):
            print("Python environment and dependencies: ready")
            print(f"Chrome extension folder: {ROOT / 'extension'}")
            print("Install/enable that folder at chrome://extensions in Chrome.")
            print("The browser extension and live website are not tested by this check.")
            return 0
        print("\nScrapper Viva - EVENTIM capture", flush=True)
        print("Use Chrome with the Scrapper Viva extension enabled.", flush=True)
        print("For live capture, choose one event date and city and follow the prompts.\n", flush=True)
        return subprocess.run(
            [str(python), str(ROOT / "scrape.py"), *args], cwd=ROOT, check=False,
        ).returncode
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Setup error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
