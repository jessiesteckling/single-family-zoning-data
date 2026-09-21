"""Mock Chicago Data Portal responses, written out exactly as they arrive.

The geography is a toy city two wards wide:

    lon  -87.700     -87.675     -87.650     -87.625     -87.600
          |-----------|-----------|-----------|-----------|
          |   RS-3    |         RT-4          |   M1-1    |
          |-------- ward 1 -------|-------- ward 2 -------|
    lat 41.800 (south) .. 41.900 (north) throughout

RT-4 deliberately straddles the ward line at -87.650. Splitting it is the whole
reason the pipeline runs a spatial overlay instead of a spatial join, so both
wards should come out half apartments-allowed.

Every polygon is 0.025 or 0.050 degrees wide and they all share the same
latitude band, so the expected percentages are exact halves.

These are literals rather than generated shapes so that what the portal sends
and what the pipeline should make of it can both be read off the page. Tests
that modify a response must `copy.deepcopy` it first.
"""

ZONING_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-87.700, 41.800],
                            [-87.675, 41.800],
                            [-87.675, 41.900],
                            [-87.700, 41.900],
                            [-87.700, 41.800],
                        ]
                    ]
                ],
            },
            "properties": {"zone_class": "RS-3", "objectid": "1"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-87.675, 41.800],
                            [-87.625, 41.800],
                            [-87.625, 41.900],
                            [-87.675, 41.900],
                            [-87.675, 41.800],
                        ]
                    ]
                ],
            },
            "properties": {"zone_class": "RT-4", "objectid": "2"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-87.625, 41.800],
                            [-87.600, 41.800],
                            [-87.600, 41.900],
                            [-87.625, 41.900],
                            [-87.625, 41.800],
                        ]
                    ]
                ],
            },
            "properties": {"zone_class": "M1-1", "objectid": "3"},
        },
    ],
    "crs": {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    },
}

WARDS_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-87.700, 41.800],
                            [-87.650, 41.800],
                            [-87.650, 41.900],
                            [-87.700, 41.900],
                            [-87.700, 41.800],
                        ]
                    ]
                ],
            },
            "properties": {"ward": "1", "objectid": "10"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-87.650, 41.800],
                            [-87.600, 41.800],
                            [-87.600, 41.900],
                            [-87.650, 41.900],
                            [-87.650, 41.800],
                        ]
                    ]
                ],
            },
            "properties": {"ward": "2", "objectid": "20"},
        },
    ],
    "crs": {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    },
}

# The same zoning data split across two pages, for the pagination tests. A page
# is a complete FeatureCollection, crs member and all.
ZONING_PAGE_1 = {
    "type": "FeatureCollection",
    "features": ZONING_RESPONSE["features"][:2],
    "crs": ZONING_RESPONSE["crs"],
}

ZONING_PAGE_2 = {
    "type": "FeatureCollection",
    "features": ZONING_RESPONSE["features"][2:],
    "crs": ZONING_RESPONSE["crs"],
}
