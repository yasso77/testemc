# Generated by Django 5.0.7 on 2025-02-11 16:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0055_patient_mybirthdate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='mybirthdate',
        ),
    ]
