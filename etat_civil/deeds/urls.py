from django.urls import path

from etat_civil.deeds.views import geojson_view

app_name = "deeds"

urlpatterns = [path("geojson/", view=geojson_view, name="geojson")]
