from django.urls import path, include

from .views import (
    OrdemServicoListAPIView, OrdemServicoDetailAPIView,
    RelatorioCampoCreateAPIView, DespesaCreateAPIView,
    TipoDocumentoListAPIView, DocumentoOSCreateAPIView,
    CategoriaDespesaListAPIView, FormaPagamentoListAPIView,
    RegistroPontoListCreateAPIView, RegistroPontoUpdateAPIView,
    calcular_horas_relatorio_api, CategoriaProblemaListAPIView,
    ConcluirOrdemServicoAPIView, MinhasDespesasListView
)

from . import views

# Importações para o JWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Endpoint para obter o token (login)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Endpoint para renovar um token expirado
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Sua URL de ordens de serviço
    path('ordens-servico/', OrdemServicoListAPIView.as_view(), name='api_os_list'),

    # Adicione esta linha para incluir as URLs de redefinição de senha
    path('password_reset/', include('django_rest_passwordreset.urls',
         namespace='password_reset')),

    # --- NOVAS ROTAS ---
    path('ordens-servico/<int:pk>/',
         OrdemServicoDetailAPIView.as_view(), name='api_os_detail'),
    path('ordens-servico/<int:os_pk>/relatorios/',
         RelatorioCampoCreateAPIView.as_view(), name='api_relatorio_create'),
    path('ordens-servico/<int:os_pk>/despesas/',
         DespesaCreateAPIView.as_view(), name='api_despesa_create'),

    # --- NOVAS ROTAS PARA DOCUMENTOS ---
    # Rota para listar os tipos de documento (CORRIGE O ERRO 404)
    path('tipos-documento/', TipoDocumentoListAPIView.as_view(),
         name='api_tipos_documento_list'),

    # Rota para fazer o upload de um novo documento para uma OS específica
    path('ordens-servico/<int:os_pk>/documentos/',
         DocumentoOSCreateAPIView.as_view(), name='api_documento_create'),

    # --- NOVAS ROTAS PARA A TELA DE DESPESAS ---
    path('categorias-despesa/', CategoriaDespesaListAPIView.as_view(),
         name='api_categoria_despesa_list'),
    path('formas-pagamento/', FormaPagamentoListAPIView.as_view(),
         name='api_forma_pagamento_list'),

    # --- NOVAS ROTAS PARA REGISTRO DE PONTO ---
    path('ordens-servico/<int:os_pk>/pontos/',
         RegistroPontoListCreateAPIView.as_view(), name='api_ponto_list_create'),
    path('pontos/<int:pk>/', RegistroPontoUpdateAPIView.as_view(),
         name='api_ponto_update'),

    path('despesas/<int:pk>/', views.DespesaDetailAPIView.as_view(),
         name='despesa-detail'),

    path('documentos/<int:pk>/', views.DocumentoOSDetailAPIView.as_view(),
         name='documento-detail'),

    path('ordens-servico/<int:os_pk>/calcular-horas-relatorio/',
         calcular_horas_relatorio_api,
         name='api_calcular_horas_relatorio'),

    path('ordens-servico/<int:os_pk>/relatorios/novo/',
         RelatorioCampoCreateAPIView.as_view(),
         name='api_relatorio_create_novo'),

    path('problemas/categorias/', CategoriaProblemaListAPIView.as_view(),
         name='lista_categorias_problema'),

    path('relatorios-campo/<int:relatorio_pk>/fotos/',
         views.FotoRelatorioCreateAPIView.as_view(), name='api_foto_relatorio_create'),

    path('relatorios-campo/<int:pk>/',
         views.RelatorioCampoDetailAPIView.as_view(), name='api_relatorio_detail'),

    path('tipos-relatorio/', views.TipoRelatorioListView.as_view(),
         name='api_tipos_relatorio_list'),

    path('ordens-servico/<int:os_pk>/concluir/',
         ConcluirOrdemServicoAPIView.as_view(), name='api_os_concluir'),

    path('despesas/minhas-despesas/', MinhasDespesasListView.as_view(),
         name='api_minhas_despesas_list'),

]
