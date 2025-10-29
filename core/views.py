import logging
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Vehicle, MaintenanceRecord, MileageRecord
from .forms import MileageRecordForm

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


#  --- View para Registar KM (RF005) ---
class MileageRecordCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View baseada em classe para a criação de novos registos de quilometragem.

    Acessível apenas por utilizadores autenticados (`LoginRequiredMixin`)
    que possuam a permissão 'core.add_mileagerecord' (`PermissionRequiredMixin`),
    tipicamente atribuída apenas ao grupo 'Motorista'.

    Utiliza a `CreateView` genérica do Django para simplificar o processo
    de exibição e validação do formulário `MileageRecordForm`.
    """
    model = MileageRecord             # Define o modelo alvo da criação
    form_class = MileageRecordForm    # Especifica o formulário a ser utilizado
    template_name = 'core/mileage_record_form.html'  # Caminho para o template HTML

    # Permissão necessária para aceder a esta view (RF002)
    permission_required = 'core.add_mileagerecord'

    # URL ('name') para redirecionamento após a criação bem-sucedida do registo
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        """
        Adiciona o utilizador atual (`request.user`) aos argumentos (kwargs)
        passados para o inicializador (`__init__`) do `MileageRecordForm`.

        Isto permite que o formulário filtre dinamicamente o campo 'vehicle'
        para mostrar apenas os veículos atribuídos (`assigned_drivers`)
        ao motorista autenticado.
        """
        kwargs = super().get_form_kwargs() # Obtém os argumentos padrão da CreateView
        kwargs['user'] = self.request.user # Adiciona o 'user' ao dicionário
        return kwargs

    def form_valid(self, form):
        """
        Executado quando o formulário é submetido e considerado válido.

        Define automaticamente o campo 'driver' do `MileageRecord` como
        sendo o utilizador autenticado antes de salvar o objeto no banco de dados.
        Adiciona mensagens de feedback (sucesso) e regista logs informativos.
        """
        # Associa o registo de KM ao utilizador logado (motorista)
        # form.instance refere-se ao objeto MileageRecord que está a ser criado,
        # ainda antes de ser salvo no banco de dados.
        form.instance.driver = self.request.user

        # Mensagem de sucesso a ser exibida na próxima página (dashboard)
        messages.success(
            self.request,
            f"Quilometragem para o veículo {form.instance.vehicle.plate} "
            f"registada com sucesso ({form.instance.mileage} KM)."
        )
        # Log informativo para registo interno da operação bem-sucedida
        logger.info(
            f"Utilizador {self.request.user} registou KM {form.instance.mileage} "
            f"para o veículo {form.instance.vehicle.plate}."
        )

        # Chama o método 'form_valid' da classe pai (CreateView),
        # que efetivamente salva o 'form.instance' no banco de dados
        # e retorna uma resposta HTTP de redirecionamento para 'success_url'.
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Executado quando o formulário é submetido mas considerado inválido.

        Adiciona uma mensagem de erro genérica para o utilizador e
        regista os erros detalhados de validação do formulário nos logs (nível warning).
        """
        messages.error(
            self.request,
            "Erro ao registar quilometragem. Verifique os dados no formulário."
        )
        # Log de aviso com detalhes dos erros de validação, útil para depuração
        logger.warning(
            f"Tentativa falhada de registo de KM pelo utilizador {self.request.user}. "
            f"Erros do formulário: {form.errors.as_json()}"
        )
        # Chama o método 'form_invalid' da classe pai, que re-renderiza
        # o template ('template_name') com o formulário preenchido
        # e as mensagens de erro de cada campo.
        return super().form_invalid(form)
