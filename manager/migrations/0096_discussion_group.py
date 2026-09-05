from django.db import migrations


def create_discussion_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Discussion Group')


def remove_discussion_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Discussion Group').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0095_discussion_models'),
    ]

    operations = [
        migrations.RunPython(create_discussion_group, remove_discussion_group),
    ]
