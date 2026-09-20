"""Format ward zoning shares as a markdown table: one row per ward, one
column per zoning category, with a legend documenting which zone_class
prefixes fall into each category.

`categories` selects which columns appear and what the percentages are shares
of, so the same formatter renders both the all-land table and the
residential-only one.
"""

import pandas as pd

from .analyze import OhareContext
from .categorize import (
    OHARE_ZONE_CLASS,
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


def ohare_note(context: OhareContext) -> str:
    """Footnote for the Planned Development column, which O'Hare dominates."""
    return (
        f"**Ward {context.ward} and O'Hare.** One polygon, zone_class "
        f"`{OHARE_ZONE_CLASS}`, covers the airport: {context.area_sq_mi:.1f} sq mi, "
        f"{context.pct_of_planned_dev:.0f}% of all Planned Development land in the city "
        f"and {context.pct_of_ward:.0f}% of Ward {context.ward} by area. It is classified "
        "correctly -- the zoning ordinance designates land within the Airport Layout Plan "
        f"the Airport Planned Development -- but it dominates Ward {context.ward}'s "
        "denominator and deflates every other figure in that row, so that ward is not "
        f"comparable to the rest on this table. O'Hare falls entirely within Ward "
        f"{context.ward}; no other ward is affected.\n"
    )


def _legend(categories: list[str]) -> str:
    lines = ["**Zoning codes by column:**"]
    lines += [_LEGEND_LINES[c] for c in categories]
    if OTHER not in categories:
        lines += ["", _EXCLUDED_NOTE]
    return "\n".join(lines)


def format_ward_report(
    shares: pd.DataFrame,
    citywide: pd.Series,
    categories: list[str] = CATEGORY_ORDER,
    title: str | None = None,
    notes: list[str] | None = None,
) -> str:
    pivot = shares.pivot(index="ward", columns="category", values="pct")
    pivot = pivot.sort_index()[categories]
    pivot.columns = [_COLUMN_LABELS[c] for c in categories]

    header = "| Ward | " + " | ".join(pivot.columns) + " |"
    separator = "|---" * (len(pivot.columns) + 1) + "|"
    citywide_row = (
        "| **All Chicago** | "
        + " | ".join(f"**{v:.1f}%**" for v in citywide[categories])
        + " |"
    )
    ward_rows = [
        "| " + str(ward) + " | " + " | ".join(f"{v:.1f}%" for v in row) + " |"
        for ward, row in pivot.iterrows()
    ]

    table = "\n".join([header, separator, citywide_row, *ward_rows])
    heading = f"# {title}\n\n" if title else ""
    footnotes = "".join(f"\n{note}\n" for note in notes or [])
    return f"{heading}{table}\n\n{_legend(categories)}\n{footnotes}"
