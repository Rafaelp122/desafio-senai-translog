from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    admin_group, _ = Group.objects.get_or_create(name='Admin')
    viewer_group, _ = Group.objects.get_or_create(name='Viewer')

    perms = Permission.objects.filter(codename__in=[
        'view_vehicle', 'add_vehicle', 'change_vehicle', 'delete_vehicle'
    ])
    admin_group.permissions.set(perms)

    viewer_group.permissions.set(Permission.objects.filter(codename='view_vehicle'))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
