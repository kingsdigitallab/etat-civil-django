import pandas as pd
import pytest
from django.utils.dateparse import parse_date

from etat_civil.deeds.models import (
    Data,
    Deed,
    DeedType,
    Gender,
    Person,
    Role,
    Source,
    Origin,
    OriginType,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("data")
class TestData:
    def test_load_data(self, data):
        no_data = Data(title="No data")
        loaded = no_data.load_data()
        assert loaded is False

        loaded = data.load_data()
        assert loaded

        deed_type = DeedType.get_birth()
        assert Deed.objects.filter(deed_type=deed_type).count() == 9

    def test_get_data_sheet(self, data):
        df = data.get_data_sheet(None)
        assert df is None

        df = data.get_data_sheet("births")
        assert len(df.index) == 9

    def test_convert_date_columns(self, data):
        df = pd.DataFrame(
            {"date": ["2019-12-24", "24/12/2019"], "location": ["Paris", "Alexandria"]}
        )

        df_none = data.convert_date_columns(None)
        assert df_none is None

        df = data.convert_date_columns(df)
        assert df is not None
        assert df["date"].dtype == "datetime64[ns]"

    def test_load_births(self, data):
        loaded = data.load_births(None)
        assert loaded is False

        df = data.get_data_sheet("births")
        loaded = data.load_births(df)
        assert loaded is True

        deed_type = DeedType.get_birth()
        assert Deed.objects.filter(deed_type=deed_type).count() == 9

    def test_get_place(self, data):
        locations_df = pd.DataFrame(
            {
                "id": [1, 2],
                "location": ["Paris", "Alexandria"],
                "geonames_id": [2988507, None],
                "lat": [48.853, None],
                "lon": [2.349, None],
                "display_name": ["1: Paris", "2: Alexandria"],
            }
        )
        locations_df = locations_df.set_index("display_name")

        data.locations_df = locations_df

        p, r = data.get_place("1: Paris")
        assert p is not None
        assert r == 1

        p, r = data.get_place("1: Paris")
        assert p is not None
        assert r == 0

        p, r = data.get_place("2: Alexandria")
        assert p is not None
        assert r == 2

        p, r = data.get_place("Port Said")
        assert p is not None
        assert r == -1

        p, r = data.get_place("Port Said")
        assert p is not None
        assert r == 0

        p, r = data.get_place("Unknown place name in the middle of nowhere")
        assert p is None
        assert r == -1

        p, r = data.get_place(None)
        assert p is None
        assert r == -1


@pytest.mark.usefixtures("data")
class TestSource:
    def test_load_source(self, data):
        source = Source.load_source(data, None, None)
        assert source is None

        source = Source.load_source(data, "Classmark 1", None)
        assert source is None

        source = Source.load_source(data, "Classmark 1", "Microfilm 1")
        assert source is not None


class TestDeedType:
    def test_get_birth(self):
        dt = DeedType.get_birth()
        assert dt.title == "birth"

    def test_get_death(self):
        dt = DeedType.get_death()
        assert dt.title == "death"

    def test_get_marriage(self):
        dt = DeedType.get_marriage()
        assert dt.title == "marriage"


@pytest.mark.django_db
@pytest.mark.usefixtures("data", "births_df", "source")
class TestDeed:
    def test_is_birth(self, data, births_df, source):
        deed = Deed.load_birth_deed(data, source, births_df.iloc[0])
        assert deed.is_birth

        # TODO: test for negative case

    def test_is_birth_legitimate(self, data, births_df, source):
        deed = Deed.load_birth_deed(data, source, births_df.iloc[0])
        assert deed.is_birth_legitimate

        deed = Deed.load_birth_deed(data, source, births_df.iloc[1])
        assert deed.is_birth_legitimate is False

    def test_load_birth_deed(self, data, births_df, source):
        row = births_df.iloc[1]

        deed = Deed.load_birth_deed(None, source, row)
        assert deed is None
        deed = Deed.load_birth_deed(data, None, row)
        assert deed is None
        deed = Deed.load_birth_deed(data, source, None)
        assert deed is None

        deed = Deed.load_birth_deed(data, source, row)
        assert deed is not None
        assert deed.n == 1045

    def test_get_deed_n(self, births_df):
        n = Deed.get_deed_n(None)
        assert n == -1

        n = Deed.get_deed_n(births_df.iloc[0])
        assert n == 0

        n = Deed.get_deed_n(births_df.iloc[1])
        assert n == 1045

    def test_get_deed_date(self, births_df):
        d = Deed.get_deed_date(None)
        assert d is None

        d = Deed.get_deed_date(births_df.iloc[0])
        assert d is not None
        assert d.year == 1818

    def test_get_deed_notes(self, births_df):
        n = Deed.get_deed_notes(None)
        assert n is None

        n = Deed.get_deed_notes(births_df.iloc[0])
        assert n is not None
        assert "true" in n.lower()


@pytest.mark.django_db
@pytest.mark.usefixtures("data", "deed", "births_df")
class TestPerson:
    def test_birthplace(self, data, deed, births_df):
        gender = Gender.get_f()
        label = "mother_"
        role = Role.get_mother()

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[0])
        assert person.birthplace is None

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[5])
        assert person.birthplace.place.address == "Marseille"

    def test_domicile(self, data, deed, births_df):
        gender = Gender.get_m()
        label = "father_"
        role = Role.get_father()

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[1])
        assert person.domicile.place.address == "Alexandria"

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[5])
        assert person.domicile.place.address == "Alexandria"

    def test_get_origins(self, data, deed, births_df):
        gender = Gender.get_m()
        label = "father_"
        role = Role.get_father()

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[5])
        assert "Alexandria" in person.get_origins()
        assert "Marseille" in person.get_origins()

    def test_get_professions(self, data, deed, births_df):
        gender = Gender.get_m()
        label = "father_"
        role = Role.get_father()

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[0])
        assert person.get_professions() is None

        person = Person.load_person(data, label, gender, role, deed, births_df.iloc[1])
        assert "Négociant" in person.get_professions()

    def test_load_father(self, data, deed, births_df):
        row = births_df.iloc[0]

        person = Person.load_father(None, deed, row)
        assert person is None
        person = Person.load_father(data, None, row)
        assert person is None
        person = Person.load_father(data, deed, None)
        assert person is None

        person = Person.load_father(data, deed, row)
        assert person is not None
        assert person.name == "Louis"
        assert person.age == 35

    def test_load_person(self, data, deed, births_df):
        gender = Gender.get_f()
        label = "mother_"
        role = Role.get_mother()

        row = births_df.iloc[0]
        person = Person.load_person(data, label, gender, role, deed, row)
        assert person is not None
        assert person.name == "Catherine"
        assert person.unknown is False

        row = births_df.iloc[8]
        person = Person.load_person(data, label, gender, role, deed, row)
        assert person is not None
        assert person.name == "Unknown"
        assert person.unknown

    def test_get_name_field(self, births_df):
        row = births_df.iloc[0]
        assert Person.get_name_field("father_name", row) == "Louis"
        assert Person.get_name_field("mother_name", row) == "Catherine"

        row = births_df.iloc[8]
        assert Person.get_name_field("father_name", row) == "Charles"
        assert Person.get_name_field("mother_name", row) == "Unknown"

    def test_get_age(self, births_df):
        row = births_df.iloc[0]
        assert Person.get_age("father_", row) == 35
        assert Person.get_age("mother_", row) is None

    def test_get_birth_date(self):
        deed_date = parse_date("1827-12-19")

        assert Person.get_birth_date(None, None) is None
        assert Person.get_birth_date(deed_date, None).year == 1827
        assert Person.get_birth_date(deed_date, 25).year == 1802

    def test_load_mother(self, data, deed, births_df):
        row = births_df.iloc[0]

        person = Person.load_mother(None, deed, row)
        assert person is None
        person = Person.load_mother(data, None, row)
        assert person is None
        person = Person.load_mother(data, deed, None)
        assert person is None

        person = Person.load_mother(data, deed, row)
        assert person is not None
        assert person.name == "Catherine"
        assert person.age is None


# @pytest.mark.django_db
@pytest.mark.usefixtures("data", "deed", "person", "births_df")
class TestOrigin:
    def test_load_origins(self, data, deed, person, births_df):
        row = births_df.iloc[0]

        origins = Origin.load_origins(None, person, "father_", deed, row)
        assert origins is None
        origins = Origin.load_origins(data, None, "father_", deed, row)
        assert origins is None
        origins = Origin.load_origins(data, person, None, deed, row)
        assert origins is None
        origins = Origin.load_origins(data, person, "father_", None, row)
        assert origins is None
        origins = Origin.load_origins(data, person, "father_", deed, None)
        assert origins is None

        origins = Origin.load_origins(data, person, "", deed, row)
        assert len(origins) == 1

        origins = Origin.load_origins(data, person, "father_", deed, row)
        assert len(origins) == 1

        origins = Origin.load_origins(data, person, "father_", deed, births_df.iloc[3])
        assert len(origins) == 2

    def test_load_origin(self, data, deed, person, births_df):
        address = "0051: Alexandrie"
        origin_type = OriginType.get_birth()

        origin = Origin.load_origin(None, person, address, origin_type)
        assert origin is None
        origin = Origin.load_origin(data, None, address, origin_type)
        assert origin is None
        origin = Origin.load_origin(data, person, None, origin_type)
        assert origin is None
        origin = Origin.load_origin(data, person, address, None)
        assert origin is None

        origin = Origin.load_origin(data, person, address, origin_type)
        assert origin is not None
        assert origin.place.address == "Alexandria"
