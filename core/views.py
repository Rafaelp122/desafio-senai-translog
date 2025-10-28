from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Vehicle, MaintenanceRecord


class HomePageView(TemplateView):
    """
    Renderiza a página inicial (pública) do sistema.

    Esta view é o destino para onde os usuários são
    redirecionados após o logout (LOGOUT_REDIRECT_URL).
    """
    template_name = "core/home.html"


class DashboardPageView(LoginRequiredMixin, TemplateView):
    """
    Renderiza o painel principal (Dashboard) para usuários autenticados.

    Esta é a Interface Principal (Item 5 do desafio).

    Atributos:
    - LoginRequiredMixin: Garante que apenas usuários logados acessem esta página.
      Usuários não logados são redirecionados para a tela de login.

    Responsabilidades:
    - (RF005) Servir como tela principal após o login.
    - (RF006) Calcular e exibir a lista de alertas de manutenção.
    - (RF002) Preparar o contexto para os menus dinâmicos (baseados em permissões).
    """
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        """
        Sobrescreve o método padrão para injetar dados personalizados
        no contexto que será enviado ao template HTML.

        Principalmente, calcula a lista de 'alert_list' (RF006).
        """

        # Inicia o contexto chamando o método da classe pai
        context = super().get_context_data(**kwargs)

        # --- LÓGICA DE ALERTA (RF006) ---

        # Define o limite em KM para um alerta "próximo"
        LIMITE_ALERTA_KM = 1000

        # Busca todos os veículos. Em um sistema real,
        # poderíamos filtrar por 'veiculos_ativos=True'
        all_vehicles = Vehicle.objects.all()
        vehicles_in_alert = []  # A lista final de alertas

        for vehicle in all_vehicles:
            # 1. Busca a última manutenção PREVENTIVA do veículo
            last_preventive = MaintenanceRecord.objects.filter(
                vehicle=vehicle,
                maintenance_type='PRE'  # Filtra apenas por Preventiva
            ).order_by('-date').first()  # '-date' = mais recente

            km_proxima_revisao = 0

            if last_preventive:
                # 2a. Se já teve revisão, a próxima é baseada na última
                km_proxima_revisao = last_preventive.mileage_at_maintenance + vehicle.maintenance_interval_km
            else:
                # 2b. Se NUNCA teve, a primeira revisão é o próprio intervalo
                km_proxima_revisao = vehicle.maintenance_interval_km

            # 3. Compara a KM atual com a KM da próxima revisão
            km_atual = vehicle.current_mileage
            km_faltando = km_proxima_revisao - km_atual

            # 4. A Lógica de Alerta:
            # Se (km_faltando <= 0) -> A revisão está ATRA
            # Se (km_faltando <= LIMITE_ALERTA_KM) -> A revisão está PRÓXIMA
            if km_atual >= (km_proxima_revisao - LIMITE_ALERTA_KM):
                vehicles_in_alert.append({
                    'vehicle': vehicle,
                    'km_faltando': km_faltando,  # Será negativo se estiver atrasado
                    'proxima_revisao_km': km_proxima_revisao
                })

        # 5. Envia a lista de alertas para o template
        context['alert_list'] = vehicles_in_alert

        # # 6. Adiciona as permissões do usuário ao contexto (RF002).
        # # É crucial adicionar 'perms' explicitamente usando
        # # 'get_all_permissions()' para que o template possa
        # # verificar as permissões vindas dos Grupos (ex: {% if perms.core.add_vehicle %}).
        # context['perms'] = self.request.user.get_all_permissions()

        return context
