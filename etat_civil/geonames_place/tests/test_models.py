import geocoder
import pytest
from django.conf import settings
from django.db.utils import IntegrityError
from etat_civil.geonames_place.models import Place

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestPlace:
    GEONAMES_ID = 2635167
    GEONAMES_ADDRESS = "United Kingdom"

    def test_save(self):
        place = Place(geonames_id=self.GEONAMES_ID)
        place.save()
        assert place.address == self.GEONAMES_ADDRESS

        with pytest.raises(IntegrityError):
            place = Place()
            place.save()

            place.geonames_id = self.GEONAMES_ID
            place.update_from_geonames = False
            place.save()

    def test_hydrate_from_geonames(self):
        place = Place()
        place.hydrate_from_geonames()
        assert place.address is None

        place.geonames_id = self.GEONAMES_ID
        place.hydrate_from_geonames()
        assert place.address == self.GEONAMES_ADDRESS

    def test__hydrate(self):
        place = Place(geonames_id=self.GEONAMES_ID)
        place._hydrate(None)
        assert place.address is None

        g = geocoder.geonames(
            place.geonames_id, key=settings.GEONAMES_KEY, method="details"
        )

        place._hydrate(g)
        assert place.address == self.GEONAMES_ADDRESS

    def test_to_list(self):
        place = Place(geonames_id=1, address="Address", lat=1, lon=1)
        place_as_list = place.to_list()

        assert len(place_as_list) == 4
        assert place_as_list[0] == place.geonames_id
        assert place_as_list[1] == place.address
        assert place_as_list[2] == place.lat
        assert place_as_list[3] == place.lon

    def test_create_or_update_from_geonames(self):
        assert Place.create_or_update_from_geonames(None) == 0
        assert Place.create_or_update_from_geonames("un") == 0
        assert (
            Place.create_or_update_from_geonames(self.GEONAMES_ADDRESS)
            == settings.GEONAMES_MAX_RESULTS
        )

    def test_get_or_create_from_geonames(self):
        assert Place.get_or_create_from_geonames(None) is None
        assert Place.get_or_create_from_geonames("un") is None

        place = Place.get_or_create_from_geonames(self.GEONAMES_ADDRESS)
        assert place is not None
        assert place.geonames_id == self.GEONAMES_ID

    def test_places_to_csv(self, tmpdir):
        p = tmpdir.mkdir("places").join("places.tsv")

        Place.places_to_csv(p)
        assert "id" in p.read()
        assert "," in p.read()
        assert len(tmpdir.listdir()) == 1

        Place.objects.get_or_create(geonames_id=1, address="Address", lat=1, lon=1)

        Place.places_to_csv(p, delimiter="\t")
        assert "Address" in p.read()
        assert "\t" in p.read()
        assert len(tmpdir.listdir()) == 1
