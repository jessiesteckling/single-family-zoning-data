"""How per-ward percentages become the markdown table."""

import unittest

import geopandas as gpd

from src.analyze import (
    OhareContext,
    compute_citywide_category_shares,
    compute_ward_category_shares,
    rescale_category_shares_to,
    rescale_ward_shares_to,
)
from src.categorize import RESIDENTIAL_CATEGORY_ORDER
from src.constants import SOURCE_CRS
from src.report import format_ward_report, ohare_note
from tests.unit import fixtures

EXPECTED_ALL_LAND_REPORT = """\
| Ward | Single-Family Only | Apartments Allowed | Planned Development | Other |
|---|---|---|---|---|
| **All Chicago** | **25.0%** | **50.0%** | **0.0%** | **25.0%** |
| 1 | 50.0% | 50.0% | 0.0% | 0.0% |
| 2 | 0.0% | 50.0% | 0.0% | 50.0% |

**Zoning codes by column:**
- Single-Family Only: RS (e.g. RS-1, RS-2, RS-3)
- Apartments Allowed: B, C, DC, DR, DX, RM, RT
- Planned Development: PD (e.g. PD 23, PD 461)
- Other: everything else (e.g. M, POS, PMD, T) -- no residential allowed
"""

EXPECTED_RESIDENTIAL_REPORT = """\
| Ward | Single-Family Only | Apartments Allowed | Planned Development |
|---|---|---|---|
| **All Chicago** | **33.3%** | **66.7%** | **0.0%** |
| 1 | 50.0% | 50.0% | 0.0% |
| 2 | 0.0% | 100.0% | 0.0% |

**Zoning codes by column:**
- Single-Family Only: RS (e.g. RS-1, RS-2, RS-3)
- Apartments Allowed: B, C, DC, DR, DX, RM, RT
- Planned Development: PD (e.g. PD 23, PD 461)

Percentages are shares of land where residential is permitted or negotiable. \
Zones allowing no housing (M, POS, PMD, T) are excluded from the denominator, \
so a ward's figures here are higher than in the all-land table.
"""

EXPECTED_OHARE_NOTE = (
    "**Ward 7 and O'Hare.** One polygon, zone_class `PD 0`, covers the airport: "
    "10.3 sq mi, 32% of all Planned Development land in the city and 60% of "
    "Ward 7 by area. It is classified correctly -- the zoning ordinance "
    "designates land within the Airport Layout Plan the Airport Planned "
    "Development -- but it dominates Ward 7's denominator and deflates every "
    "other figure in that row, so that ward is not comparable to the rest on "
    "this table. O'Hare falls entirely within Ward 7; no other ward is "
    "affected.\n"
)


def _frame(response):
    return gpd.GeoDataFrame.from_features(response["features"], crs=SOURCE_CRS)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.zoning = _frame(fixtures.ZONING_RESPONSE)
        self.wards = _frame(fixtures.WARDS_RESPONSE)
        self.shares = compute_ward_category_shares(self.zoning, self.wards)
        self.citywide = compute_citywide_category_shares(self.zoning)

    def test_the_whole_all_land_report(self):
        self.assertEqual(
            format_ward_report(self.shares, self.citywide), EXPECTED_ALL_LAND_REPORT
        )

    def test_the_whole_residential_report(self):
        report = format_ward_report(
            rescale_ward_shares_to(self.shares, RESIDENTIAL_CATEGORY_ORDER),
            rescale_category_shares_to(self.citywide, RESIDENTIAL_CATEGORY_ORDER),
            categories=RESIDENTIAL_CATEGORY_ORDER,
        )
        self.assertEqual(report, EXPECTED_RESIDENTIAL_REPORT)

    def test_a_title_becomes_a_heading_above_the_table(self):
        report = format_ward_report(self.shares, self.citywide, title="Toy City")
        self.assertEqual(report, "# Toy City\n\n" + EXPECTED_ALL_LAND_REPORT)

    def test_notes_are_appended_after_the_legend(self):
        report = format_ward_report(
            self.shares, self.citywide, notes=["**A footnote.**"]
        )
        self.assertEqual(report, EXPECTED_ALL_LAND_REPORT + "\n**A footnote.**\n")


class FootnoteTests(unittest.TestCase):
    def test_every_figure_in_the_note_comes_from_the_context(self):
        note = ohare_note(
            OhareContext(
                ward=7, area_sq_mi=10.32, pct_of_planned_dev=32.0, pct_of_ward=60.0
            )
        )
        self.assertEqual(note, EXPECTED_OHARE_NOTE)


if __name__ == "__main__":
    unittest.main()
