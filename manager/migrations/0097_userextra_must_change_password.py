from django.db import migrations, models


def flag_all_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserExtra = apps.get_model('manager', 'UserExtra')
    for user in User.objects.all().iterator():
        extra, created = UserExtra.objects.get_or_create(
            user_id=user.id,
            defaults={'must_change_password': True},
        )
        if not created and not extra.must_change_password:
            extra.must_change_password = True
            extra.save(update_fields=['must_change_password'])


def unflag_all_users(apps, schema_editor):
    UserExtra = apps.get_model('manager', 'UserExtra')
    UserExtra.objects.update(must_change_password=False)


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0096_discussion_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='userextra',
            name='must_change_password',
            field=models.BooleanField(default=True, verbose_name='Must change password'),
        ),
        migrations.RunPython(flag_all_users, unflag_all_users),
    ]
