# configuracoes/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class TipoManutencao(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Tipo de Serviço")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tipo de Manutenção"
        verbose_name_plural = "Tipos de Manutenção"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoDocumento(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Tipo de Documento")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class FormaPagamento(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome da Forma de Pagamento")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Forma de Pagamento"
        verbose_name_plural = "Formas de Pagamento"
        ordering = ['nome']

    def __str__(self):
        return self.nome


# NOVO MODELO: CategoriaDespesa
class CategoriaDespesa(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name=_("Nome da Categoria"))
    ativo = models.BooleanField(default=True, verbose_name=_("Ativo"))

    class Meta:
        verbose_name = _("Categoria de Despesa")
        verbose_name_plural = _("Categorias de Despesas")
        ordering = ['nome']

    def __str__(self):
        return self.nome


class PoliticaDespesa(models.Model):
    """
    Armazena o arquivo de política de despesas para consulta.
    Permite apenas um arquivo ativo por vez (ou um histórico de versões).
    """
    nome = models.CharField(max_length=255, verbose_name=_(
        "Nome da Política"), help_text=_("Ex: Política de Reembolso de Despesas V1.0"))
    arquivo = models.FileField(
        upload_to='politicas_despesa/', verbose_name=_("Arquivo da Política (PDF)"))
    data_upload = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Data de Upload"))
    ativa = models.BooleanField(default=True, verbose_name=_("Ativa"))

    class Meta:
        verbose_name = _("Política de Despesa")
        verbose_name_plural = _("Políticas de Despesas")
        ordering = ['-data_upload']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Garante que apenas uma política esteja ativa por vez
        if self.ativa:
            PoliticaDespesa.objects.filter(ativa=True).exclude(
                pk=self.pk).update(ativa=False)
        super().save(*args, **kwargs)


class ConfiguracaoEmail(models.Model):
    """
    Armazena as configurações de e-mail SMTP para envio pela aplicação.
    Deve haver apenas uma instância deste modelo.
    """
    email_backend = models.CharField(
        max_length=255,
        default='django.core.mail.backends.smtp.EmailBackend',
        verbose_name=_("Backend de Email"),
        help_text=_(
            "Ex: django.core.mail.backends.smtp.EmailBackend (para SMTP) ou django.core.mail.backends.console.EmailBackend (para testes).")
    )
    email_host = models.CharField(
        max_length=255, verbose_name=_("Host SMTP"), blank=True, null=True,
        help_text=_("Endereço do servidor SMTP (ex: smtp.gmail.com).")
    )
    email_port = models.IntegerField(
        verbose_name=_("Porta SMTP"), default=587, blank=True, null=True,
        help_text=_("Porta do servidor SMTP (ex: 587 para TLS, 465 para SSL).")
    )
    email_use_tls = models.BooleanField(
        verbose_name=_("Usar TLS?"), default=True,
        help_text=_(
            "Marque para usar TLS (Transport Layer Security) para conexão segura.")
    )
    email_use_ssl = models.BooleanField(
        verbose_name=_("Usar SSL?"), default=False,
        help_text=_(
            "Marque para usar SSL (Secure Sockets Layer). Se TLS for True, SSL deve ser False.")
    )
    email_host_user = models.CharField(
        max_length=255, verbose_name=_("Usuário SMTP"), blank=True, null=True,
        help_text=_(
            "Nome de usuário para autenticação SMTP (geralmente seu e-mail completo).")
    )
    email_host_password = models.CharField(
        max_length=255, verbose_name=_("Senha SMTP / Chave API"), blank=True, null=True,
        help_text=_(
            "Senha ou chave de API para autenticação SMTP. Nunca coloque sua senha principal aqui.")
    )
    default_from_email = models.CharField(
        max_length=255, verbose_name=_("Remetente Padrão"), blank=True, null=True,
        help_text=_(
            "Endereço de e-mail que aparecerá como remetente padrão (ex: noreply@seusistema.com).")
    )

    class Meta:
        verbose_name = _("Configuração de Email")
        verbose_name_plural = _("Configurações de Email")

    def __str__(self):
        return _("Configurações de E-mail do Sistema")

    # Método para garantir que só haja uma instância
    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracaoEmail.objects.exists():
            raise ValidationError(
                _('Só pode haver uma instância de Configuração de Email.'))
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        # Garante que sempre haja uma instância com PK=1
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class TipoRelatorio(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name=_("Nome do Tipo de Relatório"))
    ativo = models.BooleanField(default=True, verbose_name=_("Ativo"))

    class Meta:
        verbose_name = _("Tipo de Relatório")
        verbose_name_plural = _("Tipos de Relatórios")
        ordering = ['nome']

    def __str__(self):
        return self.nome
