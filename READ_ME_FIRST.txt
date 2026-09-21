SCRAPPER VIVA - START HERE
Version 1.1.0

WHAT THIS DOES
Copies an EVENTIM Germany event's name, date, venue, ticket prices,
and seating-section availability into a file called result.json.

1. EXTRACT THE ZIP
Extract the whole folder to a permanent location, such as Documents.
Do not run it from inside the ZIP. Keep all the files together.

2. INSTALL THE TWO PREREQUISITES
- Python 3.11 or newer: https://www.python.org/downloads/
  Windows: enable Add Python to PATH if the installer offers it.
- Google Chrome: https://www.google.com/chrome/
  On Linux, Python's venv support must also be installed.

3. ADD THE CHROME EXTENSION (ONCE PER COMPUTER/CHROME PROFILE)
Open Chrome and type chrome://extensions into the address bar.
Turn on Developer mode, choose Load unpacked, and select the extension
folder INSIDE the extracted Scrapper-Viva folder.
Keep that folder in place after installation.
If an older Scrapper Viva extension is installed from a different folder,
remove that old copy first so only one copy is enabled.
On the Mac already set up by Codex, use the existing project or switch the
extension to this extracted folder if you choose to run this new copy.

4. RUN THE FILE FOR YOUR COMPUTER
Mac:     Double-click START_HERE.command.
Windows: Double-click START_HERE.bat.
Linux:   Open a terminal in the folder and run: sh START_HERE.sh

The first run creates .venv and installs the required Python packages.
It needs internet access. Later runs reuse that computer's environment.
Do not copy the .venv folder between computers.

If the Mac launcher has lost its executable permission, open Terminal
in the extracted folder and run: sh START_HERE.command

5. CAPTURE ONE SHOW
Paste the full EVENTIM link for ONE event date and city.
A tour page listing several dates is not an individual event link.
When Chrome opens the event, click Saalplanbuchung (seating plan).
Wait for the coloured map, then return to the terminal and press Enter.
If another browser opens, open the same link manually in Chrome.

6. READ YOUR RESULT
A successful run saves result.json in the extracted project folder.
That file contains a snapshot; rerun the launcher to refresh it.
A successful new capture replaces the old result.json, so copy it first
if you want to keep previous captures.
The examples folder contains an older sample, not live ticket data.

Need more detail? Open README.md.
No Python or Chrome installer is bundled. Website changes can require
future scraper updates. This release was tested on macOS; Windows and
Linux launchers are included but have not been run on those systems here.
