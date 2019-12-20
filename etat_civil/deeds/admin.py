from deeds.jobs import import_data_async
from deeds.models import (
    Data, Deed, DeedType, Gender, Origin, OriginType, Party, Person, Profession,
    Role, Source
)
from django.contrib import admin


class BaseALAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


@admin.register(Data)
class DataAdmin(admin.ModelAdmin):
    list_display = ['title', 'data']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        import_data_async.delay(request.user, obj)


class PartyInline(admin.TabularInline):
    model = Party

    autocomplete_fields = ['deed', 'person', 'profession', 'role']
    extra = 1


@admin.register(Deed)
class DeedAdmin(admin.ModelAdmin):
    autocomplete_fields = ['deed_type', 'place', 'source']
    date_hierarchy = 'date'
    inlines = [PartyInline]
    list_display = ['n', 'date', 'deed_type', 'place', 'source']
    list_filter = ['deed_type', 'place']
    search_fields = ['n', 'date', 'deed_type', 'place', 'source']


@admin.register(DeedType)
class DeedTypeAdmin(BaseALAdmin):
    pass


@admin.register(Gender)
class GenderAdmin(BaseALAdmin):
    pass


@admin.register(OriginType)
class OriginType(BaseALAdmin):
    pass


class OriginInline(admin.TabularInline):
    model = Origin

    autocomplete_fields = ['origin_type', 'place']
    extra = 1


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    inlines = [OriginInline, PartyInline]
    list_display = ['name', 'surname', 'gender',
                    'age', 'birth_year', 'get_origins']
    list_display_links = list_display
    list_filter = ['gender', 'age', 'surname']
    search_fields = ['name', 'surname']


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person', 'place', 'origin_type']
    date_hierarchy = 'date'
    list_display = ['person', 'place', 'origin_type', 'date']
    list_filter = ['origin_type', 'place']


@admin.register(Profession)
class ProfessionAdmin(BaseALAdmin):
    pass


@admin.register(Role)
class RoleAdmin(BaseALAdmin):
    pass


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['classmark', 'microfilm']
    search_fields = ['classmark', 'microfilm']
