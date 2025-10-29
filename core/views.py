import logging
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Vehicle, MaintenanceRecord

# Obtém o logger para este módulo ('core.views')
logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    """
    Renderiza a página inicial pública do sistema.

    É o destino padrão após o logout do utilizador.
    """
    template_name = "core/home.html"


class DashboardPageView(LoginRequiredMixin, TemplateView):
    """
    Renderiza o painel principal (Dashboard) para utilizadores autenticados.

    Esta view implementa a Interface Principal (Item 5) do desafio,
    incluindo o cálculo de alertas de manutenção (RF006) e
    o fornecimento de contexto para menus baseados em permissões (RF002).
    """
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        """
        Calcula e adiciona dados dinâmicos ao contexto do template.

        Principalmente, determina quais veículos necessitam de alerta
        de manutenção preventiva com base na quilometragem.
        """
        context = super().get_context_data(**kwargs)

        # Log de entrada na função, útil para rastrear o fluxo da requisição
        logger.debug(f"A calcular alertas de manutenção para: {self.request.user}")

        # Define o limiar (em KM) para considerar uma revisão como "próxima"
        LIMITE_ALERTA_KM = 1000

        # TODO: Filtrar apenas por veículos ativos num cenário real
        all_vehicles = Vehicle.objects.all()
        vehicles_in_alert = []

        for vehicle in all_vehicles:
            # Encontra a última manutenção *preventiva* registada
            last_preventive = MaintenanceRecord.objects.filter(
                vehicle=vehicle, maintenance_type='PRE'
            ).order_by('-date').first()

            km_proxima_revisao = 0
            if last_preventive:
                # Calcula a KM da próxima revisão baseada na última
                km_proxima_revisao = last_preventive.mileage_at_maintenance + vehicle.maintenance_interval_km
            else:
                # Se nunca houve preventiva, a primeira é o intervalo padrão
                km_proxima_revisao = vehicle.maintenance_interval_km

            km_atual = vehicle.current_mileage
            km_faltando = km_proxima_revisao - km_atual

            # Log de depuração detalhado para cada veículo
            logger.debug(
                f"[Verificação Alerta] Veículo {vehicle.plate}: "
                f"KM Atual={km_atual}, Próxima KM={km_proxima_revisao}, "
                f"KM Faltando={km_faltando}, Limite={LIMITE_ALERTA_KM}"
            )

            # Regra de Negócio RF006: Inclui no alerta se a revisão está atrasada
            # (km_atual >= km_proxima_revisao) ou próxima (dentro do limite).
            if km_atual >= (km_proxima_revisao - LIMITE_ALERTA_KM):
                logger.debug(f"[Alerta Ativado] Veículo {vehicle.plate} adicionado à lista.")
                vehicles_in_alert.append({
                    'vehicle': vehicle,
                    'km_faltando': km_faltando,
                    'proxima_revisao_km': km_proxima_revisao
                })

        context['alert_list'] = vehicles_in_alert

        # Log informativo de conclusão, registando o resultado principal
        logger.info(
            f"Dashboard processado para {self.request.user}. "
            f"Alertas encontrados: {len(vehicles_in_alert)}."
        )

        return context
