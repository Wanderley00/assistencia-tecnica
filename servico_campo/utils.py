# Em servico_campo/utils.py
from django.core.mail import get_connection
from configuracoes.models import ConfiguracaoEmail
from django.contrib.auth import get_user_model
from .models import Notificacao

User = get_user_model()


def criar_notificacao(destinatario: User, mensagem: str, link: str = None):
    """
    Cria e salva uma notificação no banco de dados para um usuário específico.

    Args:
        destinatario (User): O objeto de usuário que receberá a notificação.
        mensagem (str): O texto da notificação.
        link (str, optional): A URL para a qual o usuário será redirecionado. Defaults to None.
    """
    if not isinstance(destinatario, User):
        # Medida de segurança para garantir que estamos recebendo o tipo de objeto correto
        print(
            f"AVISO: Tentativa de criar notificação para um objeto que não é um usuário: {destinatario}")
        return

    try:
        Notificacao.objects.create(
            destinatario=destinatario,
            mensagem=mensagem,
            link=link
        )
    except Exception as e:
        # Imprime um erro no console se a criação da notificação falhar por algum motivo
        print(f"ERRO ao criar notificação para {destinatario.username}: {e}")


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
