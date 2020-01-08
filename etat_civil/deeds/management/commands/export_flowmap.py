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
        Place.to_csv(os.path.join(output_dir, "locations.tsv"), delimiter="\t")

    def handle_flows(self, output_dir):
        with open(os.path.join(output_dir, "flows.tsv"), "w") as f:
            tsv_writer = csv.writer(f, delimiter="\t")
            tsv_writer.writerow(["origin", "dest", "count"])

            for person in Person.objects.all():
                person_origins = person.get_origins()

                if person_origins.count() > 1:
                    origin_place = None

                    for idx, person_origin in enumerate(person_origins):
                        dest_place = person_origin.place

                        if idx > 0 and origin_place:
                            tsv_writer.writerow(
                                [origin_place.geonames_id, dest_place.geonames_id, 1]
                            )

                        origin_place = person_origin.place

            f.close()
