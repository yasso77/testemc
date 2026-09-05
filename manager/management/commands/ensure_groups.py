from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the Admin and Discussion Group auth groups if they are missing.'

    def handle(self, *args, **options):
        for name in ('Admin', 'Discussion Group'):
            group, created = Group.objects.get_or_create(name=name)
            status = 'created' if created else 'already exists'
            self.stdout.write(f'{name}: {status} (id={group.id})')
