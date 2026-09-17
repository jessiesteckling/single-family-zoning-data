"""Fetch GeoJSON datasets from the Chicago Data Portal (Socrata/SODA API),
caching each one to a local file so repeated runs don't re-download.
"""

import json
from pathlib import Path

import geopandas as gpd
import requests

SOCRATA_BASE_URL = "https://data.cityofchicago.org/resource"
PAGE_SIZE = 5000


def fetch_geojson(dataset_id: str, cache_path: Path) -> gpd.GeoDataFrame:
    """Return a dataset as a GeoDataFrame, downloading and paginating through
    the Socrata API on first use and reading from `cache_path` afterward.
    """
    if cache_path.exists():
        return gpd.read_file(cache_path)

    features = []
    offset = 0
    while True:
        url = (
            f"{SOCRATA_BASE_URL}/{dataset_id}.geojson"
            f"?$limit={PAGE_SIZE}&$offset={offset}"
        )
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        page = response.json()
        page_features = page["features"]
        features.extend(page_features)
        if len(page_features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    geojson = {"type": "FeatureCollection", "features": features}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(geojson))
    return gpd.read_file(cache_path)
