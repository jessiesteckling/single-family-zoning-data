"""Shared configuration: dataset identifiers, API settings, coordinate systems,
unit conversions and output locations.

What belongs here is cross-cutting -- used by more than one module, or a value
worth stating once so a change lands everywhere. Domain definitions stay in the
module they define: the zoning taxonomy is in `categorize.py` and the report's
column labels are in `report.py`, because those are what those modules are for.
"""

from pathlib import Path

# --- Chicago Data Portal (Socrata/SODA) --------------------------------------

SOCRATA_BASE_URL = "https://data.cityofchicago.org/resource"

# Boundaries - Zoning Districts (current). One polygon per zoning district,
# carrying a `zone_class` code such as "RS-1". Roughly 15,000 rows, no ward
# information. https://dev.socrata.com/foundry/data.cityofchicago.org/dj47-wfun
ZONING_DATASET_ID = "dj47-wfun"

# Boundaries - Wards (2023-). One polygon per ward, 50 rows, no zoning
# information. https://dev.socrata.com/foundry/data.cityofchicago.org/p293-wvbd
WARDS_DATASET_ID = "p293-wvbd"

# Rows per paginated request. This is a choice, not an API limit: Socrata's
# $limit defaults to 1,000 and SODA 2.0 permits up to 50,000, while 2.1 and 3.0
# have no maximum. 5,000 keeps the zoning dataset to three requests.
PAGE_SIZE = 5000

# --- Coordinate reference systems --------------------------------------------

# What the portal sends. GeoJSON is WGS84 by definition (RFC 7946) and Socrata
# includes no `crs` member, so this has to be supplied rather than inferred:
# `GeoDataFrame.from_features` infers nothing and `to_crs` raises without it.
# Coordinates are degrees, so this CRS cannot be used to measure area.
WGS84 = "EPSG:4326"

# NAD83 / Illinois East, US survey feet -- what areas are measured in.
#
# Area needs a projected CRS. In degrees a ward's `.area` comes back as 0.0022
# "square degrees", which is not a unit: a degree of longitude in Chicago spans
# 51.6 miles against 69.0 for a degree of latitude, and the ratio shifts with
# latitude. Projecting flattens the surface so coordinates become feet and
# `.area` becomes square feet.
#
# Flattening always distorts something; State Plane zones stay accurate by being
# narrow, and Illinois East is the zone covering Chicago. Verified rather than
# assumed: areas computed in this CRS match the datasets' own shape_area and
# st_area_sh fields at a ratio of 1.000000 for all 50 wards and at both the 5th
# and 95th percentile across all 14,982 zoning polygons.
PROJECTED_CRS = "EPSG:3435"

# 5,280 feet to a mile, squared -> 27,878,400. PROJECTED_CRS is in feet, so
# every area arrives in square feet and divides by this to be readable.
SQ_FEET_PER_SQ_MILE = 5_280**2

# --- Data quirks -------------------------------------------------------------

# O'Hare. A single polygon of 10.3 sq mi, correctly classified as a planned
# development: the zoning ordinance places land within the Airport Layout Plan
# in the Airport Planned Development of 1964-01-23. It is large enough to be 60%
# of ward 41 and 32% of all planned-development land citywide, which distorts
# that ward's row badly enough that both reports footnote it.
OHARE_ZONE_CLASS = "PD 0"

# --- Output locations --------------------------------------------------------
#
# Relative to the working directory, so the pipeline expects to be run from the
# repository root.

PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("output")
