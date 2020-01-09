import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from etat_civil.deeds.models import Person
from etat_civil.geonames_place.models import Place


class Command(BaseCommand):
    help = """Exports all the person\'s origins into the flowmap.blue data
    format, a tsv file with locations and a tsv file with flows."""

    def add_arguments(self, parser):
        parser.add_argument(
            "output_dir",
            nargs=1,
            type=Path,
            help="The directory where to write the output file.",
        )

    def handle(self, *args, **options):
        output_dir = options["output_dir"][0]

        self.handle_locations(output_dir)
        self.handle_flows(output_dir)

    def handle_locations(self, output_dir):
        with open(os.path.join(output_dir, "locations.tsv"), "w") as f:
            csv_writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow(["id", "name", "lat", "lon"])
            csv_writer.writerows(Place.places_to_list())

            f.close()

    def handle_flows(self, output_dir):
        with open(os.path.join(output_dir, "flows.tsv"), "w") as f:
            csv_writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow(["origin", "dest", "count"])
            csv_writer.writerows(Person.persons_to_flows())

            f.close()
