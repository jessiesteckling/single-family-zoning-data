"""Fetch Chicago zoning + ward boundary data and report, per ward, the
percentage of zoned land area in each apartment-allowed category.
"""

from pathlib import Path

from src.analyze import compute_citywide_category_shares, compute_ward_category_shares
from src.fetch_data import fetch_geojson
from src.report import format_ward_report

ZONING_DATASET_ID = "dj47-wfun"  # Boundaries - Zoning Districts (current)
WARDS_DATASET_ID = "p293-wvbd"  # Boundaries - Wards (2023-)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("output")


def main() -> None:
    zoning = fetch_geojson(ZONING_DATASET_ID, RAW_DIR / "zoning.geojson")
    wards = fetch_geojson(WARDS_DATASET_ID, RAW_DIR / "wards.geojson")

    shares = compute_ward_category_shares(zoning, wards)
    citywide = compute_citywide_category_shares(zoning)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shares.to_csv(PROCESSED_DIR / "ward_zoning_shares.csv", index=False)

    report = format_ward_report(shares, citywide)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "ward_zoning_report.md"
    report_path.write_text(report)

    print(report)
    print(f"\nWrote {PROCESSED_DIR / 'ward_zoning_shares.csv'}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
