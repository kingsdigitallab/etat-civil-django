import pytest
from django.test import RequestFactory

from etat_civil.deeds.views import FlowmapFlowsView, FlowmapLocationsView, GeoJSONView

pytestmark = pytest.mark.django_db


class TestFlowmapFlowsView:
    def test_get(self, request_factory: RequestFactory):
        view = FlowmapFlowsView()

        request = request_factory.get("/fake-url/")

        response = view.get(request)
        content = response.content

        assert response.get("Content-Disposition") == 'attachment; filename="flows.tsv"'
        assert b"origin" in content
        assert b"dest" in content
        assert b"count" in content


class TestFlowmapLocationsView:
    def test_get(self, request_factory: RequestFactory):
        view = FlowmapLocationsView()

        request = request_factory.get("/fake-url/")

        response = view.get(request)
        content = response.content

        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="locations.tsv"'
        )
        assert b"id" in content
        assert b"name" in content
        assert b"lat" in content
        assert b"lon" in content


class TestGeoJSONView:
    def test_get(self, request_factory: RequestFactory):
        view = GeoJSONView()

        request = request_factory.get("/fake-url/")

        response = view.get(request)
        content = response.content

        assert (
            response.get("Content-Disposition") == 'attachment; filename="geojson.json"'
        )
        assert b"FeatureCollection" in content
        assert b"features" in content
