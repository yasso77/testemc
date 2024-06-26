# Generated by Django 5.0.4 on 2024-05-18 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0004_alter_patient_age_alter_patient_mobile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='image',
            field=models.ImageField(default='photos/patient.png', null=True, upload_to='patients/photos/%y/%m/%d'),
        ),
    ]
