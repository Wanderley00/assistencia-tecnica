# servico_campo/urls.py

from django.urls import path, include
from . import views
from django.utils.translation import gettext_lazy as _  # Para internacionalização

from django.conf import settings
from django.conf.urls.static import static

app_name = 'servico_campo'

urlpatterns = [

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('perfil/', views.perfil_view, name='perfil'),

    path('load-equipamentos/', views.load_equipamentos, name='load_equipamentos'),

    path('despesas/pendentes/', views.DespesaPendenteListView.as_view(),
         name='lista_despesas_pendentes'),
    # NOVO: URL unificada para aprovar/rejeitar despesa com comentário
    path('despesa/<int:pk>/<str:acao>/',
         views.DespesaAprovarRejeitarView.as_view(), name='acao_despesa'),


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
    path('despesas/<int:pk>/editar/',
         views.DespesaUpdateView.as_view(), name='editar_despesa'),
    path('despesas/<int:pk>/', views.DespesaDetailView.as_view(),
         name='detalhe_despesa'),
    path('despesas/<int:pk>/excluir/',
         views.DespesaDeleteView.as_view(), name='excluir_despesa'),

    # URLs para Registro de Ponto (a serem criadas)
    path('ordens-servico/<int:os_pk>/ponto/registrar/',
         views.RegistroPontoCreateView.as_view(), name='registrar_ponto'),
    path('ordens-servico/<int:os_pk>/ponto/<int:pk>/encerrar/', views.RegistroPontoEncerramentoView.as_view(),
         name='encerrar_ponto'),
    path('registros-ponto/<int:pk>/excluir/',
         views.RegistroPontoDeleteView.as_view(), name='excluir_registro_ponto'),
    path('registros-ponto/<int:pk>/',
         views.RegistroPontoDetailView.as_view(), name='detalhe_registro_ponto'),
    # NOVO: URL para editar um registro de ponto existente (para correção)
    path('registros-ponto/<int:pk>/editar/',
         views.RegistroPontoEditView.as_view(), name='editar_registro_ponto'),
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

    # URLs para Regras de Jornada de Trabalho
    path('gestao/regras-jornada/', views.RegraJornadaTrabalhoListView.as_view(),
         name='lista_regras_jornada'),
    path('gestao/regras-jornada/nova/',
         views.RegraJornadaTrabalhoCreateView.as_view(), name='nova_regra_jornada'),
    path('gestao/regras-jornada/<int:pk>/editar/',
         views.RegraJornadaTrabalhoUpdateView.as_view(), name='editar_regra_jornada'),
    path('gestao/regras-jornada/<int:pk>/excluir/',
         views.RegraJornadaTrabalhoDeleteView.as_view(), name='excluir_regra_jornada'),

    # URLs para Gestão de Categorias e Subcategorias de Problemas
    path('gestao/categorias-problema/', views.CategoriaProblemaListView.as_view(),
         name='lista_categorias_problema'),
    path('gestao/categorias-problema/nova/',
         views.CategoriaProblemaCreateView.as_view(), name='nova_categoria_problema'),
    path('gestao/categorias-problema/<int:pk>/editar/',
         views.CategoriaProblemaUpdateView.as_view(), name='editar_categoria_problema'),
    path('gestao/categorias-problema/<int:pk>/excluir/',
         views.CategoriaProblemaDeleteView.as_view(), name='excluir_categoria_problema'),

    path('gestao/subcategorias-problema/', views.SubcategoriaProblemaListView.as_view(),
         name='lista_subcategorias_problema'),
    path('gestao/subcategorias-problema/nova/',
         views.SubcategoriaProblemaCreateView.as_view(), name='nova_subcategoria_problema'),
    path('gestao/subcategorias-problema/<int:pk>/editar/',
         views.SubcategoriaProblemaUpdateView.as_view(), name='editar_subcategoria_problema'),
    path('gestao/subcategorias-problema/<int:pk>/excluir/',
         views.SubcategoriaProblemaDeleteView.as_view(), name='excluir_subcategoria_problema'),

    path('api/load-subcategorias-problema/', views.load_subcategorias_problema,
         name='api_load_subcategorias_problema'),  # API para JS

    # URLs para Contas a Pagar
    path('contas-a-pagar/', views.ContaPagarListView.as_view(),
         name='lista_contas_a_pagar'),
    path('contas-a-pagar/<int:pk>/editar/',
         views.ContaPagarUpdateView.as_view(), name='editar_conta_a_pagar'),
    # path('contas-a-pagar/<int:pk>/detalhes/',
    # views.ContaPagarDetailView.as_view(), name='detalhe_conta_a_pagar'),

    path('minhas-despesas/', views.MinhasDespesasListView.as_view(),
         name='minhas_despesas'),

    path('clientes/upload-massa/', views.BulkClientUploadView.as_view(),
         name='upload_massa_clientes'),

    path('equipamentos/upload-massa/', views.BulkEquipmentUploadView.as_view(),
         name='upload_massa_equipamentos'),

    path('clientes/cadastro-em-massa/', views.cadastro_massa_clientes,
         name='cadastro_massa_clientes'),

    path('clientes/download-modelo/', views.download_modelo_clientes,
         name='download_modelo_clientes'),

    path('gestao/equipamentos/cadastro-em-massa/',
         views.cadastro_massa_equipamentos, name='cadastro_massa_equipamentos'),
    path('gestao/equipamentos/download-modelo/',
         views.download_modelo_equipamentos, name='download_modelo_equipamentos'),

    path('gestao/equipamentos/<int:pk>/editar/',
         views.EquipamentoUpdateView.as_view(), name='editar_equipamento'),

    path('configuracoes/testar-email/',
         views.testar_conexao_email, name='testar_conexao_email'),

    # URLs para Perfil de Usuário / Dados Bancários (Adicione esta)
    path('meu-perfil/dados-bancarios/',
         views.PerfilUsuarioUpdateView.as_view(), name='editar_dados_bancarios'),

    path('api/calcular-horas/', views.calcular_horas_api,
         name='api_calcular_horas'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    # Se você também estiver servindo arquivos estáticos localmente em dev:
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    path("ordem/<int:pk>/aprovar/", views.aprovar_ordem_servico, name="aprovar_os"),
    path("ordem/<int:pk>/reprovar/",
         views.reprovar_ordem_servico, name="reprovar_os"),
    path("aprovacao-ordens-concluidas/", views.AprovacaoOrdensConcluidasListView.as_view(),
         name="aprovacao_ordens_concluidas"),
