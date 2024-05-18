import csv
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Путь к CSV файлу с ингредиентами')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    Ingredient.objects.create(name=row[0], measurement_unit=row[1])
            self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены'))
        except Exception as e:
            raise CommandError(f'Ошибка при загрузке данных из {csv_file_path}: {str(e)}')
