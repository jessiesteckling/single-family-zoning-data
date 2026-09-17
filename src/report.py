"""Format ward zoning shares as a markdown table: one row per ward, one
column per zoning category, with a legend documenting which zone_class
prefixes fall into each category.
"""

import pandas as pd

from .categorize import (
    ALLOWED,
    ALLOWED_PREFIXES,
    CATEGORY_ORDER,
    NOT_ALLOWED,
    NOT_ALLOWED_PREFIXES,
    OTHER,
    PLANNED_DEV,
    PLANNED_DEV_PREFIXES,
)

_COLUMN_LABELS = {
    NOT_ALLOWED: "Single-Family Only",
    ALLOWED: "Apartments Allowed",
    PLANNED_DEV: "Planned Development",
    OTHER: "Other",
}


def _legend() -> str:
    lines = [
        "**Zoning codes by column:**",
        f"- Single-Family Only: {', '.join(sorted(NOT_ALLOWED_PREFIXES))} (e.g. RS-1, RS-2, RS-3)",
        f"- Apartments Allowed: {', '.join(sorted(ALLOWED_PREFIXES))}",
        f"- Planned Development: {', '.join(sorted(PLANNED_DEV_PREFIXES))} (e.g. PD 23, PD 461)",
        "- Other: everything else (e.g. M, POS, PMD, T, DS) -- no residential allowed",
    ]
    return "\n".join(lines)


def format_ward_report(shares: pd.DataFrame, citywide: pd.Series) -> str:
    pivot = shares.pivot(index="ward", columns="category", values="pct")
    pivot = pivot.sort_index()[CATEGORY_ORDER]
    pivot.columns = [_COLUMN_LABELS[c] for c in CATEGORY_ORDER]
    pivot = pivot.round(1)

    header = "| Ward | " + " | ".join(pivot.columns) + " |"
    separator = "|---" * (len(pivot.columns) + 1) + "|"
    citywide_row = (
        "| **All Chicago** | "
        + " | ".join(f"**{v:.1f}%**" for v in citywide[CATEGORY_ORDER])
        + " |"
    )
    ward_rows = [
        "| " + str(ward) + " | " + " | ".join(f"{v:.1f}%" for v in row) + " |"
        for ward, row in pivot.iterrows()
    ]

    table = "\n".join([header, separator, citywide_row, *ward_rows])
    return f"{table}\n\n{_legend()}\n"
