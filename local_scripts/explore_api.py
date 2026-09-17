"""Standalone demo of the Chicago Data Portal (Socrata/SODA) API used by this
project. Not part of the main pipeline -- just run this to see what a request
looks like and what comes back, before it gets turned into GeoDataFrames.

Run: python3 local_scripts/explore_api.py
"""

import json

import requests

BASE_URL = "https://data.cityofchicago.org/resource"
ZONING_DATASET_ID = "dj47-wfun"  # Boundaries - Zoning Districts (current)
WARDS_DATASET_ID = "p293-wvbd"  # Boundaries - Wards (2023-)


def show(title: str, url: str) -> None:
    print(f"\n=== {title} ===")
    print(f"GET {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2)[:1500])


def main() -> None:
    # 1. Plain .json request -- just the attribute columns (properties),
    #    no geometry. Good for seeing what fields a dataset has.
    show(
        "Zoning districts, plain JSON, no filter (3 rows)",
        f"{BASE_URL}/{ZONING_DATASET_ID}.json?$limit=3",
    )

    # 2. $where lets you filter server-side, like a SQL WHERE clause.
    #    "like 'RS%'" matches zone_class values starting with RS.
    show(
        "Zoning districts filtered to RS (single-family) classes",
        f"{BASE_URL}/{ZONING_DATASET_ID}.json"
        "?$where=zone_class like 'RS%25'&$limit=3",
    )

    # 3. Same dataset, .geojson instead of .json -- properties are the same,
    #    but each row now also carries its polygon "geometry".
    show(
        "Zoning districts as GeoJSON (1 row, includes geometry)",
        f"{BASE_URL}/{ZONING_DATASET_ID}.geojson?$limit=1",
    )

    # 4. Aggregation via $select/$group, like SQL "SELECT x, COUNT(*) GROUP BY x".
    #    This is how the ~15,000-row zoning dataset's category breakdown
    #    was sanity-checked without downloading everything first.
    show(
        "Count of districts per zone_class (top 5)",
        f"{BASE_URL}/{ZONING_DATASET_ID}.json"
        "?$select=zone_class,count(*)&$group=zone_class"
        "&$order=count(*) DESC&$limit=5",
    )

    # 5. The ward boundaries dataset -- small (50 rows), one per ward.
    show(
        "Ward boundaries, plain JSON (2 rows)",
        f"{BASE_URL}/{WARDS_DATASET_ID}.json?$limit=2",
    )

    # 6. Pagination: the full pipeline (src/fetch_data.py) pages through
    #    $limit/$offset since a single request caps out (5,000 rows/page
    #    here) and the zoning dataset has ~15,000 rows total.
    print("\n=== Pagination pattern used for full downloads ===")
    print(
        f"{BASE_URL}/{ZONING_DATASET_ID}.geojson?$limit=5000&$offset=0\n"
        f"{BASE_URL}/{ZONING_DATASET_ID}.geojson?$limit=5000&$offset=5000\n"
        f"{BASE_URL}/{ZONING_DATASET_ID}.geojson?$limit=5000&$offset=10000\n"
        "...until a page comes back with fewer than 5000 features."
    )


if __name__ == "__main__":
    main()
