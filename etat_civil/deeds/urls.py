from django.urls import path

from etat_civil.deeds.views import (
    geojson_view,
    flowmap_flows_view,
    flowmap_locations_view,
)

app_name = "deeds"

urlpatterns = [
    path("flowmap/flows/", view=flowmap_flows_view, name="flowmap_flows"),
    path("flowmap/locations/", view=flowmap_locations_view, name="flowmap_locations"),
    path("geojson/", view=geojson_view, name="geojson"),
]
