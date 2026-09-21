# Scrapper Viva — EVENTIM scraper

Version **1.1.0**. Start with **READ_ME_FIRST.txt** for plain-language instructions.

This tool reads a rendered EVENTIM Germany event page in your normal Chrome session and saves event metadata, ticket categories, prices, and seating/standing sections as JSON. Open the coloured seating map yourself, then press Enter in the launcher. The extension sends the page only to the Python server on your computer.

## Requirements

- Python **3.11 or newer**, installed separately.
- Google Chrome, with the included extension installed in the profile you use.
- Internet for first-time package installation and the EVENTIM website.
- A writable, fully extracted project folder in a permanent location.
- On Linux, Python's `venv` support (for example the matching `python3-venv` package on Debian/Ubuntu).
- An individual `https://www.eventim.de/event/...` page with a supported coloured SVG seating map.

The ZIP includes source code and pinned Python dependency versions. It does not bundle Python, Chrome, or a computer-specific virtual environment.

## Setup and running

1. Extract the entire ZIP. Keep the files together and leave the extension folder in place after installation.
2. Open `chrome://extensions` in Chrome. Enable **Developer mode**, choose **Load unpacked**, and select this project's `extension` folder. Enable **Scrapper Viva EVENTIM Bridge**.
3. Start the launcher for your operating system:

| Platform | Start |
| --- | --- |
| macOS | Double-click `START_HERE.command` |
| Windows | Double-click `START_HERE.bat` |
| Linux | Open a terminal in the extracted folder and run `sh START_HERE.sh` |

On first run, the launcher creates `.venv` and installs `requirements.txt` automatically. Later runs check the installed versions locally and only install packages if needed. You do not need to activate the environment or type pip commands.

On Windows, the launcher tries `py -3`, then `python`. On macOS/Linux it finds Python 3.11+ using common command names and macOS installation paths. Install Python from [python.org](https://www.python.org/downloads/) if it cannot be found. Enable **Add Python to PATH** if offered by the Windows installer, then reopen the launcher.

If extraction loses the Mac launcher's executable permission, run this from a terminal in the project folder:

```sh
sh START_HERE.command
```

Alternatively, restore permissions with `chmod +x START_HERE.command START_HERE.sh`.

### Updating an existing installation

Keep a copy of any old results you want to retain. Replace the source files with this release, then click **Reload** on the extension card in `chrome://extensions` and reload existing EVENTIM tabs. If using a new extracted folder, remove the old Scrapper Viva extension and load the new folder; keep only one copy enabled. Each computer creates its own `.venv`; do not transfer that folder between operating systems.

## Capture one event

1. Keep Chrome open in the profile where the extension is installed. Close older tabs for the same event.
2. Run the appropriate launcher.
3. Paste the full event URL and press Enter. Choose one city and date from a tour page first.
4. In Chrome, click **Saalplanbuchung** (seating plan) and wait for the coloured map to load. Leave **all categories** selected for a complete view.
5. Return to the launcher terminal and press Enter.
6. A successful capture writes `result.json` beside `capture.py` and prints a summary.

The program asks your default browser to open the link. If that is not Chrome, open the printed link manually in the Chrome profile with the extension. Chrome does not have to be your default browser for a manual capture.

Example individual event:

```text
https://www.eventim.de/event/santiano-15-jahre-die-grosse-jubilaeumstour-2027-freilichtbuehne-am-kalkberg-21626750/
```

A live capture on 21 September 2026 returned 10 ticket categories and 18 map sections for that event. Those counts are specific to that snapshot.

## Output and limitations

`result.json` includes:

- Event ID, title, start date/time and venue.
- Ticket category IDs, names, prices, currency and availability.
- Map section IDs, labels, inferred availability, and category mappings where exposed.
- UTC parsing time (`scraped_at`) and parser warnings.

A capture is a snapshot. It does not update itself or guarantee that a displayed ticket remains purchasable. Sections are not individual seats or seat counts. A section can include more than one ticket category; its displayed colour does not enumerate every category inside it. Some labels or mappings may be null. Prices retained in embedded data for unavailable categories are not currently bookable offers; additional charges may apply.

A successful new capture replaces the previous `result.json`. Copy the old file first if you want a history. The `examples` folder contains a dated sample; no pre-existing `result.json` is shipped at the project root.

The capture bridge checks required fields before saving. An incomplete capture writes `result.capture_error.json`, prints the missing information, and preserves the existing result file. An older diagnostic file can remain after a later successful run; use the latest run's message and each file's `scraped_at` timestamp.

The parser supports the legacy block-outline SVG map and the linked-area SVG map used by the tested Santiano event. Events without these structures, future website changes, and blocked pages can prevent a capture. The extension reads pages you can access normally; it does not bypass site access restrictions.

## Troubleshooting

| Message or symptom | Action |
| --- | --- |
| Python not found | Install Python 3.11+, then reopen the launcher. |
| Could not create .venv | Check the folder is writable; on Linux install the matching Python venv package. Rename a partially created `.venv` before retrying. |
| Environment belongs to another OS / cannot run | Rename `.venv` to `.venv-old`, then rerun; a new environment will be created. |
| Package installation failed | Check internet access and the printed pip error, then rerun. |
| Tour/artist URL rejected | Click one city/date and copy its individual `/event/...` link. |
| Capture timed out | Enable the extension in the right Chrome profile, reload the event, and open the supported coloured map. |
| Port 8765 unavailable | Close another running capture; run one at a time. |
| Incomplete capture | Read the printed reasons; wait for the full map and retry with all categories selected. |
| Wrong browser opens | Open the printed URL manually in Chrome. |
| Shell / permission error | Run `sh START_HERE.command` on Mac or `sh START_HERE.sh` on Linux. Keep both files saved with LF line endings. |
| Access Denied | The website is refusing the page request; try opening it normally in Chrome later. |

## Command-line options

From the project folder, the shared entry point also works directly:

```sh
python3 start.py --check
python3 start.py --setup-only
python3 start.py --help
python3 start.py --url "https://www.eventim.de/event/...-21626750/" --output latest.json
```

On Windows, replace `python3` with `py -3` or `python`. Launchers also accept these arguments. `--check` and `--setup-only` prepare and check Python dependencies without opening an event; they do not test the browser extension. The output directory must already exist.

To parse an HTML file you already saved:

```sh
.venv/bin/python scrape.py --url "https://www.eventim.de/event/...-21626750/" --html saved.html --output offline_result.json
```

Windows: use `.venv\Scripts\python.exe`. The offline parser does not enforce the live capture's completeness checks; its timestamp is parsing time.

## Validation

See **VALIDATION.md** for the release's actual checks and platform limits. The automated tests cover both map formats, unavailable categories, URL validation, the local HTTP bridge, and startup failures. They do not imply that every EVENTIM event is supported.

To run the tests:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Windows: replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

One optional test is skipped unless the old development capture `eventim_real_capture.html` is supplied. That file is intentionally not bundled. A GitHub Actions workflow is included for macOS, Windows and Linux on Python 3.11 and 3.14; including it does not mean those remote jobs have been run.

## Files

- `START_HERE.command`, `START_HERE.bat`, `START_HERE.sh`: OS launchers.
- `start.py`: automatic local environment setup and startup.
- `capture.py`: local browser bridge and validated JSON output.
- `scrape.py`: HTML parser.
- `extension/`: Chrome extension.
- `requirements.txt`: pinned runtime dependencies.
- `requirements-dev.txt`, `test/`: optional developer tests.
- `examples/`: dated sample output.
- `build_release.py`: build a clean source ZIP with correct line endings and launcher permissions.

The bridge listens only on `127.0.0.1:8765` while capturing. The normal workflow keeps raw HTML in memory and writes extracted JSON to disk.
