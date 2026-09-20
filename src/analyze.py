"""Compute, for each Chicago ward, what percentage of zoned land area falls
into each apartment-allowed category.
"""

import geopandas as gpd
import pandas as pd

from .categorize import CATEGORY_ORDER, categorize

# Illinois State Plane East (NAD83, US feet) -- a projected CRS appropriate
# for accurate area measurement within Chicago.
PROJECTED_CRS = "EPSG:3435"


def compute_ward_category_shares(
    zoning: gpd.GeoDataFrame, wards: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Return a long-format DataFrame with columns [ward, category, pct]
    giving each category's share of zoned land area within each ward.
    """
    zoning = zoning[["zone_class", "geometry"]].copy()
    zoning["category"] = zoning["zone_class"].apply(categorize)

    wards = wards[["ward", "geometry"]].copy()
    wards["ward"] = wards["ward"].astype(int)

    zoning = zoning.to_crs(PROJECTED_CRS)
    wards = wards.to_crs(PROJECTED_CRS)

    pieces = gpd.overlay(
        zoning[["category", "geometry"]],
        wards[["ward", "geometry"]],
        how="intersection",
    )
    pieces["area"] = pieces.geometry.area

    area_by_ward_category = (
        pieces.groupby(["ward", "category"])["area"].sum().reset_index()
    )

    total_by_ward = area_by_ward_category.groupby("ward")["area"].transform("sum")
    area_by_ward_category["pct"] = (
        area_by_ward_category["area"] / total_by_ward * 100
    )

    # Ensure every ward has a row for every category (0% where absent).
    all_wards = sorted(wards["ward"].unique())
    full_index = pd.MultiIndex.from_product(
        [all_wards, CATEGORY_ORDER], names=["ward", "category"]
    )
    result = (
        area_by_ward_category.set_index(["ward", "category"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    return result[["ward", "category", "pct"]]


def compute_citywide_category_shares(zoning: gpd.GeoDataFrame) -> pd.Series:
    """Return a Series indexed by category giving each category's share of
    zoned land area across all of Chicago (area-weighted, not an average of
    per-ward percentages).
    """
    zoning = zoning[["zone_class", "geometry"]].copy()
    zoning["category"] = zoning["zone_class"].apply(categorize)
    zoning = zoning.to_crs(PROJECTED_CRS)

    area_by_category = zoning.groupby("category").geometry.apply(
        lambda geoms: geoms.area.sum()
    )
    pct = area_by_category / area_by_category.sum() * 100
    return pct.reindex(CATEGORY_ORDER, fill_value=0)


def restrict_ward_shares(
    shares: pd.DataFrame, categories: list[str]
) -> pd.DataFrame:
    """Return `shares` limited to `categories`, with each ward's percentages
    renormalized to sum to 100 across just those categories.
    """
    kept = shares[shares["category"].isin(categories)].copy()
    subtotal = kept.groupby("ward")["pct"].transform("sum")
    kept["pct"] = kept["pct"].div(subtotal.where(subtotal > 0)).mul(100)
    return kept


def restrict_category_shares(
    citywide: pd.Series, categories: list[str]
) -> pd.Series:
    """Citywide equivalent of `restrict_ward_shares`."""
    kept = citywide.reindex(categories)
    return kept / kept.sum() * 100
