from django.core.mail.backends.smtp import EmailBackend
from configuracoes.models import ConfiguracaoEmail  # <-- AQUI ESTÁ A CORREÇÃO


class DatabaseEmailBackend(EmailBackend):
    """
    Um backend de e-mail SMTP customizado que busca as credenciais
    (host, port, user, password, etc.) do banco de dados no momento da sua
    criação, garantindo que as configurações mais atuais sejam sempre usadas.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)

        try:
            config = ConfiguracaoEmail.objects.first()
            if config:
                self.host = config.email_host
                self.port = config.email_port
                self.username = config.email_host_user
                self.password = config.email_host_password
                self.use_tls = config.email_use_tls
                self.use_ssl = config.email_use_ssl
        except Exception:
            pass
