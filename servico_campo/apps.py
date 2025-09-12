# Em /servico_campo/apps.py

from django.apps import AppConfig


class ServicoCampoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'servico_campo'

    def ready(self):
        """
        Este método é executado quando o Django está pronto.
        É o local ideal para importar e conectar os sinais.
        """
        # Importa o sinal e o receptor.
        # O import de 'servico_campo.views' é feito aqui dentro para evitar importações circulares.
        from django_rest_passwordreset.signals import reset_password_token_created
        from .views import password_reset_token_created_receiver

        # Conecta o sinal ao nosso receptor.
        reset_password_token_created.connect(
            password_reset_token_created_receiver)
        print("Sinal de redefinição de senha conectado.")

    def ready(self):
        """
        Este método é executado quando o aplicativo está pronto.
        É o local recomendado pelo Django para importar os sinais.
        """
        import servico_campo.signals  # noqa
