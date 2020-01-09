from django.http import JsonResponse
from django.views import View
from etat_civil.deeds.models import Person


class GeoJSONView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        return JsonResponse(Person.persons_to_geojson())


geojson_view = GeoJSONView.as_view()
