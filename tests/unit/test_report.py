"""How per-ward percentages become the markdown table."""

import unittest

import geopandas as gpd

from src.analyze import (
    compute_citywide_category_shares,
    compute_ward_category_shares,
    restrict_category_shares,
    restrict_ward_shares,
)
from src.categorize import CATEGORY_ORDER, RESIDENTIAL_CATEGORY_ORDER
from src.constants import SOURCE_CRS
from src.report import format_ward_report, ohare_note
from src.analyze import OhareContext
from tests.unit import fixtures


def _frame(features):
    return gpd.GeoDataFrame.from_features(features, crs=SOURCE_CRS)


class ReportTests(unittest.TestCase):
    def setUp(self):
        zoning = _frame(fixtures.zoning_features())
        wards = _frame(fixtures.ward_features())
        self.shares = compute_ward_category_shares(zoning, wards)
        self.citywide = compute_citywide_category_shares(zoning)
        self.report = format_ward_report(self.shares, self.citywide)
        self.lines = self.report.splitlines()

    def test_header_names_every_category(self):
        header = self.lines[0]
        for label in ("Single-Family Only", "Apartments Allowed",
                      "Planned Development", "Other"):
            self.assertIn(label, header)

    def test_separator_matches_the_column_count(self):
        self.assertEqual(self.lines[1].count("---"), len(CATEGORY_ORDER) + 1)

    def test_citywide_row_comes_first_and_is_bold(self):
        self.assertTrue(self.lines[2].startswith("| **All Chicago** |"))
        self.assertIn("**", self.lines[2])

    def test_one_row_per_ward_after_the_citywide_row(self):
        ward_rows = [ln for ln in self.lines if ln.startswith("| 1 |")
                     or ln.startswith("| 2 |")]
        self.assertEqual(len(ward_rows), 2)

    def test_percentages_render_to_one_decimal(self):
        self.assertIn("50.0%", self.report)

    def test_legend_is_appended(self):
        self.assertIn("**Zoning codes by column:**", self.report)


class ResidentialReportTests(unittest.TestCase):
    def setUp(self):
        zoning = _frame(fixtures.zoning_features())
        wards = _frame(fixtures.ward_features())
        shares = restrict_ward_shares(
            compute_ward_category_shares(zoning, wards), RESIDENTIAL_CATEGORY_ORDER
        )
        citywide = restrict_category_shares(
            compute_citywide_category_shares(zoning), RESIDENTIAL_CATEGORY_ORDER
        )
        self.report = format_ward_report(
            shares, citywide, categories=RESIDENTIAL_CATEGORY_ORDER, title="Residential"
        )

    def test_the_other_column_is_gone(self):
        header = self.report.splitlines()[2]
        self.assertNotIn("| Other |", header)

    def test_it_says_what_the_percentages_are_shares_of(self):
        self.assertIn("residential is permitted or negotiable", self.report)

    def test_the_title_becomes_a_heading(self):
        self.assertTrue(self.report.startswith("# Residential"))


class FootnoteTests(unittest.TestCase):
    def test_every_figure_in_the_ohare_note_comes_from_the_context(self):
        note = ohare_note(
            OhareContext(
                ward=7, area_sq_mi=10.32, pct_of_planned_dev=32.0, pct_of_ward=60.0
            )
        )
        self.assertIn("Ward 7", note)
        self.assertIn("10.3 sq mi", note)
        self.assertIn("32%", note)
        self.assertIn("60%", note)

    def test_notes_are_appended_to_the_report(self):
        report = format_ward_report(
            compute_ward_category_shares(
                _frame(fixtures.zoning_features()), _frame(fixtures.ward_features())
            ),
            compute_citywide_category_shares(_frame(fixtures.zoning_features())),
            notes=["**A footnote.**"],
        )
        self.assertIn("**A footnote.**", report)


if __name__ == "__main__":
    unittest.main()
