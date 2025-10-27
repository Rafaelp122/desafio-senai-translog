from django.db import models
from django.contrib.auth.models import User


class Vehicle(models.Model):
    """
    Armazena um único veículo da frota.

    Este modelo é a entidade central para o gerenciamento da frota,
    contendo informações básicas e o estado de quilometragem.
    """

    # Validação RF007 (placa única) é garantida por 'unique=True'
    plate = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Placa"
    )
    make = models.CharField(max_length=50, verbose_name="Marca")
    model = models.CharField(max_length=50, verbose_name="Modelo")
    year = models.IntegerField(verbose_name="Ano de Fabricação")

    current_mileage = models.IntegerField(
        default=0,
        verbose_name="Quilometragem Atual"
    )

    # Define o ciclo padrão de manutenção (ex: a cada 10.000 km)
    maintenance_interval_km = models.IntegerField(
        default=10000,
        verbose_name="Intervalo de Revisão (KM)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )

    def __str__(self) -> str:
        """Retorna uma representação em string do veículo."""
        return f"{self.make} {self.model} ({self.plate})"


class MaintenanceRecord(models.Model):
    """
    Registra um evento de manutenção (preventiva ou corretiva)
    associado a um veículo.
    """

    class MaintenanceType(models.TextChoices):
        """Define as escolhas para o tipo de manutenção."""
        PREVENTIVE = 'PRE', 'Preventiva'
        CORRECTIVE = 'COR', 'Corretiva'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        # related_name permite acesso reverso: meu_veiculo.maintenance_records.all()
        related_name="maintenance_records",
        verbose_name="Veículo"
    )

    maintenance_type = models.CharField(
        max_length=3,
        choices=MaintenanceType.choices,
        verbose_name="Tipo de Manutenção"
    )
    date = models.DateField(verbose_name="Data da Manutenção")
    description = models.TextField(verbose_name="Descrição do Serviço")

    # Quilometragem do veículo no momento exato da manutenção
    mileage_at_maintenance = models.IntegerField(
        verbose_name="KM no momento da Manutenção"
    )

    parts_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Custo das Peças"
    )

    labor_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Custo Mão de Obra"
    )

    # Se o mecânico (Usuário) for excluído, o registro de manutenção
    # permanece, mas este campo fica nulo.
    responsible_mechanic = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Mecânico Responsável"
    )

    def __str__(self) -> str:
        """Retorna uma representação em string do registro."""
        # 'get_maintenance_type_display' usa o valor legível ('Preventiva')
        return f"{self.get_maintenance_type_display()} em {self.vehicle.plate} - {self.date}"


class MileageRecord(models.Model):
    """
    Armazena um registro pontual de quilometragem inserido por um motorista.

    Esta tabela cumpre o RF005 e sua principal lógica de negócio
    está no método .save().
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="mileage_records",
        verbose_name="Veículo"
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="mileage_logs",
        verbose_name="Motorista"
    )
    date_recorded = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do Registro"
    )
    mileage = models.IntegerField(verbose_name="Quilometragem Registrada")

    def save(self, *args, **kwargs) -> None:
        """
        Sobrescreve o 'save' para atualizar a quilometragem do veículo (RF005).

        Sempre que um novo registro de KM é salvo, este método verifica
        se a quilometragem registrada é maior que a 'current_mileage'
        do veículo e, em caso afirmativo, atualiza o veículo.
        """

        # Regra de Negócio: Garante que a quilometragem do veículo
        # nunca seja atualizada para um valor menor que o atual.
        if self.mileage > self.vehicle.current_mileage:
            self.vehicle.current_mileage = self.mileage
            self.vehicle.save()  # Atualiza o objeto Vehicle relacionado

        # Chama o 'save' original para salvar este objeto MileageRecord
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Retorna uma representação em string do registro de KM."""
        return f"KM de {self.vehicle.plate} em {self.date_recorded.strftime('%Y-%m-%d')}: {self.mileage}"
