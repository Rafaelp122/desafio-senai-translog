from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group

from .models import Vehicle, MaintenanceRecord

# Define uma senha padrão para todos os usuários de teste
TEST_PASSWORD = 'TestPassword123@'


class CoreViewsTestCase(TestCase):
    """
    Conjunto de testes para as views principais da aplicação 'core'.

    Estes testes validam o controle de acesso (login), o fluxo de
    autenticação (login/logout) e a lógica de negócio do dashboard (Alerta RF006),
    cumprindo o Item 8 do desafio.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Configura os dados iniciais para todos os testes da classe.

        Este método roda apenas uma vez, criando os usuários de teste
        e os veículos necessários para simular o cenário de alerta.
        Assume que a migração 0003_create_groups já foi executada.
        """

        # --- 1. Busca os Grupos criados pela migração ---
        try:
            cls.motorista_group = Group.objects.get(name='Motorista')
            cls.mecanico_group = Group.objects.get(name='Mecanico')
            cls.admin_group = Group.objects.get(name='Administrador')
        except Group.DoesNotExist:
            # Falha crítica se a migração de dados não rodou
            raise Exception("ERRO: Grupos não encontrados. Execute a migração 0003_create_groups.")

        # --- 2. Cria usuários de teste para cada perfil ---
        cls.motorista_user = User.objects.create_user(
            username='test_motorista', password=TEST_PASSWORD
        )
        cls.motorista_user.groups.add(cls.motorista_group)

        cls.mecanico_user = User.objects.create_user(
            username='test_mecanico', password=TEST_PASSWORD
        )
        cls.mecanico_user.groups.add(cls.mecanico_group)

        cls.admin_user = User.objects.create_user(
            username='test_admin', password=TEST_PASSWORD
        )
        cls.admin_user.groups.add(cls.admin_group)

        # --- 3. Cria dados para o Teste de Alerta (RF006) ---

        # Veículo 1: (ALERTA) Próximo da revisão
        cls.vehicle_alert = Vehicle.objects.create(
            plate='ALERT01', make='TestMake', model='TestModel',
            year=2020, maintenance_interval_km=10000
        )
        MaintenanceRecord.objects.create(
            vehicle=cls.vehicle_alert,
            maintenance_type='PRE',  # Preventiva
            date='2024-01-01',
            mileage_at_maintenance=50000,  # Última revisão aos 50k
        )
        cls.vehicle_alert.current_mileage = 59500  # Próxima é aos 60k
        cls.vehicle_alert.save()

        # Veículo 2: (OK) Longe da revisão
        cls.vehicle_safe = Vehicle.objects.create(
            plate='SAFE001', make='TestMake', model='TestModel',
            year=2022, maintenance_interval_km=10000
        )
        MaintenanceRecord.objects.create(
            vehicle=cls.vehicle_safe,
            maintenance_type='PRE',
            date='2024-05-01',
            mileage_at_maintenance=20000,  # Última revisão aos 20k
        )
        cls.vehicle_safe.current_mileage = 22000  # Próxima é aos 30k
        cls.vehicle_safe.save()

    # --- Testes de Visão Geral e Acesso ---

    def test_home_page_view(self):
        """
        CT001 (Sucesso): Testa se a HomePage (/) carrega (status 200)
        e usa o template correto.
        """
        # self.client simula um navegador web
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_dashboard_page_requires_login(self):
        """
        CT002 (Falha - Acesso): Testa se o Dashboard (/) está protegido.
        Um usuário não logado deve ser redirecionado (status 302).
        """
        response = self.client.get(reverse('dashboard'))

        # 302 é o código para "Redirecionamento"
        self.assertEqual(response.status_code, 302)

        # Verifica se o redirecionamento foi para a página de login
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

    def test_dashboard_page_loads_for_logged_in_user(self):
        """
        CT003 (Sucesso - Acesso): Testa se o Dashboard carrega (status 200)
        para um usuário autenticado.
        """
        # Faz o login do usuário de teste
        self.client.login(username='test_motorista', password=TEST_PASSWORD)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

        # Verifica se o conteúdo da página contém a saudação
        self.assertContains(response, 'Olá, <strong>test_motorista</strong>!')

    # --- Testes do Fluxo de Autenticação (Login/Logout) ---

    def test_login_success_redirects_to_dashboard(self):
        """
        CT004 (Sucesso - Login): Testa um login válido (RF001).
        Deve redirecionar (302) para o dashboard.
        """
        response = self.client.post(
            reverse('login'), 
            {'username': 'test_mecanico', 'password': TEST_PASSWORD}
        )

        self.assertEqual(response.status_code, 302)
        # Verifica se o redirecionamento foi para o 'dashboard' (LOGIN_REDIRECT_URL)
        self.assertRedirects(response, reverse('dashboard'))

        # Garante que o usuário está de fato logado na sessão
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_failure_wrong_password(self):
        """
        CT005 (Falha - Login): Testa um login com senha errada (RF001).
        Deve recarregar a página (200) e exibir uma mensagem de erro.
        """
        response = self.client.post(
            reverse('login'), 
            {'username': 'test_mecanico', 'password': 'WrongPassword123'}
        )

        # Uma falha de login POST recarrega a página e mostra o formulário
        self.assertEqual(response.status_code, 200)

        # Garante que o usuário NÃO foi logado
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        # Verifica se a mensagem de erro está no HTML
        self.assertContains(response, 'Seu nome de usuário ou senha estão incorretos.')

    def test_logout_view_redirects_to_home(self):
        """
        CT006 (Sucesso - Logout): Testa se o logout (via POST) funciona
        e redireciona para a 'home' (LOGOUT_REDIRECT_URL).
        """
        # O usuário precisa estar logado para testar o logout
        self.client.login(username='test_admin', password=TEST_PASSWORD)

        # O logout do Django moderno exige um POST
        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

        # Garante que o usuário foi desconectado da sessão
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # --- Teste da Lógica de Negócio (O Mais Importante) ---

    def test_dashboard_alert_logic_rf006(self):
        """
        CT007 (Sucesso - Alerta): Testa a lógica de alerta (RF006)
        enviada pela DashboardPageView.
        """
        self.client.login(username='test_admin', password=TEST_PASSWORD)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)

        # Verifica se a view enviou a lista 'alert_list' no contexto
        self.assertIn('alert_list', response.context)

        alert_list = response.context['alert_list']

        # Converte a lista de dicionários em uma lista simples de placas
        alert_plates = [item['vehicle'].plate for item in alert_list]

        # O veículo 'ALERT01' (próximo da revisão) DEVE estar na lista
        self.assertIn('ALERT01', alert_plates)

        # O veículo 'SAFE001' (longe da revisão) NÃO DEVE estar na lista
        self.assertNotIn('SAFE001', alert_plates)
