from django.core.management.base import BaseCommand

from course.models import Course


class Command(BaseCommand):
    help = 'Add a sourced example course without overwriting an existing course.'

    def handle(self, *args, **options):
        _, created = Course.objects.get_or_create(
            course_name='Sahm Park',
            city='Indianapolis',
            defaults={'holes': 18, 'tee_type': 'Concrete'},
        )
        self.stdout.write('Added Sahm Park.' if created else 'Sahm Park already exists.')
