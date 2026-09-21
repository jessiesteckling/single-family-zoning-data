"""Mock Chicago Data Portal responses, shaped exactly like the real ones.

The geography is a toy city two wards wide, laid out so the numbers the
pipeline should produce are obvious by inspection:

    lon  -87.70      -87.675     -87.65      -87.625     -87.60
          |-----------|-----------|-----------|-----------|
          |   RS-3    |         RT-4          |   M1-1    |
          |-------- ward 1 -------|-------- ward 2 -------|

RT-4 deliberately straddles the ward line. Splitting it is the whole reason the
pipeline runs a spatial overlay instead of a spatial join, so every ward should
come out half single-family-or-other and half apartments-allowed.
"""

WARD_BOUNDARY_LON = -87.65
LAT_SOUTH, LAT_NORTH = 41.80, 41.90


def _box(west: float, east: float) -> dict:
    """A MultiPolygon spanning the full north-south extent, as the portal sends
    it: one ring, counter-clockwise, [lon, lat] pairs.
    """
    ring = [
        [west, LAT_SOUTH],
        [east, LAT_SOUTH],
        [east, LAT_NORTH],
        [west, LAT_NORTH],
        [west, LAT_SOUTH],
    ]
    return {"type": "MultiPolygon", "coordinates": [[ring]]}


def feature(geometry: dict, **properties) -> dict:
    return {"type": "Feature", "geometry": geometry, "properties": properties}


def collection(features: list[dict]) -> dict:
    """A FeatureCollection with the `crs` member the portal really sends.

    The member sits beside `features`, not inside it, which is why
    `fetch_geojson` has to supply the CRS itself.
    """
    return {
        "type": "FeatureCollection",
        "features": features,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
    }


def zoning_features() -> list[dict]:
    return [
        feature(_box(-87.700, -87.675), zone_class="RS-3", objectid="1"),
        feature(_box(-87.675, -87.625), zone_class="RT-4", objectid="2"),
        feature(_box(-87.625, -87.600), zone_class="M1-1", objectid="3"),
    ]


def ward_features() -> list[dict]:
    return [
        feature(_box(-87.700, WARD_BOUNDARY_LON), ward="1", objectid="10"),
        feature(_box(WARD_BOUNDARY_LON, -87.600), ward="2", objectid="20"),
    ]


def zoning_response() -> dict:
    return collection(zoning_features())


def ward_response() -> dict:
    return collection(ward_features())
