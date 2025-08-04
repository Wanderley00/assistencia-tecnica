from django.urls import path, include

from .views import (
    OrdemServicoListAPIView, OrdemServicoDetailAPIView,
    RelatorioCampoCreateAPIView, DespesaCreateAPIView,
    TipoDocumentoListAPIView, DocumentoOSCreateAPIView,
    CategoriaDespesaListAPIView, FormaPagamentoListAPIView,
    RegistroPontoListCreateAPIView, RegistroPontoUpdateAPIView,
)

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

]
