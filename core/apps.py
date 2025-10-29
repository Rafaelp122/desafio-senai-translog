from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuração para a aplicação 'core'.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Este método é chamado pelo Django quando a aplicação está pronta.

        É o local recomendado para importar e registar os sinais (signals),
        garantindo que eles sejam "ouvidos" pelo Django.
        """
        # Importa o módulo de sinais para que o decorador @receiver funcione.
        import core.signals
