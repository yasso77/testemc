from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0098_patientvisits_discussion_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientdiscussion',
            name='receiptNo',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name='Receipt No'),
        ),
    ]
