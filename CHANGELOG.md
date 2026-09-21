# Changes

## 1.2.0 — final assignment package

- Capture the specified Holiday on Ice event (20995028) and include its actual
  `result.json` at the project root.
- Make `scrape.py --url ... --output ...` the live CLI; add offline `--html` mode.
- Separate acquisition, pure parsing and output writing into distinct modules.
- Save partial results with null fields and logged warnings, as required.
- Handle malformed metadata, invalid dates, missing ticket types and unknown map
  states without inventing values or rejecting all partial output.
- Add a minimized real HTML fixture, expected JSON and saved synthetic fixtures;
  remove the skipped test that depended on an absent local capture.
- Include 44 passing tests, fixture provenance, approach/limitations notes and
  explicit instructions for the manual Chrome seating-map step.
- Include submission files in the release allowlist and keep result.json in Git.
- Retain platform-specific launchers and add offline CLI validation to CI.

## 1.1.0 — portability and Santiano support

- Add Mac, Windows and Linux launchers with automatic local environment setup.
- Normalize POSIX line endings and preserve paths containing spaces.
- Support linked-area SVG maps as well as block outlines.
- Recognize explicitly unavailable category forms with empty ticket-type lists.
- Provide pinned dependencies, a clean ZIP builder and the earlier Santiano
  example (21626750).
