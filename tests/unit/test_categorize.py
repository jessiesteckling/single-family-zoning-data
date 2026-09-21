"""How a zone_class code becomes one of the four categories."""

import unittest

from src.categorize import ALLOWED, NOT_ALLOWED, OTHER, PLANNED_DEV, categorize


class CategorizeTests(unittest.TestCase):
    def test_each_prefix_lands_in_its_category(self):
        cases = {
            "RS-1": NOT_ALLOWED,
            "RS-3": NOT_ALLOWED,
            "RT-4": ALLOWED,
            "RT-3.5": ALLOWED,
            "RM-5": ALLOWED,
            "B3-2": ALLOWED,
            "C1-2": ALLOWED,
            "DX-7": ALLOWED,
            "DR-3": ALLOWED,
            "DC-16": ALLOWED,
            "PD 461": PLANNED_DEV,
            "PD 0": PLANNED_DEV,
            "M1-1": OTHER,
            "POS-2": OTHER,
            "PMD 11": OTHER,
            "T": OTHER,
            "DS-3": OTHER,
        }
        for code, expected in cases.items():
            with self.subTest(code=code):
                self.assertEqual(categorize(code), expected)

    def test_malformed_codes_in_the_real_data_still_resolve(self):
        # These four spellings all appear in the live dataset.
        for code in ("RM4.5", "RM5.5", "RM4-.5"):
            with self.subTest(code=code):
                self.assertEqual(categorize(code), ALLOWED)
        self.assertEqual(categorize("PMD13"), OTHER)

    def test_prefix_matching_ignores_case_and_surrounding_space(self):
        self.assertEqual(categorize("  rs-3 "), NOT_ALLOWED)

    def test_pd_is_not_confused_with_pmd(self):
        self.assertEqual(categorize("PD 12"), PLANNED_DEV)
        self.assertEqual(categorize("PMD 12"), OTHER)

    def test_an_unknown_prefix_falls_through_to_other(self):
        # Documents current behaviour, which finding M7 flags as a silent guess.
        self.assertEqual(categorize("ZZ-9"), OTHER)


if __name__ == "__main__":
    unittest.main()
