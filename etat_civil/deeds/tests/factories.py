from factory import DjangoModelFactory, SubFactory
from factory.django import FileField

from etat_civil.deeds.models import Data, Source


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
