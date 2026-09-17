# single-family-zoning-data


Goal: make a chart showing the percentage of land zoned for each use for each ward in Chicago.

Run `python3 main.py` to fetch the latest data and regenerate the output: [output/ward_zoning_report.md](output/ward_zoning_report.md).

New to this data? Run `python3 local_scripts/explore_api.py` first — it prints example requests/responses from the Chicago Data Portal API so you can see the raw data shape before it's processed.

## Data sources

- [Boundaries – Zoning Districts (current)](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun) — one polygon per zoning district, with a `zone_class` code (e.g. `RS-1`). No ward info.
- [Boundaries – Wards (2023-)](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd) — one polygon per ward. No zoning info.

Neither dataset knows about the other, so a spatial overlay (`src/analyze.py`) intersects the two: it geometrically slices every zoning polygon along ward boundary lines, so each resulting piece is tagged with both its zoning category and the ward it actually falls in. That handles zoning districts that straddle a ward line without misattributing area to the wrong side.

This repo (code, analysis, and README) was generated with [Claude Code](https://claude.com/claude-code).
