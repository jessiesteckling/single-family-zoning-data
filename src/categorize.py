"""Group Chicago zone_class codes into the four categories used by Steven
Vance's "Where apartments are allowed in Chicago" map: whether new apartments/
condos are allowed under each district's base zoning.
"""

import re

NOT_ALLOWED = "Apartments & condos not allowed (RS)"
ALLOWED = "Apartments & condos allowed"
PLANNED_DEV = "Planned Developments"
OTHER = "All other zones (no residential allowed)"

NOT_ALLOWED_PREFIXES = {"RS"}
PLANNED_DEV_PREFIXES = {"PD"}
# Base zoning prefixes where new multi-unit apartments/condos are permitted.
ALLOWED_PREFIXES = {"RT", "RM", "B", "C", "DR", "DC", "DX"}

CATEGORY_ORDER = [NOT_ALLOWED, ALLOWED, PLANNED_DEV, OTHER]


def categorize(zone_class: str) -> str:
    """Map a zone_class code (e.g. "RS-3", "B3-2", "PD 461") to one of the
    four categories above.
    """
    prefix_match = re.match(r"^[A-Za-z]+", zone_class.strip())
    prefix = prefix_match.group(0).upper() if prefix_match else ""

    if prefix in NOT_ALLOWED_PREFIXES:
        return NOT_ALLOWED
    if prefix in PLANNED_DEV_PREFIXES:
        return PLANNED_DEV
    if prefix in ALLOWED_PREFIXES:
        return ALLOWED
    return OTHER

# The categories where residential is permitted or negotiable. Excludes OTHER,
# which is the zones that allow no housing at all.
RESIDENTIAL_CATEGORY_ORDER = [NOT_ALLOWED, ALLOWED, PLANNED_DEV]
