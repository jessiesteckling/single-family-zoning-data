"""How two sets of polygons become a percentage per ward."""

import unittest

import geopandas as gpd

from src.analyze import (
    compute_citywide_category_shares,
    compute_ohare_context,
    compute_ward_category_shares,
    restrict_category_shares,
    restrict_ward_shares,
)
from src.categorize import (
    ALLOWED,
    NOT_ALLOWED,
    OTHER,
    PLANNED_DEV,
    RESIDENTIAL_CATEGORY_ORDER,
)
from src.constants import SOURCE_CRS
from tests.unit import fixtures


def _frame(features):
    return gpd.GeoDataFrame.from_features(features, crs=SOURCE_CRS)


class WardShareTests(unittest.TestCase):
    def setUp(self):
        self.zoning = _frame(fixtures.zoning_features())
        self.wards = _frame(fixtures.ward_features())
        self.shares = compute_ward_category_shares(self.zoning, self.wards)

    def _pct(self, ward, category):
        row = self.shares[
            (self.shares["ward"] == ward) & (self.shares["category"] == category)
        ]
        return row["pct"].iloc[0]

    def test_a_district_straddling_the_ward_line_is_split_between_both(self):
        # RT-4 spans the boundary, so each ward gets half of it. Without the
        # overlay the whole district would land in one ward or be counted twice.
        self.assertAlmostEqual(self._pct(1, ALLOWED), 50.0, places=1)
        self.assertAlmostEqual(self._pct(2, ALLOWED), 50.0, places=1)

    def test_districts_inside_one_ward_stay_there(self):
        self.assertAlmostEqual(self._pct(1, NOT_ALLOWED), 50.0, places=1)
        self.assertAlmostEqual(self._pct(2, NOT_ALLOWED), 0.0, places=1)
        self.assertAlmostEqual(self._pct(2, OTHER), 50.0, places=1)

    def test_every_ward_gets_a_row_for_every_category(self):
        self.assertEqual(len(self.shares), 2 * 4)
        self.assertEqual(list(self.shares.columns), ["ward", "category", "pct"])

    def test_each_ward_sums_to_100(self):
        for ward, total in self.shares.groupby("ward")["pct"].sum().items():
            with self.subTest(ward=ward):
                self.assertAlmostEqual(total, 100.0, places=6)


class RestrictedShareTests(unittest.TestCase):
    def test_dropping_other_renormalises_the_rest_to_100(self):
        shares = compute_ward_category_shares(
            _frame(fixtures.zoning_features()), _frame(fixtures.ward_features())
        )
        restricted = restrict_ward_shares(shares, RESIDENTIAL_CATEGORY_ORDER)

        self.assertNotIn(OTHER, set(restricted["category"]))
        for ward, total in restricted.groupby("ward")["pct"].sum().items():
            with self.subTest(ward=ward):
                self.assertAlmostEqual(total, 100.0, places=6)

    def test_ward_2_is_all_apartments_once_industrial_land_is_excluded(self):
        # Ward 2 is half RT-4 and half M1-1. Drop the M and the RT is all of it.
        shares = compute_ward_category_shares(
            _frame(fixtures.zoning_features()), _frame(fixtures.ward_features())
        )
        restricted = restrict_ward_shares(shares, RESIDENTIAL_CATEGORY_ORDER)
        row = restricted[
            (restricted["ward"] == 2) & (restricted["category"] == ALLOWED)
        ]
        self.assertAlmostEqual(row["pct"].iloc[0], 100.0, places=6)

    def test_citywide_restriction_matches(self):
        citywide = compute_citywide_category_shares(_frame(fixtures.zoning_features()))
        restricted = restrict_category_shares(citywide, RESIDENTIAL_CATEGORY_ORDER)
        self.assertAlmostEqual(restricted.sum(), 100.0, places=6)
        self.assertNotIn(OTHER, restricted.index)


class OhareContextTests(unittest.TestCase):
    def test_it_finds_the_ward_holding_the_airport_polygon(self):
        features = fixtures.zoning_features()
        # Re-label the ward-2-only district as the airport placeholder.
        features[2]["properties"]["zone_class"] = "PD 0"

        context = compute_ohare_context(
            _frame(features), _frame(fixtures.ward_features())
        )

        self.assertEqual(context.ward, 2)
        self.assertAlmostEqual(context.pct_of_planned_dev, 100.0, places=6)
        self.assertAlmostEqual(context.pct_of_ward, 50.0, places=1)
        self.assertGreater(context.area_sq_mi, 0)


if __name__ == "__main__":
    unittest.main()
