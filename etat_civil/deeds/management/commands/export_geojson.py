import json
from collections import defaultdict
from datetime import datetime

from deeds.models import Person
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '''Exports all the person\'s origins into a GeoJSON
    FeatureCollection. The exported file can be used with a viewer like
    kepler.gl.'''

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--output',
            help='Specifies file to which the GeoJSON output is written.')

    def handle(self, *args, **options):
        output = options['output']
        stream = open(output, 'w') if output else self.stdout

        geo = defaultdict()
        geo['type'] = 'FeatureCollection'
        geo['features'] = []

        for person in Person.objects.all():
            if person.origin_from.count() > 0:
                feature = defaultdict()
                feature['type'] = 'Feature'

                properties = defaultdict()
                properties['id'] = person.id
                properties['name'] = person.name
                properties['age'] = person.age

                if person.gender:
                    properties['gender'] = person.gender.title

                properties['origins'] = person.get_origins()
                # properties['professions'] = person.get_professions()

                geometry = defaultdict()
                geometry['type'] = 'LineString'

                coords = []

                prev_place = None
                origins = person.origin_from.order_by('date')
                for idx, origin in enumerate(origins):
                    if not origin.place.lat or not origin.place.lon:
                        continue

                    if idx == 0 or idx == origins.count() - 1:
                        pos = 'first' if idx == 0 else 'last'

                        properties['origin_{}'.format(
                            pos)] = origin.place.address
                        properties['origin_{}_type'.format(
                            pos)] = origin.origin_type.title
                        properties['origin_{}_lat'.format(pos)] = float(
                            origin.place.lat)
                        properties['origin_{}_lon'.format(pos)] = float(
                            origin.place.lon)
                        properties['origin_{}_date'.format(
                            pos)] = '{} 00:00'.format(origin.date)
                        properties['origin_{}_is_date_computed'.format(
                            pos)] = origin.is_date_computed

                    if origin.place != prev_place:
                        ts = datetime.fromordinal(
                            origin.date.toordinal()).timestamp()
                        coords.append([float(origin.place.lon),
                                       float(origin.place.lat),
                                       0, int(ts)])

                    prev_place = origin.place

                feature['properties'] = properties
                geometry['coordinates'] = coords
                feature['geometry'] = geometry
                geo['features'].append(feature)

        json.dump(geo, stream, indent=2, sort_keys=True)
