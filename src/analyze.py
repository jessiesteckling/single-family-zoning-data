"""Compute, for each Chicago ward, what percentage of zoned land area falls
into each apartment-allowed category.
"""

from typing import NamedTuple

import geopandas as gpd
import pandas as pd

from .categorize import CATEGORY_ORDER, PLANNED_DEV, categorize
from .constants import OHARE_ZONE_CLASS, PROJECTED_CRS, SQ_FEET_PER_SQ_MILE


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

    total_area_by_ward = area_by_ward_category.groupby("ward")["area"].transform("sum")
    area_by_ward_category["pct"] = (
        area_by_ward_category["area"] / total_area_by_ward * 100
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
    pct_by_category = area_by_category / area_by_category.sum() * 100
    return pct_by_category.reindex(CATEGORY_ORDER, fill_value=0)


def rescale_ward_shares_to(
    shares: pd.DataFrame, categories: list[str]
) -> pd.DataFrame:
    """Rewrite each ward's percentages as shares of `categories` alone.

    Drops the categories left out -- in practice "All other zones", the fourth
    column of the all-land report -- then scales what remains back up to 100.
    The residential report is its only caller.
    """
    kept = shares[shares["category"].isin(categories)].copy()

    # transform("sum") broadcasts each ward's subtotal back onto its own rows,
    # so every row can divide by the total for the ward it belongs to.
    kept_pct_by_ward = kept.groupby("ward")["pct"].transform("sum")

    # Percentages within a ward are proportional to area, so rescaling them is
    # exact. A ward with nothing left would divide by zero; .where makes that
    # NaN, which shows as missing rather than inf.
    kept["pct"] = kept["pct"].div(kept_pct_by_ward.where(kept_pct_by_ward > 0)).mul(100)
    return kept


def rescale_category_shares_to(
    citywide: pd.Series, categories: list[str]
) -> pd.Series:
    """Rescale the citywide percentages the same way, for the All Chicago row.

    Like its ward counterpart, only the residential report calls it.
    """
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

    area_sq_ft = zoning.geometry.area
    is_ohare = zoning["zone_class"] == OHARE_ZONE_CLASS
    ohare_sq_ft = area_sq_ft[is_ohare].sum()
    planned_sq_ft = area_sq_ft[zoning["zone_class"].apply(categorize) == PLANNED_DEV].sum()

    in_wards = gpd.overlay(zoning[is_ohare], wards, how="intersection")
    host = int(in_wards.assign(area=in_wards.geometry.area).groupby("ward")["area"].sum().idxmax())
    host_sq_ft = wards.loc[wards["ward"] == host, "geometry"].area.sum()

    return OhareContext(
        ward=host,
        area_sq_mi=ohare_sq_ft / SQ_FEET_PER_SQ_MILE,
        pct_of_planned_dev=ohare_sq_ft / planned_sq_ft * 100,
        pct_of_ward=ohare_sq_ft / host_sq_ft * 100,
    )
