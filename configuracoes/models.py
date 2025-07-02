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
