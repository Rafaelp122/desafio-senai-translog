import logging
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_groups_on_migrate(sender, **kwargs):
    """
    Cria os perfis de utilizador (Grupos) após a execução das migrações.

    Este sinal (signal) é disparado pelo Django após o comando 'migrate'
    ser concluído. Ele garante que as Permissões (ex: 'add_vehicle')
    já existam no banco de dados antes de tentarmos atribuí-las aos Grupos,
    resolvendo assim o problema de "timing" (race condition) que
    ocorre ao usar migrações de dados ('RunPython') para este fim.

    Argumentos:
        sender: A configuração da app que acabou de ser migrada (ex: 'core.apps.CoreConfig').
        **kwargs: Argumentos adicionais enviados pelo sinal.
    """

    # (1) Verificamos se é o nosso app 'core' que enviou o sinal.
    # Isto impede que este código seja executado múltiplas vezes,
    # uma para cada app instalada (como 'admin', 'auth', etc.).
    if sender.name == 'core':

        # --- Grupo Motorista ---
        # Define as permissões que um Motorista deve ter.
        motorista_group, _ = Group.objects.get_or_create(name='Motorista')

        motorista_perms_codenames = [
            'add_mileagerecord',   # Pode adicionar registo de KM
            'view_mileagerecord',  # Pode ver seus registos de KM
            # Nota: 'view_vehicle' foi removido intencionalmente.
            # A lógica de negócio (RF005) será que o motorista
            # só pode registar KM para os veículos a ele atribuídos
            # (via 'Vehicle.assigned_drivers'), e não para a frota toda.
        ]
        motorista_permissions = Permission.objects.filter(
            codename__in=motorista_perms_codenames
        )
        motorista_group.permissions.set(motorista_permissions)

        # --- Grupo Mecânico ---
        mecanico_group, _ = Group.objects.get_or_create(name='Mecanico')

        mecanico_perms_codenames = [
            'add_maintenancerecord',     # Pode adicionar manutenção
            'change_maintenancerecord',  # Pode editar manutenção
            'view_maintenancerecord',    # Pode ver histórico de manutenções
            'view_vehicle',              # Pode ver a frota completa
        ]
        mecanico_permissions = Permission.objects.filter(
            codename__in=mecanico_perms_codenames
        )
        mecanico_group.permissions.set(mecanico_permissions)

        # --- Grupo Administrador ---
        # O Administrador tem todas as permissões sobre os modelos do 'core'.
        admin_group, _ = Group.objects.get_or_create(name='Administrador')

        # Busca todos os modelos do app 'core'
        core_models = ['vehicle', 'maintenancerecord', 'mileagerecord']
        core_content_types = ContentType.objects.filter(
            app_label='core',
            model__in=core_models
        )

        # Busca todas as permissões associadas a esses modelos
        admin_permissions = Permission.objects.filter(
            content_type__in=core_content_types
        )
        admin_group.permissions.set(admin_permissions)

        logger.info(
            "Sinal 'post_migrate' executado: Grupos 'Administrador', 'Mecanico' "
            "e 'Motorista' verificados/criados."
        )
