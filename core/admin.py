from django.contrib import admin
from .models import Vehicle, MaintenanceRecord, MileageRecord


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Define a interface de administração para o modelo Vehicle.

    Personaliza a exibição em lista, adiciona filtros e 
    funcionalidade de busca.
    """

    # Define as colunas que aparecem na listagem principal de veículos
    list_display = (
        'plate',
        'make',
        'model',
        'year',
        'current_mileage',
        'maintenance_interval_km'
    )

    # Habilita uma barra de busca para pesquisar por estes campos
    search_fields = ('plate', 'make', 'model')

    # Adiciona filtros na barra lateral para facilitar a navegação
    list_filter = ('make', 'year')


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    """
    Define a interface de administração para o modelo MaintenanceRecord.

    Organiza o formulário de edição em seções (fieldsets) e otimiza
    a seleção de chaves estrangeiras com autocomplete.
    """

    list_display = (
        'vehicle',
        'date',
        'maintenance_type',
        'mileage_at_maintenance',
        'get_total_cost'
    )

    search_fields = (
        'vehicle__plate',  # Permite buscar pela placa do veículo relacionado
        'vehicle__model',
        'description'
    )
    list_filter = ('maintenance_type', 'date', 'vehicle__make')

    # Organiza o formulário de edição/criação em grupos lógicos
    fieldsets = (
        (None, {  # Seção principal, sem título
            'fields': ('vehicle', 'maintenance_type', 'date', 'description')
        }),
        ('Custos e Quilometragem', {
            'fields': ('mileage_at_maintenance', 'parts_cost', 'labor_cost')
        }),
        ('Responsável', {
            'fields': ('responsible_mechanic',)
        }),
    )

    # Otimiza a seleção de FKs, substituindo <select> por um campo de busca.
    autocomplete_fields = ('vehicle', 'responsible_mechanic')

    def get_search_results(self, request, queryset, search_term):
        """
        Personaliza os resultados da busca do autocomplete.
        """
        # Deixa o Django fazer a busca padrão primeiro
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Pega o nome do campo que está fazendo a busca
        field_name = request.GET.get('field_name')

        # Se for o campo 'responsible_mechanic'...
        if field_name == 'responsible_mechanic':
            # ...filtra o queryset para incluir APENAS usuários do grupo 'Mecanico'
            queryset = queryset.filter(groups__name='Mecanico')

        return queryset, use_distinct

    @admin.display(description='Custo Total')
    def get_total_cost(self, obj: MaintenanceRecord) -> float:
        """
        Este método serve apenas para 'envelopar' o método do modelo
        e dar a ele um 'description' (nome da coluna) personalizado.
        """
        return obj.get_total_cost()


@admin.register(MileageRecord)
class MileageRecordAdmin(admin.ModelAdmin):
    """
    Define a interface de administração para o modelo MileageRecord.
    """

    list_display = ('vehicle', 'date_recorded', 'mileage', 'driver')
    search_fields = ('vehicle__plate', 'driver__username')
    list_filter = ('date_recorded', 'vehicle__make')

    # Otimiza a seleção de Veículo e Motorista (User)
    autocomplete_fields = ('vehicle', 'driver')

    def get_search_results(self, request, queryset, search_term):
        """
        Personaliza os resultados da busca do autocomplete.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        field_name = request.GET.get('field_name')

        # Se for o campo 'driver'...
        if field_name == 'driver':
            # ...filtra o queryset para incluir APENAS usuários do grupo 'Motorista'
            queryset = queryset.filter(groups__name='Motorista')

        return queryset, use_distinct
