"""Fetch Chicago zoning + ward boundary data and report, per ward, the
percentage of zoned land area in each apartment-allowed category.

Two reports are written: one over all zoned land, and one restricted to land
where residential is permitted or negotiable, which is the better basis for
reading a ward's true single-family share.
"""

from src.analyze import (
    compute_citywide_category_shares,
    compute_ohare_context,
    compute_ward_category_shares,
    restrict_category_shares,
    restrict_ward_shares,
)
from src.categorize import RESIDENTIAL_CATEGORY_ORDER
from src.constants import (
    OUTPUT_DIR,
    PROCESSED_DIR,
    WARDS_DATASET_ID,
    ZONING_DATASET_ID,
)
from src.fetch_data import fetch_geojson
from src.report import format_ward_report, ohare_note


def main() -> None:
    zoning = fetch_geojson(ZONING_DATASET_ID)
    wards = fetch_geojson(WARDS_DATASET_ID)

    shares = compute_ward_category_shares(zoning, wards)
    citywide = compute_citywide_category_shares(zoning)

    notes = [ohare_note(compute_ohare_context(zoning, wards))]

    residential_shares = restrict_ward_shares(shares, RESIDENTIAL_CATEGORY_ORDER)
    residential_citywide = restrict_category_shares(
        citywide, RESIDENTIAL_CATEGORY_ORDER
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shares.to_csv(PROCESSED_DIR / "ward_zoning_shares.csv", index=False)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reports = {
        OUTPUT_DIR
        / "ward_zoning_report.md": format_ward_report(shares, citywide, notes=notes),
        OUTPUT_DIR
        / "ward_zoning_report_residential.md": format_ward_report(
            residential_shares,
            residential_citywide,
            categories=RESIDENTIAL_CATEGORY_ORDER,
            title="Share of residentially zoned land, by ward",
            notes=notes,
        ),
    }
    for path, report in reports.items():
        path.write_text(report)

    print(reports[OUTPUT_DIR / "ward_zoning_report_residential.md"])
    print(f"Wrote {PROCESSED_DIR / 'ward_zoning_shares.csv'}")
    for path in reports:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
