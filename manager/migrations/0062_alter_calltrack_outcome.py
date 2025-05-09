# Generated by Django 5.0.7 on 2025-02-15 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0061_alter_calltrack_outcome_alter_calltrack_tracktype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calltrack',
            name='outcome',
            field=models.CharField(blank=True, choices=[('Canceled', 'Canceled'), ('Rescheduled', 'Rescheduled'), ('Confirmed', 'Confirmed'), ('Re-examination', 'Re-examination'), ('Eye surgery', 'Eye surgery'), ('After surgery', 'After surgery')], max_length=100, null=True, verbose_name='Outcome of Follow-Up'),
        ),
    ]
