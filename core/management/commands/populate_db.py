from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User, Group
from core.models import Vehicle, MaintenanceRecord, MileageRecord

# A senha de teste
TEST_PASSWORD = 'TransLog@2025'


class Command(BaseCommand):
    """
    Comando de gerenciamento para popular o banco de dados com dados de teste.

    Limpa e recria dados para Veículos, Usuários de Teste,
    Manutenções e Registros de KM.

    Como usar: python manage.py populate_db
    """
    help = 'Popula o banco de dados com dados de teste (Veículos, Usuários, Manutenções).'

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(self.style.NOTICE('Iniciando a população do banco de dados...'))

        # --- 1. LIMPA DADOS ANTIGOS ---
        # Isso garante que podemos rodar o comando várias vezes sem duplicar dados
        self.stdout.write("Limpando dados de teste antigos...")
        Vehicle.objects.all().delete()
        MaintenanceRecord.objects.all().delete()
        MileageRecord.objects.all().delete()
        User.objects.filter(username__in=['mecanico_chefe', 'motorista_jose', 'admin_frota']).delete()

        # --- 2. BUSCA OS GRUPOS ---
        # (Assume que a migração 0003_... já rodou)
        try:
            motorista_group = Group.objects.get(name='Motorista')
            mecanico_group = Group.objects.get(name='Mecanico')
            admin_group = Group.objects.get(name='Administrador')
        except Group.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Grupos não encontrados. Rode a migração 0003_create_groups primeiro.'
            ))
            return

        # --- 3. CRIA OS USUÁRIOS DE TESTE ---
        self.stdout.write("Criando usuários de teste...")
        mecanico_user = User.objects.create_user(
            username='mecanico_chefe', password=TEST_PASSWORD
        )
        mecanico_user.groups.add(mecanico_group)

        motorista_user = User.objects.create_user(
            username='motorista_jose', password=TEST_PASSWORD
        )
        motorista_user.groups.add(motorista_group)

        admin_user = User.objects.create_user(
            username='admin_frota', password=TEST_PASSWORD
        )
        admin_user.groups.add(admin_group)

        # --- 4. CRIA OS VEÍCULOS (Vehicles) ---
        self.stdout.write("Criando veículos...")
        v1 = Vehicle.objects.create(
            plate='VOL1234', make='Volvo', model='FH 540',
            year=2021, current_mileage=0, maintenance_interval_km=10000
        )
        v2 = Vehicle.objects.create(
            plate='SCA5678', make='Scania', model='R450',
            year=2020, current_mileage=0, maintenance_interval_km=10000
        )
        v3 = Vehicle.objects.create(
            plate='MER9012', make='Mercedes-Benz', model='Actros 2651',
            year=2022, current_mileage=0, maintenance_interval_km=15000
        )

        # --- 5. CRIA AS MANUTENÇÕES (MaintenanceRecords) ---
        self.stdout.write("Criando registros de manutenção...")
        MaintenanceRecord.objects.create(
            vehicle=v1, maintenance_type='PRE', date='2025-08-01',
            description='Revisão dos 50.000 km. Troca de óleo e filtros.',
            mileage_at_maintenance=50000,
            parts_cost=1800.00, labor_cost=500.00,
            responsible_mechanic=mecanico_user
        )
        MaintenanceRecord.objects.create(
            vehicle=v2, maintenance_type='COR', date='2025-06-10',
            description='Conserto do sistema de injeção eletrônica.',
            mileage_at_maintenance=42000,
            parts_cost=3500.00, labor_cost=1200.00,
            responsible_mechanic=mecanico_user
        )
        MaintenanceRecord.objects.create(
            vehicle=v3, maintenance_type='PRE', date='2025-09-15',
            description='Revisão dos 15.000 km. Alinhamento e balanceamento.',
            mileage_at_maintenance=15000,
            parts_cost=600.00, labor_cost=300.00,
            responsible_mechanic=admin_user
        )

        # --- 6. CRIA OS REGISTROS DE KM (MileageRecords) ---
        # (Isso também vai atualizar a 'current_mileage' dos veículos)
        self.stdout.write("Criando registros de KM e atualizando veículos...")
        MileageRecord.objects.create(
            vehicle=v1, driver=motorista_user, mileage=59500
        )  # Lógica: Próximo de 60k

        MileageRecord.objects.create(
            vehicle=v2, driver=motorista_user, mileage=68000
        )  # Lógica: Atrasado (primeira era aos 10k)

        MileageRecord.objects.create(
            vehicle=v3, driver=motorista_user, mileage=23000
        )  # Lógica: OK (próxima aos 30k)

        self.stdout.write(self.style.SUCCESS(
            'Banco de dados populado com dados de teste com sucesso!'
        ))
