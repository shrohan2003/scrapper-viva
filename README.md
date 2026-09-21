# Scrapper Viva — EVENTIM Scraper

A Python project that reads an EVENTIM event page from your browser and saves event details, ticket categories, and seating-block information as JSON.

You open the seating map yourself. After you press Enter in the terminal, a small Chrome extension sends the rendered page to Python, which extracts the data and writes `result.json`.

## Current status

The complete Windows launcher workflow has been tested successfully. The tested event produced 5 ticket categories, 94 seating blocks, and no parser warnings. These counts belong to that event and are not expected for every event.

macOS and Linux launchers are included, but have not yet been tested on those operating systems. Four parser tests passed locally with the saved event HTML available.

## Requirements

- Python 3.11 or newer; development was done with Python 3.11.
- Google Chrome with the included extension installed and enabled.
- Chrome set as your default browser for automatic opening.
- An internet connection and an EVENTIM Germany event page with a supported coloured seating map.

The Python dependencies are listed in `requirements.txt`. Playwright is not required for the current extension-based workflow.

## Project files

```text
scrapper viva/
├── README.md
├── requirements.txt
├── scrape.py
├── capture.py
├── START_HERE.bat
├── START_HERE.command
├── START_HERE.sh
├── .gitignore
├── extension/
│   ├── manifest.json
│   ├── background.js
│   └── content.js
├── test/
│   └── test_scrape.py
└── result.json
```

`capture.py` handles the browser-to-Python connection and saves successful captures. `scrape.py` extracts fields from HTML. The three launchers run the same Python program using the launch format supported by each operating system.

The `.venv` folder is created during setup. Create it separately on each computer; do not copy a Windows virtual environment to macOS or Linux.

## First-time setup

Download or copy the project to your computer. Open a terminal inside the project folder, then follow the steps for your operating system.

### Windows

Run these commands in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `python` is not recognised but the Python launcher is installed, use `py -3 -m venv .venv` for the first command.

For daily use, double-click `START_HERE.bat`. It opens a terminal and runs the program. You do not need to activate the virtual environment manually.

### macOS

Run these commands in Terminal:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
chmod +x START_HERE.command
```

For daily use, double-click `START_HERE.command` in Finder. You can also run it from the project folder:

```sh
./START_HERE.command
```

### Linux

Run these commands in a terminal:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
chmod +x START_HERE.sh
```

For daily use, run this from the project folder:

```sh
./START_HERE.sh
```

Some Linux file managers offer “Run in Terminal” when opening a shell script; double-click behaviour depends on your desktop settings. If creating the environment fails because `venv` is unavailable, install the Python virtual-environment package for your distribution and retry.

Keep both `START_HERE.command` and `START_HERE.sh` saved with LF line endings. In VS Code, a `.command` file may appear as plain white text until its language mode is set to Shell Script. Its colour does not determine whether it works.

## Install the Chrome extension — all operating systems

1. Open Chrome and enter `chrome://extensions` in the address bar.
2. Turn on **Developer mode**.
3. Click **Load unpacked**.
4. Select the project's `extension` folder, which contains `manifest.json`.
5. Confirm that **Scrapper Viva EVENTIM Bridge** is enabled.

Keep the extension folder in place after installation. If you change its code, click Reload on its extension card and reload the EVENTIM tab so the updated code runs there.

## Capture an event

1. Keep Chrome open in the profile where you installed the extension. Close older tabs for the same event to avoid capturing an older copy of the page.
2. Start the launcher for your operating system.
3. Paste the full event URL into the terminal and press Enter.
4. The program requests a new tab in your default browser. Wait for the event page to load and open its coloured seating map.
5. Once the map is visible and loaded, return to the terminal and press Enter.
6. The extension sends the page to Python. A successful capture saves `result.json` and prints a summary.

Example event URL used during development:

```text
https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/
```

Example output:

```text
Saved: result.json
Event: 20995028 Holiday on Ice - MIRAGE
Ticket categories: 5
Seating blocks: 94
Warnings: []
```

When using a launcher, `result.json` is saved in the project folder beside `capture.py`. Open it in VS Code or another text editor.

The program requests a new tab, but the browser and operating system determine the actual window used. Keep Chrome open and set as the default browser. If another browser opens, open the event URL manually in the Chrome profile with the extension.

## How it works

```text
START_HERE → paste event URL → Chrome opens the page
    → you open the seating map → you press Enter
    → extension sends rendered HTML to local Python
    → BeautifulSoup extracts the fields → result.json
```

“Rendered HTML” means the page structure after the website's JavaScript has loaded or changed it. Opening the seating map adds information that may be missing from the original page response.

The parser reads event metadata from JSON-LD where available, with fallbacks to other embedded page data. Ticket categories come from EVENTIM's embedded configuration. Seating blocks come from the rendered SVG map, with availability inferred from map colours and CSS classes.

### Why use an extension if the project is Python?

Python performs the capture coordination, parsing, validation, and JSON output. The small JavaScript extension provides access to the page in your normal Chrome session. Chrome extensions use JavaScript; a normal Python script cannot directly read an arbitrary existing Chrome tab without a browser integration.

This approach supports using your existing browser session and manually opening the seating map. It avoids requiring you to copy HTML through Developer Tools each time.

The bridge listens at `127.0.0.1:8765` on your computer while the program runs. The extension checks for a capture request and sends the rendered HTML after you press Enter. The normal capture workflow holds raw HTML in memory and writes the extracted JSON to disk.

## What the JSON contains

| Field | Meaning |
| --- | --- |
| `event_id` | Event identifier extracted from the URL. |
| `title` | Event name. |
| `start_datetime` | Event start date/time as provided by the page. |
| `venue` | Venue name, city, and country. |
| `ticket_categories` | Category IDs, names, prices, currencies, and availability. |
| `seating_map.present` | Whether seating-map information was detected. |
| `seating_map.blocks` | Block IDs, inferred availability, and labels/category mappings where available. |
| `scraped_at` | UTC time when Python parsed the captured HTML. |
| `warnings` | Missing-data issues detected by the parser. |

Seating blocks are not individual seats. A block marked available does not provide a seat count or guarantee that any particular seat can be purchased. Some labels or category mappings may be `null` because the captured map does not expose them.

### The result is a snapshot

The JSON does not update itself when EVENTIM changes prices or availability. For example, a file captured ten minutes ago still contains that capture's values.

To refresh it, rerun the launcher, let a fresh event page load, open the seating map, and press Enter. A successful capture replaces the previous output file. Copy or rename the old file first if you want to keep a history.

`scraped_at` records parsing time, not proof of when EVENTIM last refreshed its inventory. An old browser tab can contain stale data, so use a freshly loaded page. Continuous automatic updates are not implemented in this version.

## Warnings and incomplete captures

`Warnings: []` means the parser did not detect any of its listed missing-data conditions. It does not independently prove that every value matches current live inventory.

Warnings can report missing metadata, missing ticket categories, or a seating map whose rendered blocks could not be found. Common causes are incomplete page loading, not opening the map, or a website layout change.

`capture.py` also checks required fields, category values, and block availability before saving. If these checks fail, it writes `result.capture_error.json` and leaves an existing `result.json` untouched. In that case, the existing result still belongs to an earlier successful run. An incomplete capture can occur even with an empty warning list because the completeness check covers additional conditions.

VS Code's Problems counter for a saved HTML file is separate from the scraper's `warnings` field. Inspect those editor messages separately; they do not automatically mean the JSON capture failed.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Access Denied | The site is refusing the browser request. During development, this happened on some attempts. Try opening the page normally in Chrome later. The extension reads a page you can already access; it does not bypass an access block. |
| Capture timed out | The program waits up to 45 seconds after Enter. Check the extension is enabled in the correct Chrome profile, reload the event page if the extension was just installed, open the coloured map, and run again. |
| Local port 8765 is unavailable | Another capture run or program may be using it. Close your previous capture terminal and retry. Run one capture at a time. |
| A new window or wrong browser opens | Set Chrome as your default browser and keep its intended profile open. Tab/window placement is controlled by the browser. You can open the URL manually in the correct Chrome window. |
| “Create the virtual environment…” | Complete the setup commands for your operating system in the project folder. |
| No seating blocks or incomplete capture | Wait for the coloured map to finish loading. This workflow requires the supported SVG seating map; events without it are not currently supported by the capture bridge. |
| Saved HTML file not found | This applies to the optional offline parser. Check the filename and location. Normal launcher use does not require a saved HTML file. |
| macOS/Linux permission or shell errors | Apply the `chmod +x` command for your launcher and make sure its line endings are LF. |

## Optional command-line use

Run commands from the project folder. After activating the virtual environment, you can use:

```sh
python capture.py
python capture.py --url "https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/" --output latest.json
```

Without activation, replace `python` with `.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux. The output folder must already exist.

To parse an HTML file you already saved:

```sh
python scrape.py --url "https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/" --html eventim_real_capture.html --output offline_result.json
```

The offline parser writes its result directly, even if fields are missing; it does not apply `capture.py`'s completeness protection. Its `scraped_at` is the time of parsing, not the original HTML capture time.

## Tests

From the project folder, use the environment's Python:

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

macOS/Linux:

```sh
.venv/bin/python -m pytest -q
```

Three tests use self-contained examples for price conversion, availability text, and event/map parsing. A fourth checks the development event's saved `eventim_real_capture.html` when that file is present. Since the HTML is excluded from Git, a fresh checkout should normally report three passed and one skipped. That fourth test expects the development snapshot's 5 categories and 94 blocks; it is not a general test for every event.

These parser tests do not verify the Chrome extension or the macOS/Linux launchers end to end.

## Scope and limitations

The current implementation targets EVENTIM Germany pages with the supported rendered map structure. Website changes may require parser updates. It captures displayed and embedded page data; it does not reserve or purchase tickets. The checked-in `result.json`, if present, is an example snapshot until you replace it with your own successful capture.
