from django.db import migrations


def create_groups_and_permissions(apps, schema_editor):
    """
    Cria os grupos de usuários (Administrador, Mecanico, Motorista)
    e atribui as permissões corretas a eles.
    """

    # --- Modelos Relevantes ---
    # Carregamos as versões históricas dos modelos
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # --- Permissões do Motorista ---
    motorista_perms_codenames = [
        'add_mileagerecord',
        'view_mileagerecord',
        'view_vehicle',
    ]
    motorista_permissions = Permission.objects.filter(
        codename__in=motorista_perms_codenames
    )

    motorista_group, created = Group.objects.get_or_create(name='Motorista')
    if created:
        motorista_group.permissions.set(motorista_permissions)

    # --- Permissões do Mecânico ---
    mecanico_perms_codenames = [
        'add_maintenancerecord',
        'change_maintenancerecord',
        'view_maintenancerecord',
        'view_vehicle',
    ]
    mecanico_permissions = Permission.objects.filter(
        codename__in=mecanico_perms_codenames
    )

    mecanico_group, created = Group.objects.get_or_create(name='Mecanico')
    if created:
        mecanico_group.permissions.set(mecanico_permissions)

    # --- Permissões do Administrador ---
    core_models = ['vehicle', 'maintenancerecord', 'mileagerecord']

    core_content_types = ContentType.objects.filter(
        app_label='core', 
        model__in=core_models
    )

    admin_permissions = Permission.objects.filter(
        content_type__in=core_content_types
    )

    admin_group, created = Group.objects.get_or_create(name='Administrador')
    if created:
        admin_group.permissions.set(admin_permissions)


def remove_groups_and_permissions(apps, schema_editor):
    """
    Reverte a migração, apagando os grupos criados.
    """
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(
        name__in=['Administrador', 'Mecanico', 'Motorista']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_maintenancerecord_labor_cost_and_more'),
        # Definimos dependências explícitas para garantir
        # que as permissões de auth já existam.
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_groups_and_permissions,
            remove_groups_and_permissions
        ),
    ]
