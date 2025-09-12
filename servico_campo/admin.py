from django.contrib import admin
from .models import Cliente, Equipamento, OrdemServico, DocumentoOS, \
    RegistroPonto, RelatorioCampo, FotoRelatorio, Despesa, ContaPagar

# Importe o novo modelo
from .models import Cliente, Equipamento, OrdemServico, MembroEquipe, RegistroPonto, RelatorioCampo, RegraJornadaTrabalho, \
    CategoriaProblema, SubcategoriaProblema, ProblemaRelatorio

admin.site.register(Cliente)
admin.site.register(Equipamento)
admin.site.register(OrdemServico)
admin.site.register(DocumentoOS)
admin.site.register(RegistroPonto)
admin.site.register(RelatorioCampo)
admin.site.register(FotoRelatorio)
admin.site.register(Despesa)


@admin.register(RegraJornadaTrabalho)
class RegraJornadaTrabalhoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'horas_normais_diarias',
                    'inicio_jornada_normal', 'fim_jornada_normal', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('nome',)


@admin.register(CategoriaProblema)
class CategoriaProblemaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)


@admin.register(SubcategoriaProblema)
class SubcategoriaProblemaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'ativo')
    list_filter = ('categoria', 'ativo',)
    search_fields = ('nome', 'categoria__nome',)
    # Ajuda a selecionar a categoria em listas grandes
    raw_id_fields = ('categoria',)


@admin.register(ProblemaRelatorio)
class ProblemaRelatorioAdmin(admin.ModelAdmin):
    list_display = ('relatorio', 'categoria', 'subcategoria', 'observacao')
    list_filter = ('categoria', 'subcategoria', 'relatorio__ordem_servico')
    search_fields = ('observacao', 'categoria__nome',
                     'subcategoria__nome', 'relatorio__ordem_servico__numero_os')
    # Para facilitar seleção
    raw_id_fields = ('relatorio', 'categoria', 'subcategoria')


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('despesa', 'status_pagamento',
                    'responsavel_pagamento', 'data_criacao', 'data_atualizacao')
    list_filter = ('status_pagamento', 'responsavel_pagamento')
    search_fields = ('despesa__descricao',
                     'despesa__ordem_servico__numero_os', 'comentario')
    # Para facilitar seleção em listas grandes
    raw_id_fields = ('despesa', 'responsavel_pagamento')
