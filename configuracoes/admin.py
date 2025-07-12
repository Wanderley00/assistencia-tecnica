# configuracoes/admin.py
from django.contrib import admin
from .models import TipoManutencao, TipoDocumento, FormaPagamento, CategoriaDespesa, PoliticaDespesa


@admin.register(TipoManutencao)
class TipoManutencaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    search_fields = ('nome',)
    list_filter = ('ativo',)


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    search_fields = ('nome',)
    list_filter = ('ativo',)


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    search_fields = ('nome',)
    list_filter = ('ativo',)


@admin.register(CategoriaDespesa)
class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)


@admin.register(PoliticaDespesa)
class PoliticaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'arquivo', 'ativa', 'data_upload')
    list_filter = ('ativa',)
    search_fields = ('nome',)
