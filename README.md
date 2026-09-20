# single-family-zoning-data


Goal: make a chart showing the percentage of land zoned for each use for each ward in Chicago.

Run `python3 main.py` to regenerate the outputs:

- [output/ward_zoning_report.md](output/ward_zoning_report.md) — share of all zoned land,
  four categories.
- [output/ward_zoning_report_residential.md](output/ward_zoning_report_residential.md) —
  the same three residential categories renormalized with non-residential zones (M, POS,
  PMD, T) dropped from the denominator. Better basis for reading a ward's single-family
  share, since it is not diluted by however much industrial land or parkland the ward holds.

The first run downloads to `data/raw/`; later runs read that cache and do not re-fetch.

New to this data? Run `python3 local_scripts/explore_api.py` first — it prints example requests/responses from the Chicago Data Portal API so you can see the raw data shape before it's processed.

## Data sources

- [Boundaries – Zoning Districts (current)](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun) — one polygon per zoning district, with a `zone_class` code (e.g. `RS-1`). No ward info.
- [Boundaries – Wards (2023-)](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd) — one polygon per ward. No zoning info.

Neither dataset knows about the other, so a spatial overlay (`src/analyze.py`) intersects the two: it geometrically slices every zoning polygon along ward boundary lines, so each resulting piece is tagged with both its zoning category and the ward it actually falls in. That handles zoning districts that straddle a ward line without misattributing area to the wrong side.

This repo (code, analysis, and README) was generated with [Claude Code](https://claude.com/claude-code).
