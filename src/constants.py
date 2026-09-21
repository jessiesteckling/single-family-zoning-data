# --- Chicago Data Portal -----------------------------------------------------

DATA_PORTAL_BASE_URL = "https://data.cityofchicago.org/resource"

# Boundaries - Zoning Districts (current).
# https://data.cityofchicago.org/Community-Economic-Development/Boundaries-Zoning-Districts-current-/dj47-wfun
ZONING_DATASET_ID = "dj47-wfun"

# Boundaries - Wards (2023-).
# https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-/p293-wvbd
WARDS_DATASET_ID = "p293-wvbd"

# Rows per paginated request.
PAGE_SIZE = 5000

# --- Coordinate reference systems --------------------------------------------
#
# A coordinate reference system says what the numbers inside a shape actually
# mean. The portal sends latitude and longitude; anything that measures size has
# to convert first to a system whose numbers are feet.
#
# "EPSG:" is a catalogue reference. EPSG is a public registry of coordinate
# systems (originally the European Petroleum Survey Group), so each system has a
# short stable number: 4326 and 3435 are the two entries used below.

# What the data arrives in: ordinary latitude and longitude. Fine for saying
# where something is, useless for measuring how big it is, because a degree is
# not a fixed distance -- one degree of longitude covers about 52 miles in
# Chicago, against about 69 miles for a degree of latitude.
#
# Only a fallback. `fetch_geojson` uses whatever the response declares in its
# top-level `crs` key -- currently "urn:ogc:def:crs:OGC:1.3:CRS84", which the
# portal documents. This applies when that key is absent, which the current
# GeoJSON spec allows, having dropped the member and fixed the format to WGS84.
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
