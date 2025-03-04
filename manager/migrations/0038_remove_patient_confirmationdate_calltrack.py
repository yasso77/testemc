# Generated by Django 5.0.4 on 2025-01-26 13:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0037_alter_patient_sufferedcase'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='confirmationDate',
        ),
        migrations.CreateModel(
            name='CallTrack',
            fields=[
                ('callTrackID', models.AutoField(primary_key=True, serialize=False)),
                ('remarks', models.CharField(blank=True, max_length=500, null=True, verbose_name='Call Remarks')),
                ('confirmationDate', models.DateField(blank=True, null=True, verbose_name='Confirmation Date')),
                ('createdDate', models.DateField(auto_now_add=True, verbose_name='Created date')),
                ('createdBy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='call_agent', to=settings.AUTH_USER_MODEL)),
                ('patientID', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='call_patients', to='manager.patient')),
            ],
            options={
                'verbose_name': 'Call Track',
                'verbose_name_plural': 'Call Tracks',
            },
        ),
    ]
