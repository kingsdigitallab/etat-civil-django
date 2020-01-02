from datetime import timedelta

import pandas as pd
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel

from etat_civil.geonames_place.models import Place


class BaseAL(TimeStampedModel):
    title = models.CharField(max_length=128, unique=True)

    class Meta:
        abstract = True
        ordering = ["title"]

    def __str__(self):
        return self.title


class Data(TimeStampedModel):
    title = models.CharField(max_length=64, unique=True)
    data = models.FileField(
        upload_to="uploads/data/",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx"])],
    )

    locations_df = None

    class Meta:
        verbose_name_plural = "Data"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.locations_df = self.get_data_sheet("locations").set_index("display_name")
        super().save(*args, **kwargs)

    def load_data(self, delete=False):
        if not self.data:
            return False

        if self.delete:
            self.sources.all().delete()

        births_df = self.get_data_sheet("births")
        self.load_births(births_df)

        # marriages_df = self.get_data_sheet('marriages')
        # import_marriages(data, marriages_df, locations_df)

        # deaths_df = self.get_data_sheet('deaths')
        # import_deaths(data, deaths_df, locations_df)

        return True

    def get_data_sheet(self, sheet_name):
        if not sheet_name:
            return None

        df = pd.read_excel(self.data, engine="openpyxl", sheet_name=sheet_name)
        df = df.dropna(how="all")

        df = self.convert_date_columns(df)

        return df

    def convert_date_columns(self, df):
        if df is None:
            return None

        date_columns = filter(lambda x: "date" in x, df.columns)
        for c in date_columns:
            df[c] = pd.to_datetime(df[c], errors="ignore")

        return df

    def load_births(self, births_df):
        if births_df is None:
            return False

        for index, row in births_df.iterrows():
            try:
                source = Source.load_source(
                    self, row["classmark"], row["classmark_microfilm"]
                )
                if source:
                    Deed.load_birth_deed(self, source, row)
            except Exception as e:  # noqa
                print("birth", index, e)
                # skips the row
                continue

        return True

    def get_place(self, name):
        """Returns a geonames place and a return code, and updates the internal
        place name cache, `locations_df`, when new places get a `geonames_id`.
        Code 0, the place was found in the location cache; code 1, the place was
        searched in geonames using a geonames id; code 2, the place name was
        found in the cache but the place details were harvested from geonames;
        code -1, the place was not in the cache and was searched in geonames by
        name."""
        if not name:
            return None, -1

        code = 0
        name = name.strip()

        try:
            location = self.locations_df.loc[name]
            geonames_id = location["geonames_id"]

            if pd.notna(geonames_id):
                place, created = Place.objects.get_or_create(
                    geonames_id=int(geonames_id)
                )
                if created:
                    code = 1

                return place, code

            code = 2
        except KeyError:
            code = -1

            new_location_df = pd.DataFrame(
                [[name, name]], columns=["display_name", "location"], index=[name]
            )
            self.locations_df = self.locations_df.append(new_location_df, sort=True)
            self.locations_df.set_index("display_name")

        place = Place.get_or_create_from_geonames(address=name)

        # updates the locations cache
        if place:
            self.locations_df.loc[name, "geonames_id"] = place.geonames_id

        return place, code


class Source(TimeStampedModel):
    data = models.ForeignKey(Data, on_delete=models.CASCADE, related_name="sources")
    classmark = models.CharField(max_length=32)
    microfilm = models.CharField(max_length=32)

    class Meta:
        unique_together = ["data", "classmark", "microfilm"]

    def __str__(self):
        return "{}: {}".format(self.classmark, self.microfilm)

    @staticmethod
    def load_source(data, classmark, microfilm):
        if pd.notna(classmark):
            classmark = classmark.strip()
        else:
            return None

        if pd.notna(microfilm):
            microfilm = microfilm.strip()
        else:
            return None

        source, _ = Source.objects.get_or_create(
            data=data, classmark=classmark, microfilm=microfilm
        )

        return source


class DeedType(BaseAL):
    @staticmethod
    def get_birth():
        return DeedType.objects.get(title="birth")

    @staticmethod
    def get_death():
        return DeedType.objects.get(title="death")

    @staticmethod
    def get_marriage():
        return DeedType.objects.get(title="marriage")


class Deed(TimeStampedModel):
    deed_type = models.ForeignKey(DeedType, on_delete=models.CASCADE)
    n = models.PositiveSmallIntegerField(blank=True, null=True)
    date = models.DateField(help_text=_("Date of the deed record"))
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="deeds",
        help_text=_("Place of the deed record"),
    )
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    parties = models.ManyToManyField(
        "Person", through="Party", through_fields=("deed", "person")
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ["n", "date", "place"]

    def __str__(self):
        return "{}: {} - {}; {}".format(self.deed_type, self.n, self.date, self.place)

    @property
    def is_birth(self):
        return self.deed_type == DeedType.get_birth()

    @property
    def is_birth_legitimate(self):
        return self.is_birth and "legitimate birth: true" in self.notes.lower()

    @staticmethod
    def load_birth_deed(data, source, row):
        if data is None or source is None or row is None:
            return None

        deed_type = DeedType.get_birth()
        deed_n = Deed.get_deed_n(row)
        deed_date = Deed.get_deed_date(row)
        deed_place, _ = data.get_place(row["deed_location"])
        deed_notes = Deed.get_deed_notes(row)

        deed, _ = Deed.objects.get_or_create(
            deed_type=deed_type,
            n=deed_n,
            date=deed_date,
            place=deed_place,
            source=source,
            notes=deed_notes,
        )

        Person.load_father(data, deed, row)
        Person.load_mother(data, deed, row)

        return deed

    @staticmethod
    def get_deed_n(row):
        if row is None:
            return -1

        try:
            return int(row["deed_number"])
        except (KeyError, ValueError):
            return 0

    @staticmethod
    def get_deed_date(row):
        if row is None or "deed_date" not in row:
            return None

        deed_date = row["deed_date"]

        if isinstance(deed_date, str):
            deed_date = pd.to_datetime(deed_date).date()

        return deed_date

    @staticmethod
    def get_deed_notes(row):
        if row is None:
            return None

        notes = row["comments"]

        try:
            notes = f'Legitimate birth: {row["birth_legitimate"]}; {notes}'
            notes = notes.strip()
        except KeyError:
            pass

        return notes


class Gender(BaseAL):
    @staticmethod
    def get_f():
        return Gender.objects.get(title="f")

    @staticmethod
    def get_m():
        return Gender.objects.get(title="m")


class Person(TimeStampedModel):
    name = models.CharField(max_length=128, blank=True, null=True)
    surname = models.CharField(max_length=128, blank=True, null=True)
    unknown = models.BooleanField(default=False)
    gender = models.ForeignKey(Gender, blank=True, null=True, on_delete=models.CASCADE)
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    birth_year = models.PositiveSmallIntegerField(blank=True, null=True)
    origins = models.ManyToManyField(
        Place, through="Origin", through_fields=("person", "place")
    )

    class Meta:
        ordering = ["surname", "name", "age"]

    def __str__(self):
        return "{} {}".format(self.name, self.surname)

    def save(self, *args, **kwargs):
        if self.unknown and not self.surname:
            self.surname = Person.objects.filter(unknown=True).count()

        super().save(*args, **kwargs)

    @property
    def birthplace(self):
        origin_type = OriginType.objects.get(title="birth")
        origins = self.origin_from.filter(origin_type=origin_type)

        if origins:
            return origins.first()

        return None

    @property
    def domicile(self):
        origin_type = OriginType.objects.get(title="domicile")
        origins = self.origin_from.filter(origin_type=origin_type).order_by("order")

        if origins:
            return origins.last()

        return None

    def get_origins(self):
        origins = ""

        for o in self.origin_from.order_by("order"):
            origins = "{} {} {}".format(origins, ">" if origins else "", o.place)

        return origins.strip()

    def get_professions(self):
        professions = []

        for p in self.party_to.all():
            if p.profession and p.profession.title not in professions:
                professions.append(p.profession.title)

        if len(professions) == 0:
            return None

        return ", ".join(professions)

    @staticmethod
    def load_father(data, deed, row):
        if data is None or deed is None or row is None:
            return None

        role = Role.get_father()
        label = "father_"
        gender = Gender.get_m()

        return Person.load_person(data, label, gender, role, deed, row)

    @staticmethod
    def load_person(data, label, gender, role, deed, row):
        unknown = False

        name = Person.get_name_field(f"{label}name", row)
        surname = Person.get_name_field(f"{label}surname", row)

        if name == "Unknown":
            unknown = True

        age = Person.get_age(label, row)
        birth_year = None

        if age:
            birth_date = Person.get_birth_date(deed.date, age)
            birth_year = birth_date.year

        person, created = Person.objects.get_or_create(
            name=name,
            surname=surname,
            unknown=unknown,
            gender=gender,
            birth_year=birth_year,
        )

        if created:
            person.age = age
            person.save()

        Origin.load_origins(data, person, label, deed, row)

        Party.load_party(person, label, role, deed, row)

        return person

    @staticmethod
    def get_name_field(field, row):
        name = row[field]
        if pd.isnull(name):
            return None

        name = name.strip()
        if "inconnu" in name:
            return "Unknown"

        return name

    @staticmethod
    def get_age(label, row):
        age = row[f"{label}age"]
        if pd.notna(age):
            return int(age)

        return None

    @staticmethod
    def get_birth_date(deed_date, age):
        if not deed_date:
            return None

        if not age or age == 0:
            return deed_date

        delta = age * timedelta(days=365)
        return deed_date - delta

    @staticmethod
    def load_mother(data, deed, row):
        if data is None or deed is None or row is None:
            return None

        role = Role.get_mother()
        label = "mother_"
        gender = Gender.get_f()

        return Person.load_person(data, label, gender, role, deed, row)


class OriginType(BaseAL):
    @staticmethod
    def get_birth():
        return OriginType.objects.get(title="birth")

    @staticmethod
    def get_domicile():
        return OriginType.objects.get(title="domicile")


class Origin(TimeStampedModel):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="origin_from"
    )
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="origin_of")
    origin_type = models.ForeignKey(OriginType, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    is_date_computed = models.BooleanField(
        help_text=_(
            "Wether the date was computed using the person birth date "
            "and the date of the deed"
        )
    )
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "{}: {}".format(self.origin_type, self.place)

    @staticmethod
    def load_origins(data, person, person_label, deed, row):
        if (
            data is None
            or person is None
            or person_label is None
            or deed is None
            or row is None
        ):
            return None

        origins = []

        address = row[f"{person_label}domicile"]
        if pd.isna(address):
            address = deed.place.address

        origins.append(
            Origin.load_origin(
                data,
                person,
                address,
                OriginType.get_domicile(),
                origin_date=deed.date,
                order=5,
            )
        )

        address = row[f"{person_label}birth_location"]
        is_date_computed = False

        if person.age:
            birth_date = Person.get_birth_date(deed.date, person.age)
        else:
            birth_date = Person.get_birth_date(deed.date, person.age)
            is_date_computed = True

        origins.append(
            Origin.load_origin(
                data,
                person,
                address,
                OriginType.get_birth(),
                origin_date=birth_date,
                is_date_computed=is_date_computed,
                order=1,
            )
        )

        try:
            address = row[f"{person_label}previous_domicile_location"]

            previous_domicile_date = birth_date + (deed.date - birth_date) / 2
            is_date_computed = True

            origins.append(
                Origin.load_origin(
                    data,
                    person,
                    address,
                    OriginType.get_domicile(),
                    origin_date=previous_domicile_date,
                    is_date_computed=is_date_computed,
                    order=3,
                )
            )
        except KeyError:
            pass

        return list(filter(lambda o: o is not None, origins))

    @staticmethod
    def load_origin(
        data,
        person,
        address,
        origin_type,
        origin_date=None,
        is_date_computed=False,
        order=99,
    ):
        if data is None or person is None or address is None or origin_type is None:
            return None

        place, _ = data.get_place(address)
        if place is None:
            return None

        origin, _ = Origin.objects.get_or_create(
            person=person,
            place=place,
            origin_type=origin_type,
            date=origin_date,
            is_date_computed=is_date_computed,
            order=order,
        )

        return origin


class Profession(BaseAL):
    pass


class Role(BaseAL):
    @staticmethod
    def get_father():
        return Role.objects.get(title="father")

    @staticmethod
    def get_mother():
        return Role.objects.get(title="mother")


class Party(TimeStampedModel):
    deed = models.ForeignKey(Deed, on_delete=models.CASCADE)
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="party_to"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    profession = models.ForeignKey(
        Profession, blank=True, null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Parties"

    @staticmethod
    def load_party(person, label, role, deed, row):
        profession = Party.get_profession(label, row)

        party, _ = Party.objects.get_or_create(
            deed=deed, person=person, role=role, profession=profession
        )

        return party

    @staticmethod
    def get_profession(label, row):
        title = row[f"{label}profession"]

        if pd.notna(title):
            profession, _ = Profession.objects.get_or_create(title=title.strip())
            return profession

        return None


# def import_marriages(data, marriages_df, locations_df):
#     deed_type = DeedType.objects.get(title="marriage")

#     for index, row in marriages_df.iterrows():
#         try:
#             deed_date = get_deed_date(row)
#             place = get_place(locations_df, row["deed_location"].strip())
#             source = import_source(data, row)
#             import_marriage_record(
#                 deed_type, deed_date, place, source, row, locations_df
#             )
#         except Exception as e:  # noqa
#             print("marriage", index, e)
#             # skips the row
#             continue


# def import_marriage_record(deed_type, deed_date, place, source, record, locations_df):
#     deed = import_deed(deed_type, deed_date, place, source, record)

#     gender, _ = Gender.objects.get_or_create(title="m")
#     groom = import_person("groom_", gender, deed_date, record, locations_df)
#     role = Role.objects.get(title="groom")
#     add_party(deed, groom, role, "groom_", record)

#     gender, _ = Gender.objects.get_or_create(title="f")
#     bride = import_person("bride_", gender, deed_date, record, locations_df)
#     role = Role.objects.get(title="bride")
#     add_party(deed, bride, role, "bride_", record)


# def import_deaths(data, deaths_df, locations_df):
#     deed_type = DeedType.objects.get(title="death")

#     for index, row in deaths_df.iterrows():
#         try:
#             deed_date = get_deed_date(row)
#             place = get_place(locations_df, row["deed_location"].strip())
#             source = import_source(data, row)
#           import_death_record(deed_type, deed_date, place, source, row, locations_df)
#         except Exception as e:  # noqa
#             print("death", index, e)
#             continue


# def import_death_record(deed_type, deed_date, place, source, record, locations_df):
#     deed = import_deed(deed_type, deed_date, place, source, record)

#     deceased = import_person("", None, deed_date, record, locations_df)
#     role = Role.objects.get(title="deceased")
#     add_party(deed, deceased, role, "", record)
