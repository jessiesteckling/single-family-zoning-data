"""Fetch GeoJSON datasets from the Chicago Data Portal (Socrata/SODA API).

Every run downloads fresh. Nothing is written to disk and nothing is read from
it, so a report always reflects the portal's current state rather than whatever
snapshot happened to be sitting in the working tree.
"""

import geopandas as gpd
import requests

from .constants import DATA_PORTAL_BASE_URL, PAGE_SIZE, SOURCE_CRS


def fetch_geojson(dataset_id: str) -> gpd.GeoDataFrame:
    """Return a dataset as a GeoDataFrame, paginating through the Socrata API."""
    features = []
    offset = 0
    while True:
        url = (
            f"{DATA_PORTAL_BASE_URL}/{dataset_id}.geojson"
            f"?$limit={PAGE_SIZE}&$offset={offset}"
        )
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        page_features = response.json()["features"]
        features.extend(page_features)
        if len(page_features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return gpd.GeoDataFrame.from_features(features, crs=SOURCE_CRS)
