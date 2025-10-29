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

    Responsável por calcular e exibir alertas de manutenção (RF006)
    apenas para veículos relevantes ao perfil do utilizador, e
    fornecer contexto para menus baseados em permissões (RF002).
    """
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        """
        Calcula e adiciona dados dinâmicos ao contexto do template.

        Filtra a lista de veículos a serem verificados com base nas permissões
        do utilizador (`core.view_vehicle` para Mecânicos/Admins,
        `assigned_drivers` para Motoristas) antes de calcular os alertas.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        logger.debug(f"A iniciar cálculo de alertas para: {user}")

        LIMITE_ALERTA_KM = 1000
        vehicles_to_check = None  # QuerySet base para a verificação de alertas

        # Filtra o queryset de veículos com base no perfil do utilizador
        if user.has_perm('core.view_vehicle'):
            # Mecânicos e Administradores (que possuem a permissão geral)
            # devem ver os alertas de toda a frota.
            logger.debug(f"Utilizador {user} tem 'core.view_vehicle'. A verificar todos os veículos.")
            vehicles_to_check = Vehicle.objects.all()
        elif user.groups.filter(name='Motorista').exists():
            # Motoristas (sem a permissão geral) devem ver alertas
            # apenas dos veículos que lhes estão atribuídos.
            logger.debug(f"Utilizador {user} é Motorista. A verificar apenas veículos atribuídos.")
            vehicles_to_check = Vehicle.objects.filter(assigned_drivers=user)
        else:
            # Caso de segurança para utilizadores sem grupo/permissões relevantes
            logger.warning(f"Utilizador {user} sem perfil relevante. Nenhum veículo será verificado para alertas.")
            vehicles_to_check = Vehicle.objects.none()

        vehicles_in_alert = []

        # Itera sobre o queryset filtrado para calcular os alertas
        for vehicle in vehicles_to_check:
            # Encontra a última manutenção *preventiva* registada
            last_preventive = MaintenanceRecord.objects.filter(
                vehicle=vehicle, maintenance_type='PRE'
            ).order_by('-date').first()

            km_proxima_revisao = 0
            if last_preventive:
                km_proxima_revisao = last_preventive.mileage_at_maintenance + vehicle.maintenance_interval_km
            else:
                km_proxima_revisao = vehicle.maintenance_interval_km

            km_atual = vehicle.current_mileage
            km_faltando = km_proxima_revisao - km_atual

            logger.debug(
                f"[Verificação Alerta] Veículo {vehicle.plate}: "
                f"KM Atual={km_atual}, Próxima KM={km_proxima_revisao}, "
                f"KM Faltando={km_faltando}, Limite={LIMITE_ALERTA_KM}"
            )

            # Regra de Negócio RF006: Inclui no alerta se atrasado ou próximo
            if km_atual >= (km_proxima_revisao - LIMITE_ALERTA_KM):
                logger.debug(f"[Alerta Ativado] Veículo {vehicle.plate} adicionado à lista.")
                vehicles_in_alert.append({
                    'vehicle': vehicle,
                    'km_faltando': km_faltando,
                    'proxima_revisao_km': km_proxima_revisao
                })

        context['alert_list'] = vehicles_in_alert

        logger.info(
            f"Dashboard processado para {user}. "
            f"Alertas encontrados (pós-filtro): {len(vehicles_in_alert)}."
        )

        return context
