# servico_campo/urls.py

from django.urls import path
from . import views
from django.utils.translation import gettext_lazy as _  # Para internacionalização

app_name = 'servico_campo'

urlpatterns = [

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('perfil/', views.perfil_view, name='perfil'),

    path('load-equipamentos/', views.load_equipamentos, name='load_equipamentos'),

    path('despesas/pendentes/', views.DespesaPendenteListView.as_view(),
         name='lista_despesas_pendentes'),
    path('despesa/<int:pk>/aprovar/',
         views.aprovar_despesa, name='aprovar_despesa'),
    path('despesa/<int:pk>/rejeitar/',
         views.rejeitar_despesa, name='rejeitar_despesa'),


    # URLs para Ordem de Serviço
    path('ordens-servico/', views.OrdemServicoListView.as_view(), name='lista_os'),
    path('ordens-servico/nova/',
         views.OrdemServicoCreateView.as_view(), name='nova_os'),
    path('ordens-servico/<int:pk>/', views.OrdemServicoDetailView.as_view(),
         name='detalhe_os'),  # Adicionada/descomentada
    path('ordens-servico/<int:pk>/editar/',
         views.OrdemServicoUpdateView.as_view(), name='editar_os'),
    path('ordens-servico/<int:pk>/excluir/',
         views.OrdemServicoDeleteView.as_view(), name='excluir_os'),
    # path('ordens-servico/<int:pk>/excluir/', views.OrdemServicoDeleteView.as_view(), name='excluir_os'),

    path('ordens-servico/<int:pk>/mudar-status/',
         views.mudar_status_os, name='mudar_status_os'),

    path('ordens-servico/<int:pk>/encerrar/',
         views.OrdemServicoEncerramentoView.as_view(), name='encerrar_os'),

    # URLs para Upload de Documentos (a serem criadas)
    path('ordens-servico/<int:os_pk>/documentos/novo/',
         views.DocumentoOSCreateView.as_view(), name='upload_documento_os'),

    path('documentos/<int:pk>/excluir/',
         views.DocumentoOSDeleteView.as_view(), name='excluir_documento_os'),

    path('ordens-servico/<int:os_pk>/despesas/nova/',
         views.DespesaCreateView.as_view(), name='nova_despesa'),

    # URLs para Registro de Ponto (a serem criadas)
    path('ordens-servico/<int:os_pk>/ponto/registrar/',
         views.RegistroPontoCreateView.as_view(), name='registrar_ponto'),
    path('ordens-servico/<int:os_pk>/ponto/<int:pk>/encerrar/', views.RegistroPontoUpdateView.as_view(),
         name='encerrar_ponto'),  # Para encerrar um ponto em aberto
    # Opcional: API para verificar ponto em aberto
    path('api/ponto-aberto/<int:os_pk>/',
         views.check_open_point_api, name='api_ponto_aberto'),
    path('ordens-servico/<int:os_pk>/relatorios/novo/',
         views.RelatorioCampoCreateView.as_view(), name='novo_relatorio_campo'),
    path('ordens-servico/<int:os_pk>/relatorios/<int:pk>/editar/',
         views.RelatorioCampoUpdateView.as_view(), name='editar_relatorio_campo'),
    path('relatorios-campo/<int:pk>/download-pdf/', views.relatorio_campo_pdf_view,
         name='download_relatorio_pdf'),  # Futuro: Geração de PDF
    path('relatorios-campo/<int:relatorio_pk>/fotos/novo/',
         views.FotoRelatorioCreateView.as_view(), name='upload_foto_relatorio'),
    # Opcional: view para excluir foto

    path('gestao/clientes/', views.ClienteListView.as_view(), name='lista_clientes'),
    path('gestao/clientes/novo/',
         views.ClienteCreateView.as_view(), name='novo_cliente'),
    path('gestao/clientes/<int:pk>/',
         views.ClienteDetailView.as_view(), name='detalhe_cliente'),
    path('gestao/clientes/<int:pk>/editar/',
         views.ClienteUpdateView.as_view(), name='editar_cliente'),
    path('gestao/clientes/<int:pk>/excluir/',
         views.ClienteDeleteView.as_view(), name='excluir_cliente'),

    path('gestao/equipamentos/', views.EquipamentoListView.as_view(),
         name='lista_equipamentos'),
    path('gestao/equipamentos/novo/',
         views.EquipamentoCreateView.as_view(), name='novo_equipamento'),
    path('gestao/equipamentos/<int:pk>/editar/',
         views.EquipamentoUpdateView.as_view(), name='editar_equipamento'),
    path('gestao/equipamentos/<int:pk>/excluir/',
         views.EquipamentoDeleteView.as_view(), name='excluir_equipamento'),

    path('gestao/usuarios/', views.UserListView.as_view(), name='lista_usuarios'),
    path('gestao/usuarios/novo/',
         views.UserCreateView.as_view(), name='novo_usuario'),
    path('gestao/usuarios/<int:pk>/editar/',
         views.UserUpdateView.as_view(), name='editar_usuario'),

    path('gestao/grupos/', views.GroupListView.as_view(), name='lista_grupos'),
    path('gestao/grupos/novo/', views.GroupCreateView.as_view(), name='novo_grupo'),
    path('gestao/grupos/<int:pk>/editar/',
         views.GroupUpdateView.as_view(), name='editar_grupo'),
    path('gestao/grupos/<int:pk>/excluir/',
         views.GroupDeleteView.as_view(), name='excluir_grupo'),

    path('ordens-servico/abrir-chamado/',
         views.OrdemServicoClienteCreateView.as_view(), name='abrir_chamado_os'),

    path('ordens-servico/<int:pk>/planejamento/',
         views.OrdemServicoPlanejamentoUpdateView.as_view(), name='planejar_os'),

    path('gantt-chart/', views.GanttChartView.as_view(), name='gantt_chart'),

    path('api/gantt-data/', views.GanttDataJsonView.as_view(), name='api_gantt_data'),

    path('gestao/usuarios/<int:pk>/excluir/',
         views.UserDeleteView.as_view(), name='excluir_usuario'),
]
