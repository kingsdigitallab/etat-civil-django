from django.http import JsonResponse
from django.views import View
from etat_civil.deeds.models import Person


class GeoJSONView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        geo = {}
        geo["type"] = "FeatureCollection"
        geo["features"] = []

        for person in Person.objects.all():
            feature = person.to_geojson()
            if feature:
                geo["features"].append(feature)

        return JsonResponse(geo)


geojson_view = GeoJSONView.as_view()
