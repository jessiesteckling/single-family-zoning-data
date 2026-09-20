# single-family-zoning-data


Goal: make a chart showing the percentage of land zoned for each use for each ward in Chicago.

## Results

Checked in and ready to read — no setup, just open them:

- **[Share of all zoned land](output/ward_zoning_report.md)** — one row per ward, four
  categories.
- **[Share of residentially zoned land](output/ward_zoning_report_residential.md)** — the
  same three residential categories renormalized, with zones that allow no housing (M, POS,
  PMD, T) dropped from the denominator. The better read on a ward's single-family share,
  since it is not diluted by however much industrial land or parkland the ward happens to
  hold.

The per-ward numbers behind both:
[data/processed/ward_zoning_shares.csv](data/processed/ward_zoning_shares.csv).

## Rebuilding

Only needed to pick up new data — the reports above are current as committed.
`python3 main.py` rewrites both of them and the CSV. Its first run downloads to
`data/raw/`; later runs read that cache and do not re-fetch.

New to this data? Run `python3 local_scripts/explore_api.py` first — it prints example requests/responses from the Chicago Data Portal API so you can see the raw data shape before it's processed.

## Data sources

- [Boundaries – Zoning Districts (current)](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun) — one polygon per zoning district, with a `zone_class` code (e.g. `RS-1`). No ward info.
- [Boundaries – Wards (2023-)](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd) — one polygon per ward. No zoning info.

Neither dataset knows about the other, so a spatial overlay (`src/analyze.py`) intersects the two: it geometrically slices every zoning polygon along ward boundary lines, so each resulting piece is tagged with both its zoning category and the ward it actually falls in. That handles zoning districts that straddle a ward line without misattributing area to the wrong side.

## Categories

The four-way breakdown follows the map *Where apartments are allowed in Chicago*, from the
Chicago Cityscape blog post [Apartments & condos are banned in most of Chicago](https://blog.chicagocityscape.com/how-much-of-chicago-bans-apartments-b6c5b68db2fb) (May 2022; zoning
data as of March 2022; groupings and calculations done in PostGIS). The prefix groupings in
`src/categorize.py` come from it directly — the map's own footnote reads "Apartments & condos are allowed in RT, RM, B, C, DR, DC, and DX
zoning districts."

Citywide shares track closely four and a half years apart, which is the main external check
on this pipeline:

| Category | Cityscape, Mar 2022 | This repo, Sep 2026 |
|---|---|---|
| Apartments & condos not allowed (RS) | 40.7% | 40.3% |
| Apartments & condos allowed | 20.9% | 21.3% |
| Planned Developments | 13.3% | 14.1% |
| All other zones, no residential allowed | 25.0% | 24.3% |

One caveat inherited from the source: grouping every `C` district as apartments-allowed
includes C3, which permits no housing. That follows the map rather than the zoning
ordinance.

The map uses the same "Planned Developments" label this report does, paired with a second
line reading "Unknown which allow residential". The label is an accurate description of the
zoning — every polygon in the column is a planned development. The gloss is what that means
for the question being asked, since a PD's residential rules are set per ordinance rather
than by the district.

This repo (code, analysis, and README) was generated with [Claude Code](https://claude.com/claude-code).
