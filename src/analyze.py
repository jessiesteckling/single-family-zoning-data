"""Compute, for each Chicago ward, what percentage of zoned land area falls
into each apartment-allowed category.
"""

from typing import NamedTuple

import geopandas as gpd
import pandas as pd

from .categorize import CATEGORY_ORDER, OHARE_ZONE_CLASS, PLANNED_DEV, categorize

# Illinois State Plane East (NAD83, US feet) -- a projected CRS appropriate
# for accurate area measurement within Chicago.
PROJECTED_CRS = "EPSG:3435"

SQ_FEET_PER_SQ_MILE = 27_878_400


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


class OhareContext(NamedTuple):
    """Where O'Hare sits, for the footnote both reports carry."""

    ward: int
    area_sq_mi: float
    pct_of_planned_dev: float
    pct_of_ward: float


def compute_ohare_context(
    zoning: gpd.GeoDataFrame, wards: gpd.GeoDataFrame
) -> OhareContext:
    zoning = zoning[["zone_class", "geometry"]].to_crs(PROJECTED_CRS)
    wards = wards[["ward", "geometry"]].copy()
    wards["ward"] = wards["ward"].astype(int)
    wards = wards.to_crs(PROJECTED_CRS)

    area = zoning.geometry.area
    is_ohare = zoning["zone_class"] == OHARE_ZONE_CLASS
    ohare_area = area[is_ohare].sum()
    planned_area = area[zoning["zone_class"].apply(categorize) == PLANNED_DEV].sum()

    in_wards = gpd.overlay(zoning[is_ohare], wards, how="intersection")
    host = int(in_wards.assign(area=in_wards.geometry.area).groupby("ward")["area"].sum().idxmax())
    host_area = wards.loc[wards["ward"] == host, "geometry"].area.sum()

    return OhareContext(
        ward=host,
        area_sq_mi=ohare_area / SQ_FEET_PER_SQ_MILE,
        pct_of_planned_dev=ohare_area / planned_area * 100,
        pct_of_ward=ohare_area / host_area * 100,
    )
