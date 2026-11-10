# visitor-map-data

Where visitors to [zhangce01.github.io](https://zhangce01.github.io/) come
from. The homepage's globe reads
[`visitors.json`](https://zhangce01.github.io/visitor-map-data/visitors.json)
from this repository's GitHub Pages site, and a workflow here rebuilds and
publishes that file once a day.

- **`visitors.json`** is what the globe draws: per-country totals and
  `[cell, country, visits]` places, where a cell is one degree of latitude by
  one of longitude (about 100 km). Nothing finer is ever recorded.
- **`aggregate.py`** rebuilds it. Each day's visit on the homepage adds one to
  a counter for the visitor's cell at [Abacus](https://abacus.jasoncameron.dev);
  the script reads those counters and adds `seed.json`. Its docstring explains
  how it finds the counters.
- **`seed.json`** is the history from before the counters existed: Google
  Analytics engaged sessions by city, 2023-01-01 to 2026-11-10, rounded to the
  same cells. Engaged sessions leave out the visits that bounce within a few
  seconds, most of which are crawlers.
- **`slots.json`** is the script's memory of which counters it has already
  found.
- **`history.json`** keeps each day's reading of the counters for the last 45
  days. The "in the last 30 days" figure is today's reading minus the one from
  30 days ago, plus what is left of the last 30 days of the Google Analytics
  history (`recent` in `seed.json`), which is let go a day's share per day.
- **`countries.json`** gives each ISO country code a display name and a
  fallback centre (from [mledoze/countries](https://github.com/mledoze/countries)).

Run by hand with `python3 aggregate.py`, or from the Actions tab.
