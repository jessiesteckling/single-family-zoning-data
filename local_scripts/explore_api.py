"""Standalone demo of the Chicago Data Portal API used by this project. Not part
of the main pipeline -- run it to see what a request looks like and what comes
back, before it gets turned into GeoDataFrames.

One API, two datasets: zoning districts and ward boundaries.
Both accept the same query syntax, so `tour` runs the same requests against
either one.

Run: python3 local_scripts/explore_api.py

Docs
----
Query reference, for the $ params used below:
    https://dev.socrata.com/docs/queries/
The $order page is where the portal states that paging without it gives no stable
row order, which is why the pagination pattern at the bottom passes $order=:id.
Response formats, .json against .geojson:
    https://dev.socrata.com/docs/endpoints.html
App tokens, should these unauthenticated requests start getting throttled:
    https://dev.socrata.com/docs/app-tokens.html

Column meanings are not in the API docs. Every column of both datasets ships
with an empty description, so zone_class and zone_type are defined only in the
zoning ordinance:
    https://codelibrary.amlegal.com/codes/chicago/latest/chicagozoning_il/0-0-0-48006
    https://gisapps.cityofchicago.org/zoning/   (official map, for spot checks)
That is why src/categorize.py has to carry its own prefix table.

Dataset metadata, including when the rows were last updated:
    https://data.cityofchicago.org/api/views/dj47-wfun.json
    https://data.cityofchicago.org/api/views/p293-wvbd.json
"""

import json

import requests

BASE_URL = "https://data.cityofchicago.org/resource"

# Boundaries - Zoning Districts (current)
# https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun
ZONING_DATASET_ID = "dj47-wfun"

# Boundaries - Wards (2023-)
# https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd
WARDS_DATASET_ID = "p293-wvbd"

# Responses are printed for reading, not parsing. Both endpoints return geometry,
# and one polygon runs to tens of thousands of characters of coordinates, so cap
# what reaches stdout.
MAX_PRINT_CHARS = 1500
TIMEOUT_SECONDS = 30


def get(url: str) -> object:
    response = requests.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def show(title: str, url: str, max_chars: int = MAX_PRINT_CHARS) -> None:
    """Print a request and its response, truncated to `max_chars`."""
    print(f"\n=== {title} ===")
    print(f"GET {url}")
    body = json.dumps(get(url), indent=2)
    print(body[:max_chars])
    if len(body) > max_chars:
        print(f"... truncated: {len(body) - max_chars:,} of {len(body):,} chars omitted")


def show_fields(dataset_id: str, label: str) -> None:
    """Compare the fields .json and .geojson return for the same row.

    Two things to know before trusting either as a schema. Plain .json returns
    geometry too, as a nested `the_geom` column -- it is not attributes-only.
    And .json drops null-valued fields per row, while .geojson spells them out,
    so a single .json row under-reports the columns that exist.
    """
    print(f"\n=== {label}: fields, .json vs .geojson ===")
    row = get(f"{BASE_URL}/{dataset_id}.json?$order=:id&$limit=1")[0]
    props = get(f"{BASE_URL}/{dataset_id}.geojson?$order=:id&$limit=1")["features"][0][
        "properties"
    ]
    print(f"  .json keys:           {len(row):>3}  {sorted(row)}")
    print(f"  .geojson properties:  {len(props):>3}  (geometry moved to its own member)")
    dropped = sorted(set(props) - set(row))
    print(f"  null, so absent from .json: {len(dropped):>3}  {dropped}")


def tour(dataset_id: str, label: str, group_column: str) -> None:
    """Run the same four requests against any dataset on the portal."""
    # Aggregation, like SQL "SELECT COUNT(*)". Cheap way to size a dataset
    # before downloading it, and the check that a paginated download got
    # everything.
    show(f"{label}: row count", f"{BASE_URL}/{dataset_id}.json?$select=count(*)")

    show_fields(dataset_id, label)

    # .geojson is the shape the pipeline consumes: attributes under
    # "properties", polygon under "geometry".
    show(
        f"{label}: one row as GeoJSON",
        f"{BASE_URL}/{dataset_id}.geojson?$order=:id&$limit=1",
    )

    # $select with $group, like SQL "SELECT x, COUNT(*) ... GROUP BY x".
    # For wards every count is 1, which is itself the answer: one polygon per
    # ward. For zoning it shows which classes dominate.
    show(
        f"{label}: count per {group_column} (top 5)",
        f"{BASE_URL}/{dataset_id}.json"
        f"?$select={group_column},count(*)&$group={group_column}"
        "&$order=count(*) DESC&$limit=5",
    )


def main() -> None:
    tour(ZONING_DATASET_ID, "Zoning districts", group_column="zone_class")
    tour(WARDS_DATASET_ID, "Ward boundaries", group_column="ward")

    # $where filters server-side, like a SQL WHERE clause. "like 'RS%'" matches
    # zone_class values starting with RS; %25 is an encoded % literal.
    show(
        "Zoning districts filtered to RS (single-family) classes",
        f"{BASE_URL}/{ZONING_DATASET_ID}.json"
        "?$select=zone_class&$where=zone_class like 'RS%25'&$limit=3",
    )

    # Pagination: src/fetch_data.py pages with $limit/$offset because $limit
    # defaults to 1,000 (the portal allows up to 50,000) and the zoning dataset
    # has ~15,000 rows. $order=:id keeps the order stable across pages, which
    # the portal requires -- without it rows can repeat or go missing.
    print("\n=== Pagination pattern used for full downloads ===")
    for offset in (0, 5000, 10000):
        print(
            f"{BASE_URL}/{ZONING_DATASET_ID}.geojson"
            f"?$order=:id&$limit=5000&$offset={offset}"
        )
    print("...until a page comes back with fewer than 5000 features.")


if __name__ == "__main__":
    main()
