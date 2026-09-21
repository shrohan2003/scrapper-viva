# Version 1.1.0

## Issues fixed

1. **Mac/Linux launcher line endings:** the original shell files contained Windows CRLF endings, which can make Unix systems read the interpreter as `/bin/sh` plus an invalid carriage return. The release uses LF for shell files and CRLF for the Windows batch file, with executable mode recorded in the ZIP.
2. **Unrecognized seating map:** the extension waited only for the older `g.block-outlines path.bo` SVG structure. The Santiano map uses `g.linked-blocks path.lb`, so the original capture timed out even while a coloured map was visible. Both the extension and parser now recognize both formats, retaining labels and IDs.
3. **Unavailable ticket categories:** EVENTIM omitted `ticketTypes` for two unavailable categories. The parser returned an unknown status and the completeness check refused to save the capture. The parser now uses the matching category's unavailable rows to confirm the status. An empty list by itself remains unknown.

## Packaging and usability

- Shared Python setup creates a fresh environment for each computer and installs pinned runtime packages on first use.
- Platform launchers handle common Python command names and folders containing spaces, and preserve the program's exit status.
- No virtual environment, browser profile, cache, raw captured HTML, or stale root result is included.
- Tour/artist URLs now produce an explanation to choose an individual city/date.
- Incomplete captures print specific missing fields instead of only an empty warnings list.
- Cancellation closes cleanly; setup failures do not start a capture.
- Regression tests and a three-platform CI workflow are included.

See VALIDATION.md for what has actually been executed. This is a source distribution requiring separately installed Python and Chrome.
