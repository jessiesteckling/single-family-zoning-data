# single-family-zoning-data


Goal: make a chart showing the percentage of land zoned for each use for each ward in Chicago.

## Results


- **[Share of all zoned land](output/ward_zoning_report.md)** — one row per ward, four
  categories.
- **[Share of residentially zoned land](output/ward_zoning_report_residential.md)** — the
  same three residential categories renormalized, with zones that allow no housing (M, POS,
  PMD, T) excluded.

The per-ward numbers behind both:
[data/processed/ward_zoning_shares.csv](data/processed/ward_zoning_shares.csv).

## Rebuilding

Only needed to pick up new data — the reports above are current as committed.
`make refresh` rewrites both of them and the CSV. It re-downloads both datasets from the
portal every run — about 40 MB, roughly 12 seconds all in — and caches nothing, so a run
always reflects the portal's current state. It needs network access.

`make install` sets up the locked dependencies first, and `make` on its own lists the
targets. Each runs through pipenv; pass `PYTHON=python3` to use an interpreter you have
already set up.

Tests: `make test` — unit tests over literal mock portal responses, no network needed.

New to this data? Run `python3 local_scripts/explore_api.py` first — it prints example requests/responses from the Chicago Data Portal API so you can see the raw data shape before it's processed.

## Data sources

- [Boundaries – Zoning Districts (current)](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun) — one polygon per zoning district, with a `zone_class` code (e.g. `RS-1`). No ward info.
- [Boundaries – Wards (2023-)](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd) — one polygon per ward. No zoning info.

Neither dataset knows about the other, so a spatial overlay (`src/analyze.py`) intersects the two via the `geopandas` library.

## Categories

The four-way breakdown follows the map *Where apartments are allowed in Chicago*, from the
Chicago Cityscape blog post [Apartments & condos are banned in most of Chicago](https://blog.chicagocityscape.com/how-much-of-chicago-bans-apartments-b6c5b68db2fb) (May 2022; zoning
data as of March 2022; groupings and calculations done in PostGIS).

- Apartments & condos not allowed (RS)
- Apartments & condos allowed (RT, RM, B, C*, DR, DX)
- Planned Developments (PD**)
- All other zones, no residential allowed

\* Technically, C3 (a subset of C) doesn't allow residential, but that's an extremely small total land area

\** O'Hare is a Planned Development which significantly impacts the ward 41 numbers


## Methods

This repo was created in part with Claude Code, but heavily proofread.
