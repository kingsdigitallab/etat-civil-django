import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from etat_civil.deeds.models import Person


class Command(BaseCommand):
    help = """Exports all the person\'s origins into a GeoJSON
    FeatureCollection. The exported file can be used with a viewer like
    kepler.gl."""

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            help="Specifies file to which the GeoJSON output is written.",
        )

    def handle(self, *args, **options):
        output = options["output"]
        stream = open(output, "w") if output else self.stdout

        geo = defaultdict()
        geo["type"] = "FeatureCollection"
        geo["features"] = []

        for person in Person.objects.all():
            feature = person.to_geojson()
            if feature:
                geo["features"].append(feature)

        json.dump(geo, stream, indent=2, sort_keys=True)
