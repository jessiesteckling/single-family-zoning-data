# Code review findings

Review date: 2026-09-19. Reviewed commit: `9ebeec8`.

Method: the pipeline was re-run from the cached raw data and reproduced
`data/processed/ward_zoning_shares.csv` to within 7e-15. Geometry and area math were
validated against the zoning dataset's own `shape_area` attribute. Zoning-code
classifications were checked against the Chicago Zoning Ordinance and secondary
references. Dataset identities were confirmed against the Chicago Data Portal.

Limitation: the Data Portal returned HTTP 503 for the entire domain during this review,
so live API calls were not exercised. API behavior was verified from Socrata's
documentation and from the cached 14,986-feature response.

## Verified correct

These were tested and hold. Listed so they are not re-litigated.

- Dataset IDs. `dj47-wfun` is Boundaries – Zoning Districts (current); `p293-wvbd` is
  Boundaries – Wards (2023-).
- Projection and area math. Computed `EPSG:3435` areas match the dataset's `shape_area`
  field at a ratio of 1.00000 at the 5th and 95th percentile across all 14,982 non-null
  polygons.
- Overlay attribution. Intersected pieces total 230.717 sq mi against 230.715 expected
  from `union(zoning) ∩ union(wards)`. Per-ward percentages sum to 100 ± 1e-14.
- No double counting. Zoning polygons self-overlap by 0.002 sq mi out of 231.4. Ward
  polygons do not overlap at all (sum of areas equals union to 5 decimal places).
- Dataset currency and uniqueness. No duplicate `objectid` or `globalid`. `edit_statu`,
  `zoning_rel`, `override_c` and `case_type` are wholly null, so there are no superseded
  records. Max `edit_date` is 2026-08-31.
- External corroboration. RS / (RS+RT+RM) = 93.27 / 118.88 = 78.5%, matching the commonly
  cited figure of roughly 79% of Chicago residential land zoned single-family-only.
- `RT-3.5` in the apartments-allowed bucket is correct; it permits two-flats, townhouses
  and low-density apartment buildings.
- Wards 34 and 42 at 0.0% RS are genuine, not a division artifact.
- `zone_type` was evaluated as a replacement for regex prefix matching and rejected. It is
  not a use taxonomy: `zone_type=1` mixes B, C, DS, PD, RM, RT and `zone_type=4` mixes
  B, C, DR, RM, RS, RT. Prefix matching on `zone_class` is the correct approach.

## High

### H1. O'Hare puts Ward 41 in the wrong half of the chart

`src/categorize.py:14`, `src/report.py:22`

One polygon carries `zone_class = "PD 0"`, `pd_num = 0`, `case_numbe = 0`, covering
10.32 sq mi (6,604 acres). It contains the FAA airport reference point, Terminal 2 and the
10L/28R runway midpoint, and excludes Rosemont and Norridge: it is O'Hare. Chicago
Cityscape independently labels this record "O'Hare Airport (ORD) (PD 0)".

The classification is correct and must not be changed. O'Hare is genuinely a planned
development — the "Airport Planned Development" of City Council ordinance 1964-01-23, and
the zoning ordinance provides that land within the Airport Layout Plan "shall be deemed to
be included within, and subject to all the applicable provisions of" it.

The defect is that the airport is 61.7% of Ward 41's denominator, which moves every figure
in that row:

| Ward 41 | As published | Excluding `PD 0` |
|---|---|---|
| Single-family only | 26.0% | 67.8% |
| Apartments allowed | 4.0% | 10.5% |
| Planned development | 63.8% | 5.6% |
| Other | 6.2% | 16.1% |

Single-family rank moves from **34th of 50 to 6th of 50**. As published, Ward 41 sits
beside Ward 49 (25.2%), Ward 11 (27.0%) and Ward 48 (27.1%) — Rogers Park, Bridgeport,
Edgewater. On its developable land it sits beside Ward 23 (67.8%), Ward 31 (68.8%) and
Ward 45 (70.2%) — the bungalow belt, which is what Edison Park and Norwood Park are. A
reader comparing wards draws the opposite conclusion from the truth.

This is confined to one ward. `PD 0` is 61.7% of Ward 41; the next-largest single-PD
concentration anywhere is `PD 610` at 23.0% of Ward 13, then `PD 43` at 12.0% of Ward 5.
Nothing else distorts a row.

Fix: footnote Ward 41, or report it both ways. Do not move `PD 0` to `OTHER` — that would
be less accurate than current behavior. The citywide row is a weaker case: 32% of that
column being one airport is worth a note, but it misranks nothing.
### H2. `C3` is classified as apartments-allowed; C3 permits no housing

`src/categorize.py:16`

C3 is Commercial, Manufacturing and Employment, intended as a buffer against residential
encroachment next to M and PMD districts. C1 and C2 permit dwelling units above the
ground floor; C3 permits none. The blanket `"C"` prefix catches all three.

77 polygons, 0.38 sq mi, 0.16% of city land. Small in area, but wrong, and `_legend()`
advertises `C` wholesale so the report states it as fact.

Reclassified as inherited, not a transcription slip: the source map groups every `C`
district as apartments-allowed, so the code is faithful to what it cites. Fixing it means
deliberately diverging from the source, which is a choice to make explicitly rather than
silently. Noted as a caveat in the README in the meantime.

### H3. `DS` is reported as no-residential; DS permits dwelling units

`src/report.py:33`

Downtown Service districts carry a residential density standard (400 sq ft per dwelling
unit, 300 for efficiency, 200 for SRO) and a 30 ft setback for floors containing dwelling
units. `DS` is absent from `ALLOWED_PREFIXES` so it falls through to `OTHER`, and the
legend names it explicitly as an example of zoning where no residential is allowed.

39 polygons, 0.59 sq mi, 0.26% of land. Low materiality, but a printed false claim.

Partly addressed: `DS` has been dropped from the legend's list of no-residential examples,
so the report no longer asserts it. The classification itself is unchanged — `DS` still
falls through to `OTHER` — so this stays open.

### H4. Paginated fetch omits `$order` — latent, does not currently reproduce

`src/fetch_data.py:25-28`

Downgraded to medium severity on 2026-09-20 after live verification. Originally filed as
high on the strength of Socrata's documentation alone, because the portal was returning
503 for the whole domain during the first review.

Socrata's documentation: "The order of the results of a query are not implicitly ordered,
so if you're paging, make sure you provide an `$order` clause or at a minimum
`$order=:id`. That will guarantee that the order of your results will be stable as you
page through the dataset."

Tested against the live endpoint, paging the zoning dataset both ways, comparing `objectid`
sets:

| Run | Fetched | Unique | Duplicates |
|---|---|---|---|
| No `$order`, as the code does now | 14,986 | 14,986 | 0 |
| `$order=:id` | 14,986 | 14,986 | 0 |

Both match `$select=count(*)` = 14,986 exactly, and neither run contains a row the other
lacks. So the committed output is not affected, and no data was lost to this.

It remains worth fixing. The vendor gives no ordering guarantee, so the current behavior is
correct by luck rather than by contract, and it could break under concurrent writes to the
dataset or a backend change — silently, since nothing would detect it. `&$order=:id` costs
nothing.

### H5. A short page is treated as end-of-data, so truncation is silent

`src/fetch_data.py:34`

`if len(page_features) < PAGE_SIZE: break` assumes any short page is the last. A throttled
response, a lowered export cap or a partial page ends the loop, and the pipeline then
produces plausible percentages from a truncated dataset with no warning.

Verified 2026-09-20 that this did not bite: `$select=count(*)` returns 14,986 and a full
live download yields exactly 14,986 features. The risk is latent, not realised.

Still worth an assertion, since that check is the only thing that would ever surface it.
Compare the assembled feature count against `$select=count(*)` before returning.

### H6. README claims the run fetches current data; it does not — resolved

`README.md:6`, `src/fetch_data.py:19-20`

Originally: `fetch_geojson` returned the cache unconditionally when the file existed, with
no TTL, no `--refresh` flag and no invalidation path, so a clone downloaded once and never
updated again.

Resolved 2026-09-20 by removing caching outright. `fetch_geojson` now takes only a dataset
id, downloads on every run and parses in memory via `GeoDataFrame.from_features`; nothing
is written to or read from disk. `data/raw/` and its gitignore entry are gone. A run costs
about 12 seconds and 40 MB and requires network access, which is the accepted trade.

Verified the change is behaviour-preserving: all three outputs are byte-identical to the
committed ones when rebuilt from a live download. This also resolves L10, since the
function now has one job.

### H7. The stated deliverable, a chart, does not exist

CLAUDE.md opens with "producing a chart showing the percentage of land zoned for each use,
broken down by ward"; `README.md:4` repeats it. The pipeline emits a markdown table.

A stale `src/__pycache__/chart.cpython-311.pyc` exists for a `chart.py` that was never
committed, so the chart step appears lost rather than deliberately dropped. CLAUDE.md
directs chart work to the `dataviz` skill.

## Medium

### M1. The "All Chicago" row is not the aggregate of the table it heads

`src/analyze.py:59-72`

`compute_citywide_category_shares` sums unclipped zoning polygons; the ward rows sum
ward-clipped pieces. RS reads 40.315% against 40.391% aggregated from the table; PD reads
14.105% against 14.030%.

Deriving the citywide row from `pieces` fixes the mismatch, drops the 0.636 sq mi of
zoning lying outside all wards, and removes the duplicated `categorize` and `to_crs` work.

### M2. Unzoned gaps are dropped from ward denominators, unevenly

0.700 sq mi lies inside a ward but carries no zoning polygon, and it is not evenly
distributed:

| Ward | % of ward area unzoned |
|---|---|
| 44 | 5.08 |
| 41 | 2.71 |
| 4 | 0.73 |
| 46 | 0.55 |
| 50 | 0.51 |

Consequently "% of zoned land" is not "% of ward area". The report does not say which it
reports.

### M3. The denominator basis is unstated and materially changes the headline

The denominator is all zoned land. POS alone is 7.60% (17.59 sq mi), O'Hare a further
4.46%, M plus PMD 16.2%. So "40.3% single-family" is a share of all land.

The figure usually quoted in this debate is the share of residential land, which this same
data gives as 78.5%. Both are legitimate. The report must state which one it shows.

Partly addressed: `output/ward_zoning_report_residential.md` now reports the three
residential categories renormalized with M, POS, PMD and T dropped, and states its basis in
the legend. Citywide single-family reads 53.3% on that basis against 40.3% on all land. Note
the residential table still keeps PD in the denominator, so Ward 41 is still 68.0% planned
development there and its single-family share still reads 27.7% rather than the 67.8% its
non-airport land supports. H1 is unaffected by this change.

### M4. River surface water is counted as land, including as RS

Water inside zoning polygons is measured as area: Wolf Point river water falls in `PD 98`,
Goose Island's east channel in `PMD 3`, and Bubbly Creek falls inside an `RS-3` polygon —
open water counted as single-family land.

Lake Michigan is correctly excluded, being neither zoned nor inside any ward. The effect
is small, but "percentage of land" in CLAUDE.md and the README is imprecise.

### M5. The "Single-Family Only" column label overstates RS

`src/report.py:20`

RS-3 permits two-flats, subject to 2,500 sq ft per unit — so a 5,000 sq ft lot, or 1,500
sq ft per unit under the 17-2-0303-B block-context reduction. RS-2 and RS-3 have permitted
ADUs since 2021.

The category constant, `Apartments & condos not allowed (RS)`, is accurate. The relabel in
`report.py` is what loses precision. Cityscape confirms RS-1/2/3 prohibit new apartments
and condos, with a narrow RS-3 exception.

### M6. Only base zoning is modeled, and that limit is unstated

Classification reads `zone_class` alone. It therefore ignores the TOD/ETOD ordinance, the
2021 ADU ordinance, ARO, landmark districts and overlay districts, all of which change
buildable density without changing `zone_class`. State this as a scope limit.

### M7. Unrecognized prefixes silently become "no residential allowed"

`src/categorize.py:34`

The fallthrough branch is a guess presented as a fact; a new or renamed code is absorbed
with no signal. The existing malformed values (`RM4.5`, `RM5.5`, `RM4-.5`, `PMD13`) happen
to resolve correctly, which masks the risk.

This is the Open/Closed point in CLAUDE.md. Enumerate known prefixes and either raise or
surface an explicit `Unclassified` bucket.

### M8. Invalid and empty geometries are neither repaired nor reported

`src/analyze.py:30-34`

119 invalid and 4 empty geometries. Every run emits
`UserWarning: keep_geom_type=True in overlay resulted in 9 dropped geometries`.

Measured impact is nil: `make_valid()` shifts total area by 0.00000 sq mi and the 9 dropped
geometries are degenerate slivers. The concern is that it is unguarded, GEOS can throw on
invalid input as the data changes, and an ignored warning will hide the next real one.

### M9. The cited classification source cannot be verified

`src/categorize.py:1-4`

Resolved 2026-09-20. The map itself was located and read. Its footnote states "Apartments
& condos are allowed in RT, RM, B, C, DR, DC, and DX zoning districts", which is exactly
`ALLOWED_PREFIXES`, and its four categories match `CATEGORY_ORDER`. The code is a faithful
transcription. Attribution with date and data vintage is now in the README and the module
docstring.

The map is also the strongest external check on the pipeline. Citywide shares, four and a
half years apart:

| Category | Cityscape, Mar 2022 | This repo, Sep 2026 |
|---|---|---|
| Not allowed (RS) | 40.7% | 40.3% |
| Allowed | 20.9% | 21.3% |
| Planned Developments | 13.3% | 14.1% |
| All other | 25.0% | 24.3% |

Within 0.8 points on every category, with the drift in the direction the intervening zoning
changes would predict.

### M10. No tests

Originally: no test directory existed, though CLAUDE.md asks for "small, testable functions
for data transformations ... so they can be verified independently of the chart output".

Resolved: `tests/unit/` holds 29 tests over mock portal responses, run with
`python3 -m unittest discover -s tests -t .` and verified to pass with sockets disabled.
The fixtures are a two-ward toy city whose middle district straddles the ward line, so the
overlay's defining behaviour — splitting a district between the wards it falls in rather
than assigning it to one — is asserted directly.

### M11. No dependency manifest — resolved

Originally: nothing declared geopandas, pandas, requests or a GeoJSON engine. `fiona` is
not installed in the working environment; the code runs only because geopandas 1.x defaults
to pyogrio.

Resolved by `Pipfile` / `Pipfile.lock`, which declare the three direct imports
(`geopandas`, `pandas`, `requests`) and lock the full transitive set, pyogrio included.
`python_version` is 3.11, the floor `pandas` 3.x requires.

## Low

| ID | Location | Finding |
|---|---|---|
| L1 | `local_scripts/explore_api.py` | Resolved. The comment claimed a request "caps out (5,000 rows/page here)"; Socrata's default `$limit` is 1,000, SODA 2.0's maximum is 50,000, and 2.1/3.0 have none. Two further claims in that file were also wrong about the API — that plain `.json` returns no geometry, and that one `.json` row shows the schema. All three corrected, and the response print cap is now the named `MAX_PRINT_CHARS` rather than a bare `[:1500]`. |
| L2 | `main.py` | `PROCESSED_DIR` and `OUTPUT_DIR` are CWD-relative, so running from anywhere but the repo root writes the CSV and both reports into a new tree rather than updating the committed ones. Anchor to `Path(__file__).parent`. |
| L3 | `src/fetch_data.py:32` | `page["features"]` raises a bare `KeyError` on an error payload. `raise_for_status()` does catch the 503 seen during review, but a 200 with an error body would not be. |
| L4 | `src/report.py:19-24` | Category names differ between the CSV (`Apartments & condos not allowed (RS)`) and the report (`Single-Family Only`), so the two artifacts cannot be joined on category without a lookup. |
| L5 | `src/report.py:42` | `pivot.round(1)` is dead; every value is re-formatted by `f"{v:.1f}%"`. |
| L6 | `src/analyze.py:68-70` | `groupby("category").geometry.apply(lambda geoms: geoms.area.sum())` is roundabout and leaves `Name: geometry` on the result. Summing an `area` column is clearer. |
| L7 | `src/analyze.py:21,27,64,66` | The `zoning` and `wards` parameters are rebound to reprojected copies. Harmless, since `.copy()` is called, but it obscures that the inputs are untouched. |
| L8 | `src/constants.py` | Resolved. `PROJECTED_CRS` sat in the analysis module while other configuration sat in `main.py`; dataset ids, API settings, both CRSs, the unit conversion, the O'Hare zone class and the output paths now share one annotated module. The zoning taxonomy stays in `categorize.py` and the column labels in `report.py`, since those are what those modules define. |
| L9 | `src/__pycache__/` | Stale `.pyc` files including `chart.cpython-311.pyc` for a module that does not exist. Untracked; cruft only. |
| L10 | `src/fetch_data.py` | Resolved with H6. `fetch_geojson` conflated HTTP paging, cache management and parsing; caching is gone, so it now only pages and parses. |
| L11 | `src/analyze.py:46-55` | `reindex(fill_value=0)` makes "0% of this category" and "no data for this ward" indistinguishable. Harmless now, since all 50 wards have data. |

## Suggested fix order

1. H1. Ward 41 is misranked by 28 places on the headline metric. Disclosure, not
   reclassification.
2. H4 and H5. Neither is realised — both verified clean against the live API on
   2026-09-20 — but they are the only guards on input integrity, and both fixes are one
   line.
3. H2, H3 and M1. Classification errors the report asserts as fact, plus the citywide
   denominator mismatch.
4. M3, M2, M4 and M5. Denominator and label semantics — cheap to state, and the reason
   40.3% is easy to misread.
5. M10. Tests for `categorize` pinning each prefix to its expected bucket.
6. H7 is a scope decision. The repo's stated goal is a chart.

## References

- [Boundaries – Zoning Districts (current)](https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun)
- [Boundaries – Wards (2023-)](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd)
- [Socrata: the ORDER clause](https://dev.socrata.com/docs/queries/order.html)
- [Socrata: the LIMIT clause](https://dev.socrata.com/docs/queries/limit.html)
- [Chicago Zoning Ordinance, chapter 17-2](https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2681086)
- [2nd City Zoning: C3-3](https://secondcityzoning.org/zone/c3-3/), [DS-3](https://secondcityzoning.org/zone/ds-3/), [RS-3](https://secondcityzoning.org/zone/rs-3/), [RT-3.5](https://secondcityzoning.org/zone/rt-3.5/)
- [Chicago Cityscape: exclusionary zoning](https://help.chicagocityscape.com/exclusionaryzoning)
- [Chicago Cityscape: Apartments & condos are banned in most of Chicago](https://blog.chicagocityscape.com/how-much-of-chicago-bans-apartments-b6c5b68db2fb) — the source of the category breakdown
- [Chicago Cityscape: O'Hare Airport (ORD) (PD 0)](https://www.chicagocityscape.com/maps/index.php?place=pdchicago-0)
- [Chicago Cityscape: planned developments in Chicago](https://help.chicagocityscape.com/planneddevelopments)
