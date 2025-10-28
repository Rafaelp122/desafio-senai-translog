from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


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

    year = models.IntegerField(
        verbose_name="Ano de Fabricação",
        # Ano 1886 foi do primeiro carro, então 0 é seguro,
        # mas 1886 seria mais preciso. Vamos usar 0 por simplicidade.
        validators=[MinValueValidator(0)]
    )

    current_mileage = models.IntegerField(
        default=0,
        verbose_name="Quilometragem Atual",
        validators=[MinValueValidator(0)]
    )

    # Define o ciclo padrão de manutenção (ex: a cada 10.000 km)
    maintenance_interval_km = models.IntegerField(
        default=10000,
        verbose_name="Intervalo de Revisão (KM)",
        validators=[MinValueValidator(0)] # Intervalo não pode ser 0 ou negativo
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro"
    )

    assigned_drivers = models.ManyToManyField(
        User,
        related_name="assigned_vehicles",
        blank=True,  # Um veículo pode não ter nenhum motorista atribuído

        # Filtra o Admin para mostrar APENAS usuários
        # que pertencem ao grupo 'Motorista'.
        limit_choices_to={'groups__name': "Motorista"}
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

    mileage_at_maintenance = models.IntegerField(
        verbose_name="KM no momento da Manutenção",
        validators=[MinValueValidator(0)]
    )

    parts_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Custo das Peças",
        validators=[MinValueValidator(0.00)]
    )

    labor_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Custo Mão de Obra",
        validators=[MinValueValidator(0.00)]
    )

    responsible_mechanic = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Mecânico Responsável"
    )

    def get_total_cost(self) -> float:
        """Retorna a soma dos custos de peças e mão de obra."""
        return self.parts_cost + self.labor_cost

    def __str__(self) -> str:
        """Retorna uma representação em string do registro."""
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

    mileage = models.IntegerField(
        verbose_name="Quilometragem Registrada",
        validators=[MinValueValidator(0)]
    )

    def save(self, *args, **kwargs) -> None:
        """
        Sobrescreve o 'save' para atualizar a quilometragem do veículo (RF005).
        """
        if self.mileage > self.vehicle.current_mileage:
            self.vehicle.current_mileage = self.mileage
            self.vehicle.save() 

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Retorna uma representação em string do registro de KM."""
        return f"KM de {self.vehicle.plate} em {self.date_recorded.strftime('%Y-%m-%d')}: {self.mileage}"
