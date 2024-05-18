import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load a list of ingredients from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file_path', type=str,
            help='The path to the JSON file with ingredients')

    def handle(self, *args, **options):
        json_file_path = options['json_file_path']

        with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for entry in data:
                Ingredient.objects.create(
                    name=entry['name'],
                    measurement_unit=entry['measurement_unit']
                )
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded ingredients from JSON'))
