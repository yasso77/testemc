from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0101_patientdiscussion_eyeselection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientdiscussion',
            name='discussionSerial',
            field=models.CharField(max_length=150, unique=True, verbose_name='Discussion Serial'),
        ),
    ]
