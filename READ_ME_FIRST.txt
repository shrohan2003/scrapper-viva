SCRAPPER VIVA 1.2.0 - FINAL SUBMISSION PACKAGE

This program reads an EVENTIM event page and saves ticket/event details as JSON.
It includes the real result for the Holiday on Ice event required by the task.

TO REVIEW OR SUBMIT
1. Extract the entire ZIP.
2. Open README.md for the approach, running instructions and limitations.
3. Open result.json for the required Holiday on Ice capture.
4. See SUBMISSION_CHECKLIST.md for the private GitHub submission steps.
   No repository has been created and nothing has been submitted for you.

TO RUN A NEW LIVE CAPTURE
You need Python 3.11 or newer, Google Chrome, and internet access.
The ZIP is source code; it does not contain Python or Chrome.

1. Keep the extracted folder in a permanent location.
2. In Chrome, open chrome://extensions, turn on Developer mode, choose
   Load unpacked, and select the extension folder inside this project.
3. Launch for your computer:
   Mac: double-click START_HERE.command.
   Windows: double-click START_HERE.bat (extract the ZIP first).
   Linux: open a terminal in this folder and run: sh START_HERE.sh
4. Paste an individual EVENTIM /event/ link into the terminal.
5. Open that event in Chrome. Click Saalplanbuchung if offered and wait for
   the coloured seating map. Leave the category filter on Alle Kategorien.
6. Return to the terminal and press Enter. It saves result.json in this folder.

The first launch installs Python packages into a local .venv folder.
Later launches reuse them. Do not copy .venv between computers.

A new successful run replaces result.json, including when some fields are
missing. Missing values are null and explained in warnings. Keep a copy of the
included submission result before capturing another event. Command-line users
can use --output another-result.json to keep the included result unchanged.

MAC FALLBACK
If double-clicking is blocked or the terminal closes, open Terminal, type cd
followed by a space, drag the extracted Scrapper-Viva folder into Terminal,
press Enter, then run: sh START_HERE.sh

TEST WITHOUT THE WEBSITE
The README includes an offline command using the saved HTML fixture. It needs
no Chrome extension or website connection after Python packages are installed.

Validated on macOS. Windows/Linux launchers and a CI matrix are included, but
native Windows/Linux execution was not available during this validation.
