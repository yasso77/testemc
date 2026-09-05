from django.db import migrations, models


def backfill_doctor_name(apps, schema_editor):
    PatientDiscussion = apps.get_model('manager', 'PatientDiscussion')
    User = apps.get_model('auth', 'User')
    for discussion in PatientDiscussion.objects.filter(doctorName__isnull=True).exclude(doctor_id__isnull=True):
        try:
            user = User.objects.get(pk=discussion.doctor_id)
        except User.DoesNotExist:
            continue
        full_name = f'{user.first_name or ""} {user.last_name or ""}'.strip()
        discussion.doctorName = full_name or user.username
        discussion.save(update_fields=['doctorName'])


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0102_patientdiscussion_discussionserial_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientdiscussion',
            name='doctorName',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='اسم الطبيب'),
        ),
        migrations.RunPython(backfill_doctor_name, migrations.RunPython.noop),
    ]
