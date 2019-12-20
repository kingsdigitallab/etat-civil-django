from pathlib import Path

from deeds.models import Data, import_data
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Imports data from a data collection spreadsheet'

    def add_arguments(self, parser):
        parser.add_argument('title', nargs=1, type=str,
                            help='The title of the data')
        parser.add_argument('data_file', nargs=1, type=Path,
                            help='The data file to import')
        parser.add_argument('--delete', action='store_true',
                            help='Delete existing data before importing')

    def handle(self, *args, **options):
        title = options['title'][0]
        data_file = options['data_file'][0]

        if options['delete']:
            try:
                self.stdout.write('Deleting existing data')

                data = Data.objects.get(title=title)
                data.delete()
            except Data.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'No existing data found for {title}'))

        data, _ = Data.objects.get_or_create(title=title)
        data.data.save(data_file.name, File(open(data_file, 'rb')))
        data.save()

        self.stdout.write('Importing data...')
        import_data(data)
