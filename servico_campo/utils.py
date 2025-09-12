# Em servico_campo/utils.py
from django.core.mail import get_connection
from configuracoes.models import ConfiguracaoEmail


def get_email_backend():
    """
    Busca a configuração de e-mail do banco de dados e retorna uma
    conexão de e-mail pronta para ser usada.
    """
    try:
        config = ConfiguracaoEmail.objects.first()
        if not config:
            print("DEBUG: Nenhuma configuração encontrada. A tabela está vazia.")
            return None

        # Se encontrou a config, continua normalmente
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=config.email_host,
            port=config.email_port,
            username=config.email_host_user,
            password=config.email_host_password,
            use_tls=config.email_use_tls,
            use_ssl=config.email_use_ssl,
            fail_silently=False
        )
    except Exception as e:
        # ESTA É A MUDANÇA IMPORTANTE: VAMOS IMPRIMIR O ERRO
        print("--------------------------------------------------")
        print(f"DEBUG: ERRO AO BUSCAR CONFIGURAÇÃO DE E-MAIL: {e}")
        print("--------------------------------------------------")
        return None
