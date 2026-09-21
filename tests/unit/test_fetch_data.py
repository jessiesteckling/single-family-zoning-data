"""How a portal response becomes a GeoDataFrame."""

import copy
import unittest
from unittest.mock import patch

from src import fetch_data
from src.constants import SOURCE_CRS
from tests.unit import fixtures

CRS84 = "urn:ogc:def:crs:OGC:1.3:CRS84"


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _patch_get(payloads):
    """Answer successive requests with successive payloads."""
    return patch.object(
        fetch_data.requests, "get", side_effect=[FakeResponse(p) for p in payloads]
    )


class FetchGeojsonTests(unittest.TestCase):
    def test_properties_become_columns(self):
        with _patch_get([fixtures.ZONING_RESPONSE]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(list(gdf["zone_class"]), ["RS-3", "RT-4", "M1-1"])
        self.assertEqual(list(gdf["objectid"]), ["1", "2", "3"])

    def test_geometry_is_parsed_with_its_coordinates_intact(self):
        with _patch_get([fixtures.ZONING_RESPONSE]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(list(gdf.geometry.geom_type), ["MultiPolygon"] * 3)
        self.assertEqual(
            [tuple(round(v, 3) for v in g.bounds) for g in gdf.geometry],
            [
                (-87.700, 41.800, -87.675, 41.900),
                (-87.675, 41.800, -87.625, 41.900),
                (-87.625, 41.800, -87.600, 41.900),
            ],
        )

    def test_ward_response_parses_to_its_two_wards(self):
        with _patch_get([fixtures.WARDS_RESPONSE]):
            gdf = fetch_data.fetch_geojson("p293-wvbd")

        self.assertEqual(list(gdf["ward"]), ["1", "2"])
        self.assertEqual(
            [tuple(round(v, 3) for v in g.bounds) for g in gdf.geometry],
            [
                (-87.700, 41.800, -87.650, 41.900),
                (-87.650, 41.800, -87.600, 41.900),
            ],
        )

    def test_crs_comes_from_what_the_response_declares(self):
        with _patch_get([fixtures.ZONING_RESPONSE]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs, CRS84)

    def test_a_response_with_no_crs_member_falls_back(self):
        payload = copy.deepcopy(fixtures.ZONING_RESPONSE)
        del payload["crs"]

        with _patch_get([payload]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs, SOURCE_CRS)

    def test_a_declared_crs_that_is_not_wgs84_is_honoured(self):
        payload = copy.deepcopy(fixtures.ZONING_RESPONSE)
        payload["crs"]["properties"]["name"] = "urn:ogc:def:crs:EPSG::3435"

        with _patch_get([payload]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs, "EPSG:3435")

    def test_pages_until_a_short_page_arrives(self):
        with patch.object(fetch_data, "PAGE_SIZE", 2), _patch_get(
            [fixtures.ZONING_PAGE_1, fixtures.ZONING_PAGE_2]
        ) as get:
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(list(gdf["zone_class"]), ["RS-3", "RT-4", "M1-1"])
        self.assertEqual(
            [call.args[0] for call in get.call_args_list],
            [
                "https://data.cityofchicago.org/resource/dj47-wfun.geojson"
                "?$limit=2&$offset=0",
                "https://data.cityofchicago.org/resource/dj47-wfun.geojson"
                "?$limit=2&$offset=2",
            ],
        )

    def test_the_declaration_is_read_from_the_first_page_only(self):
        second = copy.deepcopy(fixtures.ZONING_PAGE_2)
        del second["crs"]  # a later page dropping it must not clear the CRS

        with patch.object(fetch_data, "PAGE_SIZE", 2), _patch_get(
            [fixtures.ZONING_PAGE_1, second]
        ):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs, CRS84)

    def test_a_single_short_page_makes_exactly_one_request(self):
        with _patch_get([fixtures.WARDS_RESPONSE]) as get:
            fetch_data.fetch_geojson("p293-wvbd")

        self.assertEqual(
            [call.args[0] for call in get.call_args_list],
            [
                "https://data.cityofchicago.org/resource/p293-wvbd.geojson"
                "?$limit=5000&$offset=0"
            ],
        )


if __name__ == "__main__":
    unittest.main()
