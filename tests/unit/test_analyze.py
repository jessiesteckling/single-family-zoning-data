"""How two sets of polygons become a percentage per ward."""

import unittest

import geopandas as gpd

from src.analyze import (
    compute_citywide_category_shares,
    compute_ward_category_shares,
    rescale_category_shares_to,
    rescale_ward_shares_to,
)
from src.categorize import RESIDENTIAL_CATEGORY_ORDER
from src.constants import SOURCE_CRS
from tests.unit import fixtures

NOT_ALLOWED = "Apartments & condos not allowed (RS)"
ALLOWED = "Apartments & condos allowed"
PLANNED_DEV = "Planned Developments"
OTHER = "All other zones (no residential allowed)"


def _frame(response):
    return gpd.GeoDataFrame.from_features(response["features"], crs=SOURCE_CRS)


def _rows(shares):
    """The share table as plain tuples, rounded past projection noise."""
    return [
        (int(r.ward), r.category, round(r.pct, 2)) for r in shares.itertuples()
    ]


class WardShareTests(unittest.TestCase):
    def test_the_whole_table(self):
        # Ward 1 is RS-3 (0.025 deg) plus the left half of RT-4 (0.025 deg).
        # Ward 2 is the right half of RT-4 (0.025) plus M1-1 (0.025).
        shares = compute_ward_category_shares(
            _frame(fixtures.ZONING_RESPONSE), _frame(fixtures.WARDS_RESPONSE)
        )

        self.assertEqual(
            _rows(shares),
            [
                (1, NOT_ALLOWED, 50.0),
                (1, ALLOWED, 50.0),
                (1, PLANNED_DEV, 0.0),
                (1, OTHER, 0.0),
                (2, NOT_ALLOWED, 0.0),
                (2, ALLOWED, 50.0),
                (2, PLANNED_DEV, 0.0),
                (2, OTHER, 50.0),
            ],
        )

    def test_a_district_straddling_the_ward_line_is_split_between_both(self):
        # RT-4 is the only apartments-allowed district and it spans the
        # boundary, so 50% in each ward is it being halved. A spatial join
        # would instead give one ward 100% and the other 0%.
        shares = compute_ward_category_shares(
            _frame(fixtures.ZONING_RESPONSE), _frame(fixtures.WARDS_RESPONSE)
        )
        allowed = [r for r in _rows(shares) if r[1] == ALLOWED]

        self.assertEqual(allowed, [(1, ALLOWED, 50.0), (2, ALLOWED, 50.0)])

    def test_columns_and_row_count(self):
        shares = compute_ward_category_shares(
            _frame(fixtures.ZONING_RESPONSE), _frame(fixtures.WARDS_RESPONSE)
        )
        self.assertEqual(list(shares.columns), ["ward", "category", "pct"])
        self.assertEqual(len(shares), 8)


class CitywideShareTests(unittest.TestCase):
    def test_the_whole_series(self):
        # Across the toy city: RS-3 0.025, RT-4 0.050, M1-1 0.025 of 0.100.
        citywide = compute_citywide_category_shares(_frame(fixtures.ZONING_RESPONSE))

        self.assertEqual(
            [(k, round(v, 2)) for k, v in citywide.items()],
            [
                (NOT_ALLOWED, 25.0),
                (ALLOWED, 50.0),
                (PLANNED_DEV, 0.0),
                (OTHER, 25.0),
            ],
        )


class RestrictedShareTests(unittest.TestCase):
    def test_the_whole_restricted_table(self):
        # Ward 2 loses its M1-1 half, so its remaining RT-4 becomes all of it.
        shares = compute_ward_category_shares(
            _frame(fixtures.ZONING_RESPONSE), _frame(fixtures.WARDS_RESPONSE)
        )
        restricted = rescale_ward_shares_to(shares, RESIDENTIAL_CATEGORY_ORDER)

        self.assertEqual(
            _rows(restricted),
            [
                (1, NOT_ALLOWED, 50.0),
                (1, ALLOWED, 50.0),
                (1, PLANNED_DEV, 0.0),
                (2, NOT_ALLOWED, 0.0),
                (2, ALLOWED, 100.0),
                (2, PLANNED_DEV, 0.0),
            ],
        )

    def test_the_whole_restricted_citywide_series(self):
        citywide = compute_citywide_category_shares(_frame(fixtures.ZONING_RESPONSE))
        restricted = rescale_category_shares_to(citywide, RESIDENTIAL_CATEGORY_ORDER)

        self.assertEqual(
            [(k, round(v, 2)) for k, v in restricted.items()],
            [
                (NOT_ALLOWED, 33.33),
                (ALLOWED, 66.67),
                (PLANNED_DEV, 0.0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
