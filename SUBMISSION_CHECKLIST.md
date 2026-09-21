# Submission checklist

The requested deliverable is a ZIP only. No GitHub repository, invitation or
external submission has been made as part of preparing this package.

## Included for review

- `result.json`: actual capture of the required Holiday on Ice event, ID 20995028.
- `scrape.py`: live and offline command-line entry point.
- `event_parser.py`: HTML-to-JSON parsing with missing-field warnings.
- `capture.py` and `extension/`: browser acquisition and local bridge.
- `test/fixtures/` and `test/`: saved HTML evidence and offline regression tests.
- `README.md`: installation, CLI usage, investigation, decisions and limitations.
- Platform launchers, pinned dependencies and `.github/workflows/tests.yml`.
- `VALIDATION.md`: checks performed and platform verification limits.

## If you submit through GitHub

1. Extract this ZIP and create a **private** repository in the account you intend
   to use for the assignment.
2. Add the extracted project's files, including `result.json`, all files under
   `test/fixtures/`, and the hidden `.github`, `.gitignore` and `.gitattributes`
   entries. Do not add `.venv`, caches or raw captures. With Git installed, run
   `git init`, then `git add .` from the extracted project folder; inspect
   `git status` before committing and connecting the chosen repository.
3. Commit and push the files. Check that the repository displays the README,
   required result, fixture HTML and tests. If Actions is enabled, inspect the
   Windows, macOS and Linux test runs; the workflow's presence is not a passing run.
4. Follow the assignment's access requirement for GitHub user **shamiul94**
   (the PDF lists `1505038.sh@ugrad.cse.buet.ac.bd` as contact information).
   Verify the intended recipient before sending an invitation.
5. Send the repository link through the assignment's requested submission channel.

The live capture has an explicit manual step: open the seating map in Chrome and
press Enter in the terminal. Explain that design choice if asked. The offline
fixture command and automated tests require no browser interaction.
