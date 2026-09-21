# Assumptions audit

Review date: 2026-09-19. Reviewed commit: `9ebeec8`.

Every implicit premise the pipeline relies on, with a verdict and the evidence used to
reach it. Companion to [review-findings.md](review-findings.md), which lists the defects.

Verdicts: **Holds** — tested, no action. **Caveat** — true but narrower than the code or
prose implies. **Broken** — false as relied upon.

Method: the pipeline was re-run and reproduced `data/processed/ward_zoning_shares.csv` to
within 7e-15, so every measurement below describes the data behind the committed output.
The Data Portal was unreachable during the first pass (HTTP 503 across the whole domain),
so section A was initially verified against Socrata's documentation and then re-checked
against the live API on 2026-09-20.

## A. Data acquisition

| # | Assumption | Verdict | Evidence |
|---|---|---|---|
| A1 | `dj47-wfun` and `p293-wvbd` are the intended datasets | Holds | Confirmed as Zoning Districts (current) and Wards (2023-) |
| A2 | The "current" dataset holds only live records, one per district | Holds | 0 duplicate `objectid` or `globalid`; `edit_statu`, `zoning_rel`, `override_c`, `case_type` wholly null; `override_r` is `'0'` for all 14,986 rows |
| A3 | The CRS of the incoming data is known | Holds; now read rather than assumed | The portal declares `urn:ogc:def:crs:OGC:1.3:CRS84` in the response's top-level `crs` key, and documents that member in its GeoJSON format reference. `fetch_geojson` uses the declared value and falls back to `SOURCE_CRS` only when the key is absent, which RFC 7946 permits since it dropped the member and fixed GeoJSON to WGS84. Switching from the hardcoded value left every output byte-identical. |
| A4 | `$limit`/`$offset` paging without `$order` returns each row exactly once | Holds in fact, unguaranteed by contract | Tested live 2026-09-20: paging with and without `$order` both returned 14,986 rows, 0 duplicates, identical `objectid` sets, matching `count(*)`. Socrata guarantees no ordering, so this is correct by luck. `$order=:id` costs nothing. H4, downgraded from broken |
| A5 | A page shorter than `PAGE_SIZE` means the dataset is exhausted | Holds in fact; unguarded in general | A full live download returns 14,986 features against a `count(*)` of 14,986, so no page came back short early. Any partial page would still end the loop silently and no assertion would catch it. H5 |
| A6 | 5,000 is the API's per-request cap | **Broken** | Default `$limit` is 1,000; SODA 2.0 maximum is 50,000; 2.1 and 3.0 have none. 5,000 is self-imposed. L1 |
| A7 | Plain `.json` returns attributes only, no geometry | **Broken** | Both datasets return geometry as a nested `the_geom` column on `.json`. Separately, `.json` omits null-valued fields per row (zoning: 13 keys returned against 24 `.geojson` properties, 12 null) so one `.json` row under-reports the schema. Both claims were wrong in `explore_api.py`'s comments; corrected there |
| A8 | The response always contains a `features` key | Caveat | `page["features"]` raises a bare `KeyError` otherwise. `raise_for_status()` caught the 503 seen in review; a 200 with an error body would not be. L3 |

## B. Coverage and completeness

| # | Assumption | Verdict | Evidence |
|---|---|---|---|
| B1 | Ward polygons do not overlap each other | Holds exactly | Sum of areas 231.4148 sq mi, union 231.4148, excess 0.00000 |
| B2 | Zoning polygons do not overlap each other, i.e. PDs replace base zoning rather than stacking on it | Holds | Self-overlap 0.002 sq mi out of 231.4. This is what keeps the denominator from inflating |
| B3 | All 50 wards are present and each has zoning | Holds | 50 ward rows, all 1–50, every ward represented in the overlay |
| B4 | Zoning tiles the city with no gaps | Caveat | 0.700 sq mi is inside a ward but unzoned, and unevenly spread: Ward 44 loses 5.08% of its area, Ward 41 2.71%, Ward 4 0.73%, Ward 46 0.55%, Ward 50 0.51%. Silently dropped from the ward denominator, so "% of zoned land" is not "% of ward area". M2 |
| B5 | Zoning lying outside ward boundaries is negligible | Holds | 0.636 sq mi, and it only reaches the citywide row. M1 |
| B6 | The 50 ward polygons are the whole city | Holds | Union 231.4 sq mi, consistent with Chicago's municipal area |

## C. Geometry and projection

| # | Assumption | Verdict | Evidence |
|---|---|---|---|
| C1 | `EPSG:3435` is correct for measuring area in Chicago | Holds, strongly | Computed areas match the dataset's own `shape_area` field at a ratio of 1.00000 at both the 5th and 95th percentile across all 14,982 non-null polygons |
| C2 | Geometries are valid enough for `overlay` | Caveat | 119 invalid and 4 empty geometries. Measured impact is nil: `make_valid()` shifts total area by 0.00000 sq mi and the 9 geometries `overlay` drops are degenerate slivers. Unguarded, and the resulting warning is ignored on every run. M8 |
| C3 | Planar polygon area measures **land** | **Broken** for water | River surface sits inside zoning polygons: Wolf Point river water in `PD 98`, Goose Island's east channel in `PMD 3`, Bubbly Creek inside an `RS-3` polygon, i.e. open water counted as single-family land. Lake Michigan is correctly excluded, being neither zoned nor in any ward. M4 |
| C4 | MultiPolygon inputs need no special handling | Holds | All 14,986 zoning and 50 ward features are MultiPolygon; `.area` sums parts correctly |

## D. Classification

| # | Assumption | Verdict | Evidence |
|---|---|---|---|
| D1 | The leading alpha run of `zone_class` determines the category | Holds | All 1,525 distinct values enumerated. The malformed ones (`RM4.5`, `RM5.5`, `RM4-.5`, `PMD13`) all resolve correctly |
| D2 | `zone_type` would be a more authoritative classifier than regex | **False**, so the current approach is right | `zone_type=1` mixes B, C, DS, PD, RM, RT; `zone_type=4` mixes B, C, DR, RM, RS, RT. It is not a use taxonomy |
| D3 | `RS` means apartments and condos are prohibited | Holds | Chicago Cityscape confirms RS-1/2/3 "prohibit new apartments and condos", with a narrow RS-3 block-context exception |
| D4 | "Single-Family Only" is an accurate label for RS | Caveat, overstates | RS-3 permits two-flats at 2,500 sq ft per unit, so on a 5,000 sq ft lot, or 1,500 sq ft per unit under the 17-2-0303-B block-context reduction. RS-2 and RS-3 have permitted ADUs since 2021. The CSV's own `Apartments & condos not allowed (RS)` is the accurate wording. M5 |
| D5 | `RT-3.5` allows apartments | Holds | Permits two-flats, townhouses and low-density apartment buildings |
| D6 | All `C*` districts allow apartments | **Broken**, but inherited | C3 (Commercial, Manufacturing and Employment) permits no housing; it is a buffer against residential encroachment beside M and PMD districts. C1 and C2 do permit units above the ground floor. 77 polygons, 0.16% of land. The source map groups `C` whole, so the code is faithful to its citation; correcting it means diverging from the source deliberately. H2 |
| D7 | `DS` allows no residential | **Broken**, and inherited | Downtown Service carries a residential density standard (400 sq ft per unit, 300 efficiency, 200 SRO) and a 30 ft setback for floors containing dwelling units, so it does permit housing. `DS` is absent from the source map's allowed list too, so the code is faithful to its citation; correcting it means diverging from the source, as with D6 in the opposite direction. H3 |
| D8 | Every `PD *` value is an ordinary negotiated planned development | Holds; the label is right, the ward total is what skews | `PD 0` is O'Hare (10.32 sq mi; contains the FAA reference point, Terminal 2, the 10L/28R runway midpoint). A legitimate PD under the 1964-01-23 Airport Planned Development, so correctly classified. But it is 61.7% of Ward 41's denominator, moving that ward's single-family share from 26.0% to 67.8% and its rank from 34th to 6th of 50. Confined to Ward 41, and both reports now carry a footnote saying so. H1 |
| D9 | Unrecognized prefixes belong in "no residential allowed" | **Broken** as a default | The fallthrough is a guess printed as fact; a new or renamed code is absorbed with no signal. M7 |
| D10 | Base `zone_class` determines what can be built | Caveat, unstated | Ignores the TOD/ETOD ordinance, the 2021 ADU ordinance, ARO, landmark districts and overlays, all of which change buildable density without changing `zone_class`. M6 |
| D11 | The four categories are exhaustive and mutually exclusive | Holds by construction | Single prefix test with a fallthrough. See D9 for the cost |
| D12 | The categories reproduce the Chicago Cityscape blog's map (`categorize.py`) | **Verified** | The map was located and read. Its footnote lists the allowed districts as RT, RM, B, C, DR, DC, DX — exactly `ALLOWED_PREFIXES` — and its four categories match `CATEGORY_ORDER`. Its citywide shares (40.7 / 20.9 / 13.3 / 25.0) sit within 0.8 points of this pipeline's (40.3 / 21.3 / 14.1 / 24.3) four and a half years later. M9 |

## E. Aggregation and denominator

| # | Assumption | Verdict | Evidence |
|---|---|---|---|
| E1 | The overlay correctly attributes districts straddling a ward line | Holds | Pieces total 230.717 sq mi against 230.715 expected from `union(zoning) ∩ union(wards)` |
| E2 | Per-ward percentages sum to 100 | Holds | 100 ± 1e-14 across all 50 wards |
| E3 | The "All Chicago" row is the aggregate of the rows beneath it | **Broken** | It sums unclipped zoning while the ward rows sum ward-clipped pieces. RS 40.315% against 40.391% aggregated; PD 14.105% against 14.030%. M1 |
| E4 | Area-weighting is the right weighting | Holds as a choice | Correctly described in the docstring. It does mean park, industrial and airport parcels dominate |
| E5 | "% of zoned land" is a self-evident basis | **Broken**, and it drives the headline | The denominator is all zoned land: POS alone 7.60% (17.59 sq mi), O'Hare 4.46%, M plus PMD 16.2%. So "40.3% single-family" is a share of all land. The figure usually quoted in this debate is share of *residential* land, which this same data gives as 78.5% (93.27 / (93.27+18.54+7.07)) — matching the commonly cited ~79%. Both are legitimate; the report says neither. M3 |
| E6 | A missing (ward, category) pair means 0% | Caveat | `reindex(fill_value=0)` makes "0% of this category" and "no data for this ward" indistinguishable. Harmless now, as all 50 wards have data. Wards 34 and 42 at 0.0% RS are genuine, not artifacts. L11 |

## Summary

Geometry, projection, overlay and arithmetic assumptions hold, several verified against
independent sources. The exposure is concentrated in two places:

1. **Classification** — C3 and DS are wrong against the ordinance (D6, D7), the fallthrough
   default is a guess (D9), the RS label overstates (D4), and only base zoning is modeled
   (D10).
2. **Unstated denominator semantics** — what is in it (parks, airport, river water), what
   is silently out of it (unzoned gaps, unevenly by ward), and which basis the headline
   percentage uses (E5, B4, C3, M1).

Nothing found changes the committed numbers. The numbers are what the code says they are.
The exposure is that one row (Ward 41) and one headline percentage (E5) read as the opposite
of what the underlying land supports.

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
