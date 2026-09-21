"""Create a clean source ZIP; include the submission snapshot, exclude machine/session data."""

import hashlib
from pathlib import Path
import stat
import zipfile


ROOT = Path(__file__).resolve().parent
VERSION = "1.2.0"
FILES = [
    "READ_ME_FIRST.txt", "README.md", "CHANGELOG.md", "VALIDATION.md",
    "SUBMISSION_CHECKLIST.md", "result.json",
    "START_HERE.command", "START_HERE.sh", "START_HERE.bat",
    "start.py", "capture.py", "scrape.py", "event_parser.py", "build_release.py",
    "requirements.txt", "requirements-dev.txt", ".gitignore", ".gitattributes",
    "extension/manifest.json", "extension/content.js", "extension/background.js",
    "test/test_scrape.py", "test/test_capture.py", "test/test_start.py", "test/test_cli.py",
    "test/fixtures/README.md", "test/fixtures/holiday_on_ice.html",
    "test/fixtures/holiday_on_ice.expected.json", "test/fixtures/edge_cases.html",
    "test/fixtures/missing_fields.html", "test/fixtures/malformed.html", "test/fixtures/no_map.html",
    "examples/santiano-2027-05-22.json", ".github/workflows/tests.yml",
]


def main():
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / f"Scrapper-Viva-{VERSION}-Final-Mac-Windows-Linux.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for relative in FILES:
            data = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            if not data.endswith(b"\n"):
                data += b"\n"
            if relative.endswith(".bat"):
                data = data.replace(b"\n", b"\r\n")
            info = zipfile.ZipInfo(f"Scrapper-Viva/{relative}", (2026, 9, 21, 0, 0, 0))
            info.create_system = 3
            mode = 0o755 if relative.endswith((".sh", ".command")) else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, data)
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise RuntimeError("ZIP integrity check failed")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(archive)
    print(f"{len(FILES)} files; {archive.stat().st_size} bytes; SHA-256 {digest}")


if __name__ == "__main__":
    main()
