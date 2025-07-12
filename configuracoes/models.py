# configuracoes/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class TipoManutencao(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name="Nome do Tipo de Manutenção")
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
