"""Fetch GeoJSON datasets from the Chicago Data Portal.

Every run downloads fresh. Nothing is written to disk and nothing is read from
it, so a report always reflects the portal's current state rather than whatever
snapshot happened to be sitting in the working tree.
"""

import geopandas as gpd
import requests

from .constants import DATA_PORTAL_BASE_URL, PAGE_SIZE, SOURCE_CRS


def fetch_geojson(dataset_id: str) -> gpd.GeoDataFrame:
    """Return a dataset as a GeoDataFrame, paginating through the portal API.

    The CRS comes from whatever the response declares, falling back to
    SOURCE_CRS when it declares nothing.

    Raises RuntimeError if the download does not match the row count the portal
    reports, rather than returning a short dataset that would produce plausible
    but wrong percentages.
    """
    expected_rows = _row_count(dataset_id)
    features = []
    declared_crs = None
    offset = 0
    while True:
        url = (
            f"{DATA_PORTAL_BASE_URL}/{dataset_id}.geojson"
            f"?$order=:id&$limit={PAGE_SIZE}&$offset={offset}"
        )
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        declared_crs = declared_crs or _declared_crs(payload)
        page_features = payload["features"]
        features.extend(page_features)
        if len(page_features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    if len(features) != expected_rows:
        raise RuntimeError(
            f"{dataset_id}: downloaded {len(features):,} features but the portal "
            f"reports {expected_rows:,} rows. A page may have come back short, or "
            "the dataset may have changed mid-download. Re-run before trusting "
            "any output."
        )

    return gpd.GeoDataFrame.from_features(features, crs=declared_crs or SOURCE_CRS)


def _row_count(dataset_id: str) -> int:
    """How many rows the portal says the dataset has.

    The pagination loop stops on the first short page, so on its own it cannot
    tell "that was the end" from "that request came back truncated". Comparing
    against this is what makes the difference detectable.
    """
    url = f"{DATA_PORTAL_BASE_URL}/{dataset_id}.json?$select=count(*)"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    # The column comes back named "count", but take it positionally so a rename
    # on the portal's side does not break this.
    return int(next(iter(response.json()[0].values())))


def _declared_crs(payload: dict) -> str | None:
    """The CRS named in a response, or None if it does not name one."""
    crs = payload.get("crs") or {}
    return (crs.get("properties") or {}).get("name")
