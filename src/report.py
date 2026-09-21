"""Format ward zoning shares as a markdown table: one row per ward, one
column per zoning category, with a legend documenting which zone_class
prefixes fall into each category.

`categories` selects which columns appear and what the percentages are shares
of, so the same formatter renders both the all-land table and the
residential-only one.
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

_LEGEND_LINES = {
    NOT_ALLOWED: f"- Single-Family Only: {', '.join(sorted(NOT_ALLOWED_PREFIXES))} (e.g. RS-1, RS-2, RS-3)",
    ALLOWED: f"- Apartments Allowed: {', '.join(sorted(ALLOWED_PREFIXES))}",
    PLANNED_DEV: f"- Planned Development: {', '.join(sorted(PLANNED_DEV_PREFIXES))} (e.g. PD 23, PD 461)",
    OTHER: "- Other: everything else (e.g. M, POS, PMD, T) -- no residential allowed",
}

_EXCLUDED_NOTE = (
    "Percentages are shares of land where residential is permitted or negotiable. "
    "Zones allowing no housing (M, POS, PMD, T) are excluded from the denominator, "
    "so a ward's figures here are higher than in the all-land table."
)


# Ward 41 is mostly airport, which makes its row read oddly. Hardcoded because
# the ward holding O'Hare is not going to move.
OHARE_NOTE = (
    "**Ward 41 and O'Hare.** Most of Ward 41 is taken up by O'Hare Airport, "
    "which is zoned as a planned development. That pushes the ward's Planned "
    "Development figure up and its other figures down, so Ward 41 is not "
    "really comparable to the other wards in this table.\n"
)


_WATER_NOTE = (
    "Water inside a zoning district counts toward its area. The Chicago River and its "
    "branches run through zoned land rather than being cut out of it, so a little of "
    "each riverside ward's figure is river. Lake Michigan is not zoned and is excluded."
)


def _legend(categories: list[str]) -> str:
    lines = ["**Zoning codes by column:**"]
    lines += [_LEGEND_LINES[c] for c in categories]
    if OTHER not in categories:
        lines += ["", _EXCLUDED_NOTE]
    lines += ["", _WATER_NOTE]
    return "\n".join(lines)


def format_ward_report(
    ward_pct: pd.DataFrame,
    citywide_pct: pd.Series,
    categories: list[str] = CATEGORY_ORDER,
    title: str | None = None,
    notes: list[str] | None = None,
) -> str:
    pct_table = ward_pct.pivot(index="ward", columns="category", values="pct")
    pct_table = pct_table.sort_index()[categories]
    pct_table.columns = [_COLUMN_LABELS[c] for c in categories]

    header = "| Ward | " + " | ".join(pct_table.columns) + " |"
    separator = "|---" * (len(pct_table.columns) + 1) + "|"
    citywide_row = (
        "| **All Chicago** | "
        + " | ".join(f"**{v:.1f}%**" for v in citywide_pct[categories])
        + " |"
    )
    ward_rows = [
        "| " + str(ward) + " | " + " | ".join(f"{v:.1f}%" for v in row) + " |"
        for ward, row in pct_table.iterrows()
    ]

    table = "\n".join([header, separator, citywide_row, *ward_rows])
    heading = f"# {title}\n\n" if title else ""
    footnotes = "".join(f"\n{note}\n" for note in notes or [])
    return f"{heading}{table}\n\n{_legend(categories)}\n{footnotes}"
