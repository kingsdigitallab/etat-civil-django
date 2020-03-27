import csv
from django.http import HttpResponse, JsonResponse
from django.views import View
from etat_civil.deeds.models import Person
from etat_civil.geonames_place.models import Place


class GeoJSONView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        response = JsonResponse(Person.persons_to_geojson())
        response["Content-Disposition"] = 'attachment; filename="geojson.json"'

        return response


geojson_view = GeoJSONView.as_view()


class FlowmapLocationsView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/tsv")
        response["Content-Disposition"] = 'attachment; filename="locations.tsv"'

        csv_writer = csv.writer(response, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
        csv_writer.writerow(["id", "name", "lat", "lon"])
        csv_writer.writerows(Place.places_to_list())

        return response


flowmap_locations_view = FlowmapLocationsView.as_view()


class FlowmapFlowsView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/tsv")
        response["Content-Disposition"] = 'attachment; filename="flows.tsv"'

        csv_writer = csv.writer(response, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
        csv_writer.writerow(["origin", "dest", "count"])
        csv_writer.writerows(Person.persons_to_flows())

        return response


flowmap_flows_view = FlowmapFlowsView.as_view()
