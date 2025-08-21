# configuracoes/urls.py
from django.urls import path
from . import views

app_name = 'configuracoes'

urlpatterns = [
    # Tipos de Manutenção
    path('tipos-manutencao/', views.TipoManutencaoListView.as_view(),
         name='lista_tipos_manutencao'),
    path('tipos-manutencao/novo/', views.TipoManutencaoCreateView.as_view(),
         name='novo_tipo_manutencao'),
    path('tipos-manutencao/<int:pk>/editar/',
         views.TipoManutencaoUpdateView.as_view(), name='editar_tipo_manutencao'),
    path('tipos-manutencao/<int:pk>/excluir/',
         views.TipoManutencaoDeleteView.as_view(), name='excluir_tipo_manutencao'),

    # Tipos de Documento
    path('tipos-documento/', views.TipoDocumentoListView.as_view(),
         name='lista_tipos_documento'),
    path('tipos-documento/novo/', views.TipoDocumentoCreateView.as_view(),
         name='novo_tipo_documento'),
    path('tipos-documento/<int:pk>/editar/',
         views.TipoDocumentoUpdateView.as_view(), name='editar_tipo_documento'),
    path('tipos-documento/<int:pk>/excluir/',
         views.TipoDocumentoDeleteView.as_view(), name='excluir_tipo_documento'),

    # Formas de Pagamento
    path('formas-pagamento/', views.FormaPagamentoListView.as_view(),
         name='lista_formas_pagamento'),
    path('formas-pagamento/novo/', views.FormaPagamentoCreateView.as_view(),
         name='nova_forma_pagamento'),
    path('formas-pagamento/<int:pk>/editar/',
         views.FormaPagamentoUpdateView.as_view(), name='editar_forma_pagamento'),
    path('formas-pagamento/<int:pk>/excluir/',
         views.FormaPagamentoDeleteView.as_view(), name='excluir_forma_pagamento'),

    # URLs para CategoriaDespesa
    path('categorias-despesa/', views.CategoriaDespesaListView.as_view(),
         name='lista_categorias_despesa'),
    path('categorias-despesa/nova/',
         views.CategoriaDespesaCreateView.as_view(), name='nova_categoria_despesa'),
    path('categorias-despesa/<int:pk>/editar/',
         views.CategoriaDespesaUpdateView.as_view(), name='editar_categoria_despesa'),
    path('categorias-despesa/<int:pk>/excluir/',
         views.CategoriaDespesaDeleteView.as_view(), name='excluir_categoria_despesa'),

    # URLs para PoliticaDespesa
    path('politicas-despesa/', views.PoliticaDespesaListView.as_view(),
         name='lista_politicas_despesa'),
    path('politicas-despesa/nova/',
         views.PoliticaDespesaCreateView.as_view(), name='nova_politica_despesa'),
    path('politicas-despesa/<int:pk>/editar/',
         views.PoliticaDespesaUpdateView.as_view(), name='editar_politica_despesa'),
    path('politicas-despesa/<int:pk>/excluir/',
         views.PoliticaDespesaDeleteView.as_view(), name='excluir_politica_despesa'),

    # NOVO: URL para Configurações de Email
    path('configuracao-email/', views.ConfiguracaoEmailUpdateView.as_view(),
         name='configuracao_email'),

    path('configuracao-email/', views.configuracao_email_view,
         name='configuracao_email'),

    path('tipos-relatorio/', views.TipoRelatorioListView.as_view(),
         name='lista_tipos_relatorio'),
    path('tipos-relatorio/novo/', views.TipoRelatorioCreateView.as_view(),
         name='novo_tipo_relatorio'),
    path('tipos-relatorio/<int:pk>/editar/',
         views.TipoRelatorioUpdateView.as_view(), name='editar_tipo_relatorio'),
    path('tipos-relatorio/<int:pk>/excluir/',
         views.TipoRelatorioDeleteView.as_view(), name='excluir_tipo_relatorio'),
]
