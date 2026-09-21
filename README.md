# Scrapper Viva — EVENTIM scraper

A Python scraper that converts a rendered EVENTIM event page into structured
JSON: event details, venue, ticket categories, prices, availability and seating
sections. The parser is independent of the browser and is tested against saved
HTML files.

**The included `result.json` is the actual required Holiday on Ice capture.**
Live scraping uses Chrome and the included extension: open the seating map, then
press Enter in the terminal. This is a browser-assisted workflow with an explicit
manual step. Offline parsing and tests run without Chrome or website access.

## Required event and included result

Source: [Holiday on Ice – MIRAGE](https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/)

| Field | Captured value |
| --- | --- |
| Event ID | `20995028` |
| Title | Holiday on Ice - MIRAGE |
| Start | `2026-11-27T19:30:00+01:00` |
| Venue | MERKUR Ostseehalle, Kiel, DE |
| Category prices | 98.00, 84.00, 73.00, 62.00, 46.00 EUR |
| Category availability | All five available at capture time |
| Seating map | Present; 94 section IDs, 37 available and 57 unavailable |
| Captured / parsed | `2026-09-21T17:10:33+00:00` |
| Required-field warnings | None |

Availability is a snapshot, not a reservation or a guarantee about later stock.
`examples/santiano-2027-05-22.json` is an additional earlier example; it is not the
assignment result.

## Installation on Mac, Windows or Linux

1. Extract the **whole ZIP**, including its `extension` and `test` directories.
   Keep the extracted folder in a stable, writable location.
2. Install **Python 3.11 or newer** and **Google Chrome** if absent. Official
   downloads: [Python](https://www.python.org/downloads/) and
   [Chrome](https://www.google.com/chrome/). On Windows, enable Python on PATH if
   the installer offers it. On Debian/Ubuntu, the matching `python3-venv` package
   is needed to create a virtual environment.
3. For live capture, open `chrome://extensions` in Chrome, enable **Developer
   mode**, click **Load unpacked**, and select this project's **extension**
   folder. Check that **Scrapper Viva EVENTIM Bridge 1.2.0** is enabled. When
   updating an already installed copy, reload the extension and the event tab.
4. Start with the launcher for your computer:

| Computer | Launcher | Terminal alternative, from the extracted folder |
| --- | --- | --- |
| macOS | Double-click `START_HERE.command` | `sh START_HERE.sh` |
| Windows | Double-click `START_HERE.bat` | `py -3 start.py` |
| Linux | Run the shell launcher | `sh START_HERE.sh` |

The launchers create `.venv` and install pinned packages on the first run, which
requires internet. Later runs check installed versions locally and reuse them.
A `.venv` is specific to its computer: it is intentionally absent from the ZIP.
Run `python3 start.py --check` (Windows: `py -3 start.py --check`) to set up and
check dependencies without starting a capture. This does not test the browser.

If macOS will not open the `.command` file, open Terminal, type `cd `, drag the
extracted project folder into the window, press Enter, then run
`sh START_HERE.sh`. The shell command also works when extraction tools do not
preserve executable permissions.

## Live command-line use

For direct CLI use, activate the environment created above:

```sh
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bat
:: Windows Command Prompt
.venv\Scripts\activate.bat
```

Then run the assignment's command:

```sh
python scrape.py --url "https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/" --output result.json
```

If activation is unavailable, the launchers accept exactly the same arguments,
for example `sh START_HERE.sh --url "..." --output another-result.json` or
`START_HERE.bat --url "..." --output another-result.json` in Command Prompt.
You can also invoke `.venv/bin/python` or `.venv\Scripts\python.exe` directly.

1. The command opens the URL in the default browser. If that is not Chrome,
   copy the URL into the Chrome profile with the extension enabled. Use
   `--no-open` if you already have it open there.
2. Handle the site's cookie choice if needed. Click **Saalplanbuchung** and wait
   for the coloured map to finish loading. Leave the filter on **Alle
   Kategorien** (all categories); do not select or purchase tickets.
   For an event without a map, wait for the ticket details instead.
3. Return to the terminal and press **Enter**. The extension transfers the
   rendered page to the Python process at `127.0.0.1:8765`.
4. The command saves JSON, prints counts and logs any missing-field warnings.
   The output defaults to `result.json`; choose another output name to preserve
   the included assignment snapshot.

A valid run with missing data still saves JSON using `null` and warnings and
exits with status 0. A capture/read/write failure exits 1 and preserves an
existing output if no replacement can be written; invalid CLI arguments exit 2.
Cancellation exits 130. `--timeout 90` increases the wait after Enter to 90
seconds. `python scrape.py --help` lists all options. The older `capture.py`
entry point remains an alias for this CLI.

## Reproduce parsing without internet

After dependency installation, this command needs neither Chrome nor a live
network connection:

```sh
python scrape.py --url "https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/" --html test/fixtures/holiday_on_ice.html --output offline-result.json
```

It reproduces the included event fields and section states, with a new
`scraped_at` timestamp for this parsing run. The original fixture capture time
and minimization process are documented in `test/fixtures/README.md`.

Install the test dependency once and run the offline suite:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover the real saved Holiday on Ice DOM, German number formats, both map
structures, unavailable and unknown categories, malformed/missing data, dates,
CLI output, local bridge event matching and startup failures. There are no
optional missing fixtures and no live-website tests. The bridge test talks only
to a temporary loopback server. See `VALIDATION.md` for results and platform
limits. A GitHub Actions matrix is provided for macOS, Windows and Linux with
Python 3.11 and 3.14; it has not been run by preparing this ZIP.

## Investigation and implementation decisions

The supplied URL is an individual event. An artist/tour page, such as the earlier
Santiano link, lists several dates and cannot identify a single event result.
The CLI therefore validates `/event/` links and extracts their numeric event ID.

A plain Python `urllib` request to the required URL with a browser-style
User-Agent timed out after 20 seconds in this environment. Chrome could load
the page, and opening **Saalplanbuchung** produced the interactive SVG needed for
section availability. A static HTML fetch alone does not execute that UI. This
observation motivated the browser route; it does not prove that all direct HTTP
requests or every environment would fail.

The existing Chrome session plus a small Manifest V3 extension was retained to
capture the same rendered DOM a person can inspect. Python handles all parsing
and output. This avoids a second browser/runtime installation, at the cost of
installing the extension and opening the map manually. The implementation does
not claim unattended or headless scraping, reverse-engineer a private inventory
API, or bypass browser challenges.

The parsing sources are combined in this order:

- **Event metadata:** Event JSON-LD when present, then public embedded metadata
  (`event_date`, `venue_name`, `event_city_name`) and the heading. Country can be
  read from the venue's public Maps address. Dates must include a timezone.
- **Ticket categories:** the embedded `application/configuration` price object
  supplies all category IDs, names, displayed default prices and ticket-type
  status text. Negative phrases are checked before positive phrases. If ticket
  types are empty, only explicitly unavailable rows in the matching category
  form support an unavailable result; empty data by itself means unknown.
- **Prices:** `Decimal` normalizes German thousands/decimal separators before
  emitting JSON numbers. `1.234,56 €` becomes `1234.56` and `EUR`. The fallback
  `defaultPriceAsInt` uses EVENTIM's observed thousandth-unit encoding (for
  example 98000 corresponds to displayed EUR 98.00). Currency is emitted only
  when EUR is explicit; it is not guessed for a missing price.
- **Seating map:** legacy `g.block-outlines path.bo` and newer
  `g.linked-blocks path.lb` represent sections. Decorative paths are excluded,
  IDs are deduplicated, and the legacy `bo` prefix is removed. Known grey fills
  mean unavailable; a hover state or a matching category colour means available.
  Unknown states are `null` with a warning. Grey takes precedence over hover.
  The category legend associates a section with a price category when possible.

`event_parser.py` keeps site-specific selectors together and exposes a pure
`parse_event(html, url)` function. Beautiful Soup is the only direct runtime
library; Python's standard library handles JSON, decimal conversion, timestamps,
the local HTTP bridge and atomic file replacement. Acquisition, parsing and the
CLI live in separate modules so each can be tested without the others.

## Output and missing values

`result.json` contains these required fields:

| Key | Meaning |
| --- | --- |
| `event_id`, `title` | Individual event ID and title |
| `start_datetime` | ISO 8601 start with explicit timezone |
| `venue` | `name`, `city`, `country` |
| `ticket_categories` | Each category's `name`, numeric `price`, ISO currency and `availability` |
| `seating_map` | `present` and a `blocks` collection with IDs and availability |
| `scraped_at` | UTC processing timestamp |

Additional fields preserve category IDs, optional section labels/category
associations, and a `warnings` list. Category availability is `available`,
`unavailable`, or `null`; block availability is `true`, `false`, or `null`.
Unknown required fields are saved as `null` and logged to stderr. A map offered
but not loaded has `present: true, blocks: null`; an identifiable event with no
map evidence has `present: false, blocks: []`; a page without usable event/map
evidence has `present: null, blocks: null`. Optional section labels and category
associations may be null even when the required ID and availability are known.

## Limitations and next steps

- Live capture requires a person to open the map and request capture. An early
  capture can be partial; read the warnings, allow loading to finish and retry.
  Keep one tab open for the requested event to avoid competing snapshots.
- The selectors and colour/status rules describe the observed German EVENTIM
  pages. A changed DOM, different map widget or locale may require new fixtures
  and parsing rules. Unknown states remain unknown instead of being guessed.
- Prices are each category's displayed default price, not every discount or
  checkout fee. Map availability describes sections, not counts of individual
  seats. Unlabelled SVG sections retain their IDs without invented names.
- A missing map marker is treated as no map on an otherwise identifiable event;
  incomplete or changed pages can hide that evidence. The required event was
  checked with its map visibly loaded.
- The bridge is local and short-lived, validates event IDs and limits capture
  size. It is intended for a trusted desktop session, not a public server.
  Raw HTML is not saved by default. `--save-html file.raw.html` is an optional
  local debugging aid; raw pages may contain session data and should not be
  submitted. Only minimized fixtures are included.
- The release was executed on macOS. Windows and Linux paths/launchers are
  supplied and covered by portable tests/CI definitions, but native execution
  on those systems remains to be verified.

With more time, the first improvements would be a Playwright acquisition mode
with explicit map readiness checks, fixtures for more venues and map states,
additional structured availability evidence to reduce colour dependence, and
native Windows/Linux live smoke checks. The current bridge can remain as a
fallback for interactive sessions.

## Files and submission

- `scrape.py`: CLI, logging and atomic JSON writer.
- `capture.py`: Chrome acquisition and the loopback bridge.
- `event_parser.py`: pure HTML parser.
- `start.py`, `START_HERE.*`: local dependency setup and platform launchers.
- `extension/`: Chrome bridge extension.
- `test/fixtures/`, `test/test_*.py`: saved evidence and regression suite.
- `result.json`: required real event output, intentionally tracked.
- `build_release.py`: builds a clean ZIP from an explicit file allowlist.

To rebuild: `python build_release.py`. The ZIP includes source, the required
result, tests and documentation. It excludes `.venv`, caches, raw captures and
machine-specific browser profiles. `SUBMISSION_CHECKLIST.md` explains the
remaining private GitHub handoff; no repository was created for this ZIP.
