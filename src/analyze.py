"""Compute, for each Chicago ward, what percentage of zoned land area falls
into each apartment-allowed category.
"""

import geopandas as gpd
import pandas as pd

from .categorize import CATEGORY_ORDER, categorize
from .constants import OHARE_ZONE_CLASS, PROJECTED_CRS


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


def find_ohare_ward(zoning: gpd.GeoDataFrame, wards: gpd.GeoDataFrame) -> int:
    """The ward O'Hare sits in, so the footnote can name it rather than hardcode it."""
    zoning = zoning[["zone_class", "geometry"]].to_crs(PROJECTED_CRS)
    wards = wards[["ward", "geometry"]].copy()
    wards["ward"] = wards["ward"].astype(int)
    wards = wards.to_crs(PROJECTED_CRS)

    ohare = zoning[zoning["zone_class"] == OHARE_ZONE_CLASS]
    in_wards = gpd.overlay(ohare, wards, how="intersection")
    area_sq_ft = in_wards.assign(area=in_wards.geometry.area)
    return int(area_sq_ft.groupby("ward")["area"].sum().idxmax())
