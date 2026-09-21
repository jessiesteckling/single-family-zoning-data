"""How a portal response becomes a GeoDataFrame."""

import unittest
from unittest.mock import patch

import pyproj

from src import fetch_data
from src.constants import SOURCE_CRS
from tests.unit import fixtures


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
    def test_properties_become_columns_and_geometry_is_parsed(self):
        with _patch_get([fixtures.zoning_response()]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(len(gdf), 3)
        self.assertEqual(
            list(gdf["zone_class"]), ["RS-3", "RT-4", "M1-1"]
        )
        self.assertEqual(set(gdf.geometry.geom_type), {"MultiPolygon"})

    def test_crs_comes_from_what_the_response_declares(self):
        payload = fixtures.zoning_response()
        declared = payload["crs"]["properties"]["name"]

        with _patch_get([payload]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs, pyproj.CRS.from_user_input(declared))

    def test_a_response_with_no_crs_member_falls_back(self):
        payload = fixtures.zoning_response()
        del payload["crs"]

        with _patch_get([payload]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs, SOURCE_CRS)

    def test_a_declared_crs_that_is_not_wgs84_is_honoured(self):
        payload = fixtures.zoning_response()
        payload["crs"]["properties"]["name"] = "urn:ogc:def:crs:EPSG::3435"

        with _patch_get([payload]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(gdf.crs.to_epsg(), 3435)

    def test_the_declaration_is_read_from_the_first_page_only(self):
        first = fixtures.collection(fixtures.zoning_features()[:2])
        second = fixtures.collection(fixtures.zoning_features()[2:])
        del second["crs"]  # a later page dropping it must not clear the CRS

        with patch.object(fetch_data, "PAGE_SIZE", 2), _patch_get([first, second]):
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertIsNotNone(gdf.crs)

    def test_pages_until_a_short_page_arrives(self):
        full = fixtures.collection(fixtures.zoning_features()[:2])
        last = fixtures.collection(fixtures.zoning_features()[2:])

        with patch.object(fetch_data, "PAGE_SIZE", 2), _patch_get([full, last]) as get:
            gdf = fetch_data.fetch_geojson("dj47-wfun")

        self.assertEqual(len(gdf), 3, "features from both pages are concatenated")
        offsets = [call.args[0].split("$offset=")[1] for call in get.call_args_list]
        self.assertEqual(offsets, ["0", "2"])

    def test_a_single_short_page_makes_exactly_one_request(self):
        with _patch_get([fixtures.ward_response()]) as get:
            fetch_data.fetch_geojson("p293-wvbd")

        self.assertEqual(get.call_count, 1)

    def test_request_url_targets_the_geojson_endpoint(self):
        with _patch_get([fixtures.ward_response()]) as get:
            fetch_data.fetch_geojson("p293-wvbd")

        url = get.call_args_list[0].args[0]
        self.assertIn("/p293-wvbd.geojson", url)
        self.assertIn("$limit=", url)


if __name__ == "__main__":
    unittest.main()
