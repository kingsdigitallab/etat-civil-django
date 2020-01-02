import datetime

from factory import DjangoModelFactory, Faker, SubFactory
from factory.django import FileField

from etat_civil.deeds.models import Data, Deed, DeedType, Person, Source
from etat_civil.geonames_place.models import Place


class DataFactory(DjangoModelFactory):
    title = "Test Data"
    data = FileField(from_file=open("data/raw/test.xlsx", "rb"))

    class Meta:
        model = Data
        django_get_or_create = ["title", "data"]


class SourceFactory(DjangoModelFactory):
    data = SubFactory(DataFactory)
    classmark = "Classmark 1"
    microfilm = "Microfilm 1"

    class Meta:
        model = Source
        django_get_or_create = ["data", "classmark", "microfilm"]


class DeedTypeFactory(DjangoModelFactory):
    title = "birth"

    class Meta:
        model = DeedType
        django_get_or_create = ["title"]


class PlaceFactory(DjangoModelFactory):
    geonames_id = 361058

    class Meta:
        model = Place
        django_get_or_create = ["geonames_id"]


class DeedFactory(DjangoModelFactory):
    deed_type = SubFactory(DeedTypeFactory)
    n = 1
    date = datetime.date(1820, 1, 1)
    place = SubFactory(PlaceFactory)
    source = SubFactory(SourceFactory)

    class Meta:
        model = Deed
        django_get_or_create = ["deed_type", "n", "date", "place", "source"]


class PersonFactory(DjangoModelFactory):
    name = Faker("name")
    surname = Faker("name")
    age = 40

    class Meta:
        model = Person
        django_get_or_create = ["name", "surname", "age"]
