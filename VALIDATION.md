# Release validation — version 1.2.0

Validation performed on macOS arm64 on 21 September 2026.

## Actual live result

The revised Chrome extension (version 1.2.0) was reloaded and the required event
was refreshed in Chrome. After opening **Saalplanbuchung** and loading its map,
the final `scrape.py --url ... --no-open --output result.json` command captured
and parsed it at **2026-09-21T17:10:33+00:00**.

- Event: **20995028, Holiday on Ice - MIRAGE**.
- Start: **2026-11-27T19:30:00+01:00**.
- Venue: **MERKUR Ostseehalle, Kiel, DE**.
- Five categories, all available: **EUR 98, 84, 73, 62 and 46**.
- **94 seating section IDs: 37 available, 57 unavailable**.
- **Zero parser warnings**; all required fields populated.
- Live output matched the saved fixture's expected output, apart from the
  processing timestamp. Visible event metadata and ticket prices were checked
  in Chrome; the coloured seating map was visibly loaded.

An earlier capture at 16:59:32 UTC supplied the minimized real HTML fixture.
Minimizing it preserved every parsed value apart from the timestamp. The ZIP
contains that cleaned fixture, not the full session-bearing raw page.

## Automated and packaging checks

- **44 tests passed, zero skipped** with Python **3.14.6** in the working copy.
- A clean ZIP extraction into a **folder with spaces** successfully created a
  new environment and installed runtime dependencies through `START_HERE.sh`.
  That launcher selected Python **3.12.3** from its environment.
- After installing the development dependency in that fresh environment,
  **all 44 tests passed again**.
- The extracted executable **`START_HERE.command`** ran the offline fixture
  command and wrote an output filename containing spaces. Its event/category/
  section data matched the shipped live result, excluding the new timestamp.
- A subsequent dependency check succeeded with pip index access disabled
  (`PIP_NO_INDEX=1`), reusing the installed environment.
- Both POSIX launchers passed shell syntax checks. Both extension JavaScript
  files passed Node syntax checks; Python source passed compilation checks.
- ZIP integrity, explicit file allowlist, required result/fixture inclusion,
  unique relative paths, LF text / CRLF batch endings and preserved executable
  permissions were checked. No `.venv`, caches or raw capture files are bundled.
- The real fixture contains only minimized parsing evidence and data scripts;
  hidden inputs, executable scripts and session-bearing fields were excluded.

The suite uses saved HTML and local files. Its bridge integration test starts a
loopback HTTP server; it never contacts the live EVENTIM website. Missing fields
are written as null and logged, capture failures preserve an existing result,
and malformed JSON output cannot truncate a previous file.

## Scope of platform verification

**Native Windows and Linux execution was not available in this session.** Their
launchers are supplied, platform paths are covered in tests, and a GitHub
Actions matrix defines runs on Windows, macOS and Linux with Python 3.11/3.14.
Those remote jobs have not run as part of preparing this ZIP. This document does
not claim native Windows/Linux or fully unattended browser verification.

Python and Chrome must be installed separately. Live use requires the included
extension and the documented manual map step. The source package is portable;
website changes, unavailable runtimes or local browser policy may require
further setup. The GitHub upload remains the user's chosen next step.
