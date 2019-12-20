from datetime import datetime, timedelta

import pandas as pd
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext as _
from geonames_place.models import Place
from model_utils.models import TimeStampedModel


class BaseAL(TimeStampedModel):
    title = models.CharField(max_length=128, unique=True)

    class Meta:
        abstract = True
        ordering = ['title']

    def __str__(self):
        return self.title


class DeedType(BaseAL):
    pass


class Data(TimeStampedModel):
    title = models.CharField(max_length=64, unique=True)
    data = models.FileField(
        upload_to='uploads/data/',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx'])]
    )

    class Meta:
        verbose_name_plural = 'Data'

    def __str__(self):
        return self.title


class Gender(BaseAL):
    pass


class Person(TimeStampedModel):
    name = models.CharField(max_length=128, blank=True, null=True)
    surname = models.CharField(max_length=128, blank=True, null=True)
    gender = models.ForeignKey(
        Gender, blank=True, null=True, on_delete=models.CASCADE)
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    birth_year = models.PositiveSmallIntegerField(blank=True, null=True)
    origins = models.ManyToManyField(
        Place, through='Origin', through_fields=('person', 'place'))

    class Meta:
        ordering = ['surname', 'name', 'age']

    def __str__(self):
        return '{} {}'.format(self.name, self.surname)

    def get_origins(self):
        origins = ''

        for o in self.origin_from.order_by('order'):
            origins = '{} {} {}'.format(
                origins, '>' if origins else '', o.place)

        return origins.strip()

    def get_professions(self):
        professions = []

        for p in self.party_to.all():
            if p.profession and p.profession.title not in professions:
                professions.append(p.profession.title)

        return ', '.join(professions)

    @property
    def birthplace(self):
        origin_type = OriginType.objects.get(title='birth')
        origins = self.origin_from.filter(origin_type=origin_type)

        if origins:
            return origins.first()

        return None

    @property
    def domicile(self):
        origin_type = OriginType.objects.get(title='domicile')
        origins = self.origin_from.filter(
            origin_type=origin_type).order_by('order')

        if origins:
            return origins.last()

        return None


class OriginType(BaseAL):
    pass


class Origin(TimeStampedModel):
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name='origin_from')
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE, related_name='origin_of')
    origin_type = models.ForeignKey(OriginType, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    is_date_computed = models.BooleanField(
        help_text=_('Wether the date was computed using the person birth date '
                    'and the date of the deed')
    )
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '{}: {}'.format(self.origin_type, self.place)


class Profession(BaseAL):
    pass


class Role(BaseAL):
    pass


class Source(TimeStampedModel):
    data = models.ForeignKey(Data, on_delete=models.CASCADE)
    classmark = models.CharField(max_length=32)
    microfilm = models.CharField(max_length=32)

    class Meta:
        unique_together = ['data', 'classmark', 'microfilm']

    def __str__(self):
        return '{}: {}'.format(self.classmark, self.microfilm)


class Deed(TimeStampedModel):
    deed_type = models.ForeignKey(DeedType, on_delete=models.CASCADE)
    n = models.PositiveSmallIntegerField(blank=True, null=True)
    date = models.DateField(help_text=_('Date of the deed record'))
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE,
        related_name='deeds', help_text=_('Place of the deed record'))
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    parties = models.ManyToManyField(
        Person, through='Party', through_fields=('deed', 'person'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['n', 'date', 'place']

    def __str__(self):
        return '{}: {} - {}; {}'.format(
            self.deed_type, self.n, self.date, self.place)


class Party(TimeStampedModel):
    deed = models.ForeignKey(Deed, on_delete=models.CASCADE)
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="party_to")
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    profession = models.ForeignKey(
        Profession, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Parties'


def import_data(data):
    assert data is not None

    locations_df = get_data_sheet(data, 'locations').set_index('display_name')

    births_df = get_data_sheet(data, 'births')
    import_births(data, births_df, locations_df)

    marriages_df = get_data_sheet(data, 'marriages')
    import_marriages(data, marriages_df, locations_df)

    deaths_df = get_data_sheet(data, 'deaths')
    import_deaths(data, deaths_df, locations_df)


def get_data_sheet(data, sheet_name):
    df = pd.read_excel(data.data, sheet_name=sheet_name)
    df = df.dropna(how='all')

    df = convert_date_columns(df)

    return df


def convert_date_columns(df):
    date_columns = filter(lambda x: 'date' in x, df.columns)
    for c in date_columns:
        df[c] = pd.to_datetime(df[c], errors='ignore')

    return df


def import_births(data, births_df, locations_df):
    deed_type = DeedType.objects.get(title='birth')

    for index, row in births_df.iterrows():
        try:
            deed_date = get_deed_date(row)
            place = get_place(locations_df, row['deed_location'].strip())
            source = import_source(data, row)
            import_birth_record(
                deed_type, deed_date, place, source, row, locations_df)
        except Exception as e:  # noqa
            print('birth', index, e)
            # skips the row
            continue


def get_deed_date(record):
    deed_date = record['deed_date']

    if isinstance(deed_date, str):
        deed_date = pd.to_datetime(deed_date).date()

    return deed_date


def get_place(locations_df, name):
    try:
        location = locations_df.loc[name]

        if pd.notna(location['geonames_id']):
            place, _ = Place.objects.get_or_create(
                geonames_id=int(location['geonames_id']))
            return place
        else:
            return Place.get_or_create_from_geonames(
                address=location['location'])
    except KeyError:
        return None


def import_source(data, record):
    assert record is not None

    classmark = record['classmark']
    if pd.notna(classmark):
        classmark = classmark.strip()
    else:
        return None

    microfilm = record['classmark_microfilm']
    if pd.notna(microfilm):
        microfilm = microfilm.strip()
    else:
        microfilm = None

    source, _ = Source.objects.get_or_create(
        data=data, classmark=classmark, microfilm=microfilm)

    return source


def import_birth_record(
        deed_type, deed_date, place, source, record, locations_df):
    deed = import_deed(deed_type, deed_date, place, source, record)

    gender, _ = Gender.objects.get_or_create(title='m')
    father = import_person('father_', gender, deed_date, record, locations_df)
    role = Role.objects.get(title='father')
    add_party(deed, father, role, 'father_', record)

    gender, _ = Gender.objects.get_or_create(title='f')
    mother = import_person('mother_', gender, deed_date, record, locations_df)
    role = Role.objects.get(title='mother')
    add_party(deed, mother, role, 'mother_', record)


def import_deed(deed_type, deed_date, place, source, record):
    n = record['deed_number']
    try:
        n = int(n)
    except ValueError:
        n = 0

    try:
        notes = 'Legitimate birth: {}'.format(record['birth_legitimate'])
    except KeyError:
        notes = None

    deed, _ = Deed.objects.get_or_create(
        deed_type=deed_type, n=n, date=deed_date, place=place,
        source=source, notes=notes
    )

    return deed


def import_person(label, gender, deed_date, record, locations_df):
    name = record[f'{label}name']
    if pd.notna(name):
        name = name.strip()
    else:
        name = None

    surname = record[f'{label}surname']
    if pd.notna(surname):
        surname = surname.strip()
    else:
        surname = None

    age = record[f'{label}age']
    birth_date = None
    birth_year = None

    if pd.notna(age):
        birth_date = get_date_of_birth(deed_date, int(age))
        birth_year = birth_date.year
    else:
        age = None

    person, created = Person.objects.get_or_create(
        name=name, surname=surname, gender=gender, birth_year=birth_year
    )

    if created:
        person.age = age
        person.save()

    add_origins(person, label, deed_date, birth_date, record, locations_df)

    return person


def get_date_of_birth(deed_date, age):
    assert deed_date is not None
    assert age is not None

    delta = age * timedelta(days=365)

    return (deed_date - delta)


def add_origins(person, label, deed_date, birth_date, record, locations_df):
    address = record[f'{label}domicile']
    add_origin(person, address, locations_df,
               'domicile', date=deed_date, order=5)

    is_date_computed = False

    # estimates the date of birth
    if not birth_date:
        birth_date = get_date_of_birth(deed_date, 25)
        is_date_computed = True

    address = record[f'{label}birth_location']
    add_origin(person, address, locations_df, 'birth',
               date=birth_date, is_date_computed=is_date_computed, order=1)

    is_date_computed = False

    try:
        # estimates the date of the previous domicile
        pdd = None
        if deed_date and birth_date:
            pdd = birth_date + (deed_date - birth_date) / 2
            is_date_computed = True

        address = record[f'{label}previous_domicile_location']
        add_origin(person, address, locations_df, 'domicile', date=pdd,
                   is_date_computed=is_date_computed, order=3)
    except KeyError:
        pass


def add_origin(person, address, locations_df, origin_type, date=None,
               is_date_computed=False, order=0):
    if pd.notna(address):
        place = get_place(locations_df, address.strip())

        if place:
            origin_type = OriginType.objects.get(title=origin_type)
            Origin.objects.get_or_create(
                person=person, place=place, origin_type=origin_type,
                date=date, is_date_computed=is_date_computed, order=order
            )


def add_party(deed, person, role, label, record):
    profession = None

    title = record[f'{label}profession']
    if pd.notna(title):
        profession, _ = Profession.objects.get_or_create(title=title.strip())

    Party.objects.get_or_create(
        deed=deed, person=person, role=role, profession=profession)


def import_marriages(data, marriages_df, locations_df):
    deed_type = DeedType.objects.get(title='marriage')

    for index, row in marriages_df.iterrows():
        try:
            deed_date = get_deed_date(row)
            place = get_place(locations_df, row['deed_location'].strip())
            source = import_source(data, row)
            import_marriage_record(
                deed_type, deed_date, place, source, row, locations_df)
        except Exception as e:  # noqa
            print('marriage', index, e)
            # skips the row
            continue


def import_marriage_record(
        deed_type, deed_date, place, source, record, locations_df):
    deed = import_deed(deed_type, deed_date, place, source, record)

    gender, _ = Gender.objects.get_or_create(title='m')
    groom = import_person('groom_', gender, deed_date, record, locations_df)
    role = Role.objects.get(title='groom')
    add_party(deed, groom, role, 'groom_', record)

    gender, _ = Gender.objects.get_or_create(title='f')
    bride = import_person('bride_', gender, deed_date, record, locations_df)
    role = Role.objects.get(title='bride')
    add_party(deed, bride, role, 'bride_', record)


def import_deaths(data, deaths_df, locations_df):
    deed_type = DeedType.objects.get(title='death')

    for index, row in deaths_df.iterrows():
        try:
            deed_date = get_deed_date(row)
            place = get_place(locations_df, row['deed_location'].strip())
            source = import_source(data, row)
            import_death_record(
                deed_type, deed_date, place, source, row, locations_df)
        except Exception as e:  # noqa
            print('death', index, e)
            continue


def import_death_record(
        deed_type, deed_date, place, source, record, locations_df):
    deed = import_deed(deed_type, deed_date, place, source, record)

    deceased = import_person('', None, deed_date, record, locations_df)
    role = Role.objects.get(title='deceased')
    add_party(deed, deceased, role, '', record)
