"""Shared configuration: dataset identifiers, API settings, coordinate systems
and unit conversions.

What belongs here is cross-cutting -- used by more than one module, or a value
worth stating once so a change lands everywhere. Domain definitions stay in the
module they define: the zoning taxonomy is in `categorize.py`, the report's
column labels are in `report.py`, and the output paths are in `main.py`, because
those are what those modules are for.
"""

# --- Chicago Data Portal (Socrata/SODA) --------------------------------------

SOCRATA_BASE_URL = "https://data.cityofchicago.org/resource"

# Boundaries - Zoning Districts (current).
# https://dev.socrata.com/foundry/data.cityofchicago.org/dj47-wfun
ZONING_DATASET_ID = "dj47-wfun"

# Boundaries - Wards (2023-).
# https://dev.socrata.com/foundry/data.cityofchicago.org/p293-wvbd
WARDS_DATASET_ID = "p293-wvbd"

# Rows per paginated request. This is a choice, not an API limit: Socrata's
# $limit defaults to 1,000 and SODA 2.0 permits up to 50,000, while 2.1 and 3.0
# have no maximum. 5,000 keeps the zoning dataset to three requests.
PAGE_SIZE = 5000

# --- Coordinate reference systems --------------------------------------------

# What the portal's GeoJSON arrives in: WGS84 lon/lat, which Socrata declares as
# "urn:ogc:def:crs:OGC:1.3:CRS84" and RFC 7946 requires for GeoJSON regardless.
# It has to be passed explicitly because `fetch_geojson` gives `from_features`
# the bare feature list, so that declaration -- which sits on the
# FeatureCollection wrapper -- never reaches it, leaving `crs=None`.
SOURCE_CRS = "EPSG:4326"

# NAD83 / Illinois East, in US survey feet -- the CRS every area is measured in.
# Area cannot be computed in SOURCE_CRS, whose coordinates are angles: a degree
# is a different distance depending on direction and latitude. Illinois East is
# the State Plane zone covering Chicago, so distortion across the city is
# negligible -- areas computed in it match the datasets' own shape_area and
# st_area_sh fields to six decimal places.
PROJECTED_CRS = "EPSG:3435"

# 5,280 feet to a mile, squared -> 27,878,400. PROJECTED_CRS is in feet, so
# every area arrives in square feet and divides by this to be readable.
SQ_FEET_PER_SQ_MILE = 5280**2

# --- Data quirks -------------------------------------------------------------

# O'Hare. A single polygon of 10.3 sq mi, correctly classified as a planned
# development: the zoning ordinance places land within the Airport Layout Plan
# in the Airport Planned Development of 1964-01-23. It is large enough to be 60%
# of ward 41 and 32% of all planned-development land citywide, which distorts
# that ward's row badly enough that both reports footnote it.
OHARE_ZONE_CLASS = "PD 0"

