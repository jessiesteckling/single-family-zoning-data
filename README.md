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

## Categories

The four-way breakdown follows Steven Vance's map *Where apartments are allowed in
Chicago* (May 2022; zoning data as of March 2022; groupings and calculations by the author
using PostGIS). The prefix groupings in `src/categorize.py` come from it directly — the
map's own footnote reads "Apartments & condos are allowed in RT, RM, B, C, DR, DC, and DX
zoning districts."

Citywide shares track closely four and a half years apart, which is the main external check
on this pipeline:

| Category | Vance, Mar 2022 | This repo, Sep 2026 |
|---|---|---|
| Apartments & condos not allowed (RS) | 40.7% | 40.3% |
| Apartments & condos allowed | 20.9% | 21.3% |
| Planned Developments | 13.3% | 14.1% |
| All other zones, no residential allowed | 25.0% | 24.3% |

One caveat inherited from the source: grouping every `C` district as apartments-allowed
includes C3, which permits no housing. That follows the map rather than the zoning
ordinance. Vance also labels the third category "Unknown which allow residential", which is
more precise than the bare "Planned Development" used here.

This repo (code, analysis, and README) was generated with [Claude Code](https://claude.com/claude-code).
