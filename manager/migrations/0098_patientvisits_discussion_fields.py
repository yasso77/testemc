# Safe for MySQL shared hosting: add columns without enforced FK constraint.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0097_userextra_must_change_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientvisits',
            name='discussionNotes',
            field=models.TextField(blank=True, null=True, verbose_name='ملاحظات للديسكشن'),
        ),
        migrations.AddField(
            model_name='patientvisits',
            name='operationType',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='patient_visits',
                to='manager.operationtype',
                verbose_name='نوع العملية',
            ),
        ),
    ]
