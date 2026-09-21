"""Shared configuration: dataset identifiers, API settings, coordinate systems
and unit conversions.

What belongs here is cross-cutting -- used by more than one module, or a value
worth stating once so a change lands everywhere. Domain definitions stay in the
module they define: the zoning taxonomy is in `categorize.py`, the report's
column labels are in `report.py`, and the output paths are in `main.py`, because
those are what those modules are for.
"""

# --- Chicago Data Portal -----------------------------------------------------

DATA_PORTAL_BASE_URL = "https://data.cityofchicago.org/resource"

# Boundaries - Zoning Districts (current). One polygon per zoning district,
# carrying a `zone_class` code such as "RS-1". Roughly 15,000 rows, and no ward
# information -- which is why the two datasets have to be overlaid.
# https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun
ZONING_DATASET_ID = "dj47-wfun"

# Boundaries - Wards (2023-). One polygon per ward, 50 rows, no zoning
# information.
# https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd
WARDS_DATASET_ID = "p293-wvbd"

# Rows per paginated request. A choice, not a limit: the portal's $limit
# defaults to 1,000 and accepts up to 50,000. 5,000 keeps the zoning dataset to
# three requests.
PAGE_SIZE = 5000

# --- Coordinate reference systems --------------------------------------------
#
# A coordinate reference system says what the numbers inside a shape actually
# mean. The portal sends latitude and longitude; anything that measures size has
# to convert first to a system whose numbers are feet.
#
# The "EPSG:" prefix is a catalogue reference. EPSG is a public registry of
# coordinate systems, named for the European Petroleum Survey Group that started
# it, which gives each system a short stable number rather than a paragraph of
# description. The two used below are its entries 4326 and 3435.

# What the data arrives in: ordinary latitude and longitude. Fine for saying
# where something is, useless for measuring how big it is, because a degree is
# not a fixed distance -- one degree of longitude covers about 52 miles in
# Chicago, against about 69 miles for a degree of latitude.
#
# We state it here rather than reading it off the response. The portal does
# label its data, but the label is a `crs` key at the top level of the response,
# sitting alongside the `features` list rather than inside it. `fetch_geojson`
# keeps only that list, because it has to join the features from several pages
# into one, so the label is gone before geopandas ever sees the shapes.
# (WGS84 longitude/latitude.)
SOURCE_CRS = "EPSG:4326"

# What everything is converted to before any area is measured: a flat grid laid
# over eastern Illinois whose coordinates are in feet, so a polygon's area comes
# out in square feet.
#
# Flattening a round planet always stretches something, so the grid has to be
# one drawn for this part of the world -- Chicago sits well inside this one.
# Checked rather than assumed: areas measured on it match the areas the City
# ships alongside its own data to six decimal places.
# (NAD83 / Illinois State Plane East, US survey feet.)
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
