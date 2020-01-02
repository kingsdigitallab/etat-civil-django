from pathlib import Path

from etat_civil.deeds.models import Data
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Imports data from a data collection spreadsheet"

    def add_arguments(self, parser):
        parser.add_argument("title", nargs=1, type=str, help="The title of the data")
        parser.add_argument(
            "data_file", nargs=1, type=Path, help="The data file to import"
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete existing data before importing",
        )

    def handle(self, *args, **options):
        title = options["title"][0]
        data_file = options["data_file"][0]

        data, _ = Data.objects.get_or_create(title=title)
        data.data.save(data_file.name, File(open(data_file, "rb")))
        data.save()

        self.stdout.write("Importing data...")
        data.load_data(delete=options["delete"])
