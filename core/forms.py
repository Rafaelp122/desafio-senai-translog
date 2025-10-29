from django import forms
from .models import MileageRecord, Vehicle


class MileageRecordForm(forms.ModelForm):
    """
    Formulário para o registo de quilometragem por motoristas.

    Este formulário é baseado no modelo MileageRecord, mas personaliza
    o campo 'vehicle' para exibir apenas os veículos atribuídos
    ao utilizador autenticado (motorista).
    """

    # Sobrescrevemos o campo 'vehicle' para controlar o queryset dinamicamente.
    # O queryset inicial é vazio; será populado no __init__ com base no utilizador.
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),
        label="Veículo Conduzido",
        empty_label="-- Selecione o Veículo --",  # Texto inicial do dropdown
        widget=forms.Select(attrs={'class': 'form-select'})  # Aplica estilo Bootstrap
    )

    class Meta:
        """
        Configurações do ModelForm.
        """
        model = MileageRecord
        # Campos a serem exibidos no formulário
        fields = ['vehicle', 'mileage']
        labels = {
            # Melhora a clareza do rótulo para o utilizador final
            'mileage': 'Quilometragem Atual (registada no odómetro)',
        }
        widgets = {
            # Aplica estilo Bootstrap ao campo de quilometragem
            'mileage': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializador personalizado do formulário.

        Recebe o 'user' (motorista logado) passado pela View e
        filtra o queryset do campo 'vehicle' de acordo.
        """
        # Remove o argumento 'user' de kwargs antes de chamar o pai,
        # pois o ModelForm padrão não o espera.
        user = kwargs.pop('user', None)

        # Chama o inicializador da classe pai (ModelForm)
        super().__init__(*args, **kwargs)

        # Aplica a lógica de filtragem apenas se um utilizador foi passado
        if user:
            # Lógica de Permissão por Objeto (RF005):
            # Filtra a lista de veículos para incluir apenas aqueles
            # onde o utilizador atual está no campo ManyToMany 'assigned_drivers'.
            assigned_vehicles = Vehicle.objects.filter(assigned_drivers=user)
            self.fields['vehicle'].queryset = assigned_vehicles

            # Feedback visual se o motorista não tiver veículos atribuídos
            if not assigned_vehicles.exists():
                self.fields['vehicle'].widget.attrs['disabled'] = True
                self.fields['vehicle'].help_text = (
                    "Nenhum veículo está atualmente atribuído a si. "
                    "Contacte o administrador."
                )
                self.fields['mileage'].widget.attrs['disabled'] = True

        # Nota: O campo 'driver' do modelo MileageRecord será definido
        # na View (durante o form_valid), associando o registo
        # ao utilizador autenticado (request.user).
