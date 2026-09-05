from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0100_patient_discussioncallnotes'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientdiscussion',
            name='eyeSelection',
            field=models.CharField(
                blank=True,
                choices=[('OS', 'OS'), ('OD', 'OD'), ('OU', 'OU')],
                max_length=2,
                null=True,
                verbose_name='تحديد العين',
            ),
        ),
    ]
