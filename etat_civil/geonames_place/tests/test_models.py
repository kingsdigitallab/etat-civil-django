import pytest

from etat_civil.geonames_place.models import Place


pytestmark = pytest.mark.django_db


class TestPlace:
    def test_to_list(self):
        place = Place(geonames_id=1, address="Place name", lat=1, lon=1)
        place_as_list = place.to_list()

        assert len(place_as_list) == 4
        assert place_as_list[0] == place.geonames_id
        assert place_as_list[1] == place.address
        assert place_as_list[2] == place.lat
        assert place_as_list[3] == place.lon
