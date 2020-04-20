from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext as _
from etat_civil.geonames_place.models import Place
from model_utils.models import TimeStampedModel


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

        marriages_df = self.get_data_sheet("marriages")
        self.load_marriages(marriages_df)

        deaths_df = self.get_data_sheet("deaths")
        self.load_deaths(deaths_df)

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
        return self.load_deed(births_df, Deed.load_birth_deed)

    def load_deed(self, df, load_func):
        if df is None:
            return False

        for index, row in df.iterrows():
            try:
                source = Source.load_source(
                    self, row["classmark"], row["classmark_microfilm"]
                )
                if source:
                    load_func(self, source, row)
            except Exception as e:  # noqa
                print(load_func, index, e)
                continue

        return True

    def load_marriages(self, marriages_df):
        return self.load_deed(marriages_df, Deed.load_marriage_deed)

    def load_deaths(self, deaths_df):
        return self.load_deed(deaths_df, Deed.load_death_deed)

    def get_place(self, name):
        """Returns a geonames place and a return code, and updates the internal
        place name cache, `locations_df`, when new places get a `geonames_id`.
        Code 0, the place was found in the location cache; code 1, the place was
        searched in geonames by geonames id; code 2, the place was searched in
        geonames by name; code 3, the place was searched in geonames by lat, lon;
        code -1, the place was not in the cache and was searched in geonames by
        name."""
        if not name:
            return None, -1

        code = 0
        name = name.strip()
        address = name

        try:
            location = self.locations_df.loc[name]
            address = location["location"].strip()
            geonames_id = location["geonames_id"]

            if pd.notnull(geonames_id):
                # get place by geonames id
                place, created = Place.objects.get_or_create(
                    geonames_id=int(geonames_id)
                )
                if created:
                    code = 1
            elif pd.notnull(location["lat"]) and pd.notnull(location["lon"]):
                # get place by lat, lon
                lat = location["lat"]
                lon = location["lon"]
                geonames_id = f"-{int(lat*10000)}{int(lon*10000)}"
                place, created = Place.objects.get_or_create(
                    geonames_id=int(geonames_id),
                    update_from_geonames=False,
                    lat=location["lat"],
                    lon=location["lon"],
                )
                if created:
                    code = 3
                    place.address = address
                    place.save()
            else:
                # get place by name
                place = Place.get_or_create_from_geonames(address=address)
                code = 2
        except KeyError:
            code = -1

            new_location_df = pd.DataFrame(
                [[name, name]], columns=["display_name", "location"], index=[name]
            )
            self.locations_df = self.locations_df.append(new_location_df, sort=True)
            self.locations_df.set_index("display_name")

            # get place by name
            place = Place.get_or_create_from_geonames(address=name)

        # updates the locations cache
        if place:
            self.locations_df.loc[name, "geonames_id"] = place.geonames_id

            place.address = address
            place.update_from_geonames = False
            place.save()

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
        if pd.notnull(classmark):
            classmark = classmark.strip()
        else:
            return None

        if pd.notnull(microfilm):
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

    @staticmethod
    def load_marriage_deed(data, source, row):
        if data is None or source is None or row is None:
            return None

        deed_type = DeedType.get_marriage()
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

        Person.load_groom(data, deed, row)
        Person.load_bride(data, deed, row)

        return deed

    @staticmethod
    def load_death_deed(data, source, row):
        if data is None or source is None or row is None:
            return None

        deed_type = DeedType.get_death()
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

        Person.load_deceased(data, deed, row)

        return deed


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
    def fullname(self):
        fullname = ""

        for n in [self.name, self.surname]:
            if n:
                fullname = f"{fullname} {n}"

        return fullname.strip()

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

    def get_flows(self):
        """Returns a list of origins/destinations that a person moved from/to."""
        flows = []

        orig_place = None

        for idx, origin in enumerate(self.get_origins()):
            dest_place = origin.place

            if idx > 0 and orig_place:
                flows.append((orig_place.geonames_id, dest_place.geonames_id))

            orig_place = origin.place

        return flows

    def get_origins(self, order_by=["order", "date"]):
        if isinstance(order_by, list):
            return self.origin_from.order_by(*order_by)

        return self.origin_from.order_by(order_by)

    def get_origin_names(self):
        origins = ""

        place = None
        for origin in self.get_origins():
            if origin.place != place:
                place = origin.place
                origins = f"{origins} -> {origin.origin_type}: {place}"

        return origins.strip()

    def get_professions(self):
        professions = []

        for p in self.party_to.all():
            if p.profession and p.profession.title not in professions:
                professions.append(p.profession.title)

        if len(professions) == 0:
            return None

        return ", ".join(professions)

    def to_geojson(self):
        geojson = {}

        if self.origin_from.count() == 0:
            return geojson

        geojson["type"] = "Feature"

        geometry = {}
        geometry["type"] = "LineString"

        coords = []
        properties = {}

        properties["id"] = self.id
        properties["name"] = self.fullname
        properties["unknown"] = self.unknown
        properties["origins"] = self.get_origin_names()

        if self.age:
            properties["age"] = self.age

        if self.gender:
            properties["gender"] = self.gender.title

        prev_place = None
        origins = self.get_origins()
        for idx, origin in enumerate(origins):
            if idx == 0 or idx == origins.count() - 1:
                pos = "first" if idx == 0 else "last"

                origin_geojson = origin.to_geojson(label=f"origin_{pos}")
                if origin_geojson:
                    properties.update(origin_geojson)

            if origin.place != prev_place:
                ts = datetime.fromordinal(origin.date.toordinal()).timestamp()
                coords.append(
                    [float(origin.place.lon), float(origin.place.lat), 0, int(ts)]
                )

            prev_place = origin.place

        geojson["properties"] = properties
        geometry["coordinates"] = coords
        geojson["geometry"] = geometry

        return geojson

    @staticmethod
    def load_father(data, deed, row):
        if data is None or deed is None or row is None:
            return None

        role = Role.get_father()
        label = "father_"
        gender = Gender.get_m()

        return Person.load_person(data, label, gender, role, deed, row)

    @staticmethod
    def load_person(data, label, gender, role, deed, row, from_death_deed=False):
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

        Origin.load_origins(
            data, person, label, deed, row, from_death_deed=from_death_deed
        )

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

        try:
            if pd.notnull(age):
                return int(age)
        except ValueError:
            return None

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

    @staticmethod
    def load_groom(data, deed, row):
        if data is None or deed is None or row is None:
            return None

        role = Role.get_groom()
        label = "groom_"
        gender = Gender.get_m()

        return Person.load_person(data, label, gender, role, deed, row)

    @staticmethod
    def load_bride(data, deed, row):
        if data is None or deed is None or row is None:
            return None

        role = Role.get_bride()
        label = "bride_"
        gender = Gender.get_f()

        return Person.load_person(data, label, gender, role, deed, row)

    @staticmethod
    def load_deceased(data, deed, row):
        if data is None or deed is None or row is None:
            return None

        role = Role.get_deceased()
        label = ""
        gender = None

        return Person.load_person(
            data, label, gender, role, deed, row, from_death_deed=True
        )

    @staticmethod
    def persons_to_flows():
        """Exports all the persons flows into a list of tupples, containing the origin,
        destination, and count for each flow"""
        flows = []

        for person in Person.objects.all():
            flows.extend(person.get_flows())

        counter = Counter(flows)

        return [[k[0], k[1], counter[k]] for k in counter.keys()]

    @staticmethod
    def persons_to_geojson():
        geo = {}
        geo["type"] = "FeatureCollection"
        geo["features"] = []

        for person in Person.objects.all():
            feature = person.to_geojson()
            if feature:
                geo["features"].append(feature)

        return geo


class OriginType(BaseAL):
    @staticmethod
    def get_birth():
        return OriginType.objects.get(title="birth")

    @staticmethod
    def get_death():
        return OriginType.objects.get(title="death")

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

    def to_geojson(self, label="origin"):
        geojson = {}

        geojson[f"{label}_type"] = self.origin_type.title
        geojson[f"{label}_place"] = self.place.address
        geojson[f"{label}_lat"] = float(self.place.lat)
        geojson[f"{label}_lon"] = float(self.place.lon)
        geojson[f"{label}_date"] = f"{self.date} 00:00"
        geojson[f"{label}_is_date_computed"] = self.is_date_computed

        return geojson

    @staticmethod
    def load_origins(data, person, person_label, deed, row, from_death_deed=False):
        if (
            data is None
            or person is None
            or person_label is None
            or deed is None
            or row is None
        ):
            return None

        origins = []

        address = row.get(f"{person_label}domicile")
        if pd.isnull(address):
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

        birth_date = Person.get_birth_date(deed.date, person.age)

        is_date_computed = False
        if not person.age:
            is_date_computed = True

        address = row.get(f"{person_label}birth_location")
        if pd.notnull(address):
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

        if from_death_deed:
            origins.append(
                Origin.load_origin(
                    data,
                    person,
                    deed.place.address,
                    OriginType.get_death(),
                    origin_date=deed.date,
                    order=8,
                )
            )
        else:
            address = row.get(f"{person_label}previous_domicile_location")
            if pd.notnull(address):
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
        if data is None or person is None or pd.isnull(address) or origin_type is None:
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

    @staticmethod
    def get_groom():
        return Role.objects.get(title="groom")

    @staticmethod
    def get_bride():
        return Role.objects.get(title="bride")

    @staticmethod
    def get_deceased():
        return Role.objects.get(title="deceased")


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
        if person is None or label is None or role is None or deed is None:
            return None

        profession = Party.get_profession(label, row)

        party, _ = Party.objects.get_or_create(
            deed=deed, person=person, role=role, profession=profession
        )

        return party

    @staticmethod
    def get_profession(label, row):
        if label is None or row is None:
            return None

        title = row[f"{label}profession"]

        if pd.isnull(title):
            return None

        profession, _ = Profession.objects.get_or_create(title=title.strip())
        return profession
