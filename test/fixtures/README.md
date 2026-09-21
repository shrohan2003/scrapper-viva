# Offline HTML fixtures

`holiday_on_ice.html` is a minimized copy of the public rendered DOM from
https://www.eventim.de/event/holiday-on-ice-mirage-merkur-ostseehalle-20995028/.
It was captured in Chrome on 2026-09-21 at 16:59:32 UTC after opening
**Saalplanbuchung** and waiting for the map to load.

The fixture retains the site's public event metadata, category configuration,
status classes, legend colours and all 94 block IDs/states. Scripts unrelated to
parsing, tokens, hidden inputs, session/tracking data, SVG geometry and other
unneeded markup were removed. A minimal JSON wrapper holds the original embedded
metadata values. Parsing the minimized fixture was checked against the original
full captured DOM: every output field except the processing timestamp matched.
This file is parsing evidence, not a page intended to render or run as a website.

`holiday_on_ice.expected.json` records that snapshot's expected parsed values;
`scraped_at` is tested separately because it changes on every parse. The five
prices were also checked against the visible ticket list. The snapshot has 37
available and 57 unavailable map sections. Availability can change on the live
site without changing these regression expectations.

The other saved HTML files are explicitly synthetic regression cases:

- `edge_cases.html`: German thousands separators, mixed ticket statuses, empty
  ticket-type lists, category-specific unavailable rows, newer linked-area maps,
  grey sections that still have a hover class, and unknown map colours.
- `missing_fields.html`: absent venue/prices/status, a date without a timezone,
  and a map advertised but not rendered.
- `malformed.html`: invalid JSON and unexpected field types.
- `no_map.html`: a complete event without an interactive seating map.

Every fixture is included in the ZIP and ready to track in Git. Tests use these
local files; they do not contact EVENTIM. The separate bridge integration test
uses only a temporary loopback server on this computer.
