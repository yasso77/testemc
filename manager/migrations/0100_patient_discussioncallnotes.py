from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0099_patientdiscussion_receiptno'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='discussionCallNotes',
            field=models.TextField(blank=True, null=True, verbose_name='Call Notes for Discussion'),
        ),
    ]
