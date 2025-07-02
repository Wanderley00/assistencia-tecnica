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
]
