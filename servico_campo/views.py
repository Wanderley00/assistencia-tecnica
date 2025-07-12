# servico_campo/views.py

# Python / Django Imports
from io import BytesIO
import csv
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, FormView
from django.contrib.contenttypes.models import ContentType
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.db.models import Count
from django.db.models import Sum
# <<< CERTIFIQUE-SE DE QUE 'datetime' ESTÁ AQUI TAMBÉM
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json
from django.db.models import Min, Max
from django.db import models
from django import forms

# Imports Locais (do seu app)
from .models import (
    OrdemServico, Cliente, Equipamento, DocumentoOS, RegistroPonto,
    RelatorioCampo, FotoRelatorio, Despesa, MembroEquipe, RegraJornadaTrabalho,
    CategoriaProblema, SubcategoriaProblema, ProblemaRelatorio, ContaPagar
)
# NOVO IMPORT
from configuracoes.models import TipoManutencao, TipoDocumento, FormaPagamento, PoliticaDespesa

from .forms import (
    DocumentoOSForm, RegistroPontoForm, RelatorioCampoForm,
    FotoRelatorioForm, DespesaForm, EncerramentoOSForm, ClienteForm,
    EquipamentoForm, UserCreationFormCustom, UserUpdateFormCustom, GroupForm, OrdemServicoClienteForm,
    OrdemServicoPlanejamentoForm, OrdemServicoCreateForm, MembroEquipeFormSet, OrdemServicoUpdateForm, RegraJornadaTrabalhoForm,
    CategoriaProblemaForm, SubcategoriaProblemaForm, ProblemaRelatorioFormSet, RegistroPontoEntradaForm, RegistroPontoSaidaForm,
    ContaPagarForm, BulkClientUploadForm, BulkEquipmentUploadForm
)


def organizar_permissoes():
    """
    Busca todas as permissões e as organiza em um dicionário
    agrupado por modelo para exibição amigável no template.
    """
    permissoes_organizadas = {}
    # Remova 'permission' e 'group' da lista de modelos ignorados
    # <--- MUDANÇA AQUI: Removido 'permission', 'group'
    modelos_ignorados = ['logentry', 'contenttype', 'session']

    content_types = ContentType.objects.all().order_by('app_label', 'model')

    for ct in content_types:
        if ct.model in modelos_ignorados:
            continue

        permissions = ct.permission_set.all()

        if permissions:
            permission_ids = set(p.id for p in permissions)

            # Usar ct.app_label para diferenciar 'auth' de 'servico_campo'
            app_label = ct.app_label
            # Para modelos de usuários e grupos, use um nome amigável para a seção
            if app_label == 'auth':
                if ct.model == 'user':
                    modelo_nome_amigavel = "Usuários (Autenticação)"
                elif ct.model == 'group':
                    modelo_nome_amigavel = "Grupos (Autenticação)"
                else:
                    modelo_nome_amigavel = ct.model_class()._meta.verbose_name_plural.title(
                    ) if ct.model_class() else ct.model.title()
            else:
                modelo_nome_amigavel = ct.model_class()._meta.verbose_name_plural.title(
                ) if ct.model_class() else ct.model.title()

            # A chave do dicionário pode ser o nome amigável do modelo
            if modelo_nome_amigavel not in permissoes_organizadas:
                permissoes_organizadas[modelo_nome_amigavel] = {
                    'modelo': ct.model,
                    'permissoes': [],
                    'permissoes_ids': set()
                }

            # Adicionar permissões à lista existente para o modelo
            permissoes_organizadas[modelo_nome_amigavel]['permissoes'].extend(
                list(permissions))
            permissoes_organizadas[modelo_nome_amigavel]['permissoes_ids'].update(
                permission_ids)

    # Opcional: Para garantir uma ordem específica, você pode ordenar as chaves
    # por exemplo, colocando "Usuários" e "Grupos" no topo
    ordered_permissoes = {}
    if "Usuários (Autenticação)" in permissoes_organizadas:
        ordered_permissoes["Usuários (Autenticação)"] = permissoes_organizadas.pop(
            "Usuários (Autenticação)")
    if "Grupos (Autenticação)" in permissoes_organizadas:
        ordered_permissoes["Grupos (Autenticação)"] = permissoes_organizadas.pop(
            "Grupos (Autenticação)")

    # Adicionar o restante em ordem alfabética
    for key in sorted(permissoes_organizadas.keys()):
        ordered_permissoes[key] = permissoes_organizadas[key]

    return ordered_permissoes


# -------------------------------------------------------------
# Mixins e Funções Auxiliares de Permissão
# -------------------------------------------------------------

class GestorRequiredMixin(LoginRequiredMixin):
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not self.permission_required:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} não definiu um 'permission_required'. "
                "Você precisa adicionar a propriedade permission_required a esta view."
            )
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.has_perm(self.permission_required):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

# -------------------------------------------------------------
# Views Principais e de Ação
# -------------------------------------------------------------


@login_required
# Exige permissão para visualizar OSs para acessar o dashboard
@permission_required('servico_campo.view_ordemservico', raise_exception=True)
def dashboard_view(request):
    user = request.user
    context = {
        'ordens_em_execucao_count': 0, 'despesas_pendentes_count': 0,
        'os_pendentes_planejamento_count': 0, 'os_concluidas_mes_count': 0,
        'equipamentos_count': 0, 'custo_total_reembolso': 0.00,
        'status_labels': [], 'status_counts': [], 'status_colors': [],
        'tipo_labels': [], 'tipo_counts': [], 'tipo_colors': [],
        'ultimas_os_concluidas': OrdemServico.objects.none(),
        'minhas_os_planejadas': OrdemServico.objects.none(),
        'ultimas_despesas_registradas': Despesa.objects.none(),
        'ultimas_manutencoes_por_ativo': [],
    }

    empresas_do_usuario = user.empresas_associadas.all()

    # Lógica unificada: todos os usuários só veem dados de suas empresas associadas.
    # Se não houver empresas associadas, o dashboard ficará vazio (ou exibirá mensagem).
    if not empresas_do_usuario.exists():
        messages.info(
            request, "Seu perfil não possui empresas associadas, portanto, o dashboard está vazio ou limitado.")
        return render(request, 'servico_campo/dashboard.html', context)

    # Base de QuerySets filtrada pelas empresas associadas ao usuário
    qs_base_os = OrdemServico.objects.filter(cliente__in=empresas_do_usuario)
    qs_base_despesas = Despesa.objects.filter(
        ordem_servico__cliente__in=empresas_do_usuario)
    equipamentos_qs = Equipamento.objects.filter(
        cliente__in=empresas_do_usuario)

    context['equipamentos_count'] = equipamentos_qs.count()

    # Preenchimento do contexto com base nos QuerySets filtrados
    if qs_base_os.exists():
        context['ordens_em_execucao_count'] = qs_base_os.filter(
            status='EM_EXECUCAO').count()
        context['os_pendentes_planejamento_count'] = qs_base_os.filter(
            status='AGUARDANDO_PLANEJAMENTO').count()
        mes_atual, ano_atual = timezone.now().month, timezone.now().year
        context['os_concluidas_mes_count'] = qs_base_os.filter(
            status='CONCLUIDA', data_fechamento__month=mes_atual, data_fechamento__year=ano_atual).count()

        status_data = qs_base_os.values('status').annotate(
            count=Count('status')).order_by('status')
        status_display_map, status_color_map = dict(OrdemServico.STATUS_CHOICES), {'CONCLUIDA': 'rgba(25, 135, 84, 0.7)', 'EM_EXECUCAO': 'rgba(255, 193, 7, 0.7)', 'PLANEJADA': 'rgba(13, 110, 253, 0.7)',
                                                                                   'AGUARDANDO_PLANEJAMENTO': 'rgba(108, 117, 125, 0.7)', 'CANCELADA': 'rgba(220, 53, 69, 0.7)', 'PENDENTE_APROVACAO': 'rgba(111, 66, 193, 0.7)'}
        context['status_labels'] = [status_display_map.get(
            item['status'], item['status']) for item in status_data]
        context['status_counts'] = [item['count'] for item in status_data]
        context['status_colors'] = [status_color_map.get(
            item['status'], '#CCCCCC') for item in status_data]

        # === NOVO BLOCO PARA TIPO DE MANUTENÇÃO (CORRIGIDO) ===
        # Query para pegar dados de tipo de manutenção. Exclui tipos nulos.
        tipo_data_raw = qs_base_os.filter(tipo_manutencao__isnull=False).values(
            'tipo_manutencao__nome'
        ).annotate(count=Count('tipo_manutencao')).order_by('tipo_manutencao__nome')

        # Mapeamento de cores para os tipos de manutenção (pode ser expandido ou lido de um modelo se você adicionar uma cor lá)
        tipo_color_map = {
            'Manutenção Corretiva': 'rgba(214, 40, 40, 0.7)',
            'Manutenção Preventiva': 'rgba(60, 179, 113, 0.7)',
            'Inspeção': 'rgba(255, 165, 0, 0.7)',
            'Outro': 'rgba(173, 216, 230, 0.7)'
        }

        context['tipo_labels'] = [item['tipo_manutencao__nome']
                                  for item in tipo_data_raw]
        context['tipo_counts'] = [item['count'] for item in tipo_data_raw]
        context['tipo_colors'] = [tipo_color_map.get(
            item['tipo_manutencao__nome'], '#CCCCCC') for item in tipo_data_raw]
        # === FIM DO BLOCO PARA TIPO DE MANUTENÇÃO ===

        context['ultimas_os_concluidas'] = qs_base_os.filter(
            status='CONCLUIDA').order_by('-data_fechamento')[:5]
        # Minhas OSs planejadas devem ser as que o usuário logado é técnico responsável, E estão nas empresas associadas.
        context['minhas_os_planejadas'] = qs_base_os.filter(
            tecnico_responsavel=user, status='PLANEJADA').order_by('data_previsao_conclusao')

        ultimas_manutencoes = []
        for equipamento in equipamentos_qs:  # equipamentos_qs já está filtrado
            ultima_os = qs_base_os.filter(  # qs_base_os já está filtrado
                equipamento=equipamento, status='CONCLUIDA').order_by('-data_fechamento').first()
            ultimas_manutencoes.append(
                {'equipamento': equipamento, 'ultima_os': ultima_os})
        context['ultimas_manutencoes_por_ativo'] = ultimas_manutencoes

    if qs_base_despesas.exists():
        # ALTERADO: Filtrar por status_aprovacao='PENDENTE'
        context['despesas_pendentes_count'] = qs_base_despesas.filter(
            status_aprovacao='PENDENTE').count()  # MUDANÇA AQUI
        context['custo_total_reembolso'] = qs_base_despesas.aggregate(total=Sum('valor'))[
            'total'] or 0.00
        context['ultimas_despesas_registradas'] = qs_base_despesas.filter(
            tecnico=user).order_by('-data_despesa')[:5]

    return render(request, 'servico_campo/dashboard.html', context)


@login_required
def perfil_view(request):
    return render(request, 'servico_campo/perfil.html')


def load_equipamentos(request):
    cliente_id = request.GET.get('cliente_id')
    equipamentos = Equipamento.objects.filter(
        cliente_id=cliente_id).order_by('nome')
    return JsonResponse(list(equipamentos.values('id', 'nome', 'modelo')), safe=False)


# @login_required
# @permission_required('servico_campo.change_despesa', raise_exception=True)
# @require_POST
# def aprovar_despesa(request, pk):
#     despesa = get_object_or_404(Despesa, pk=pk)
#     despesa.aprovada = True
#     despesa.aprovado_por = request.user
#     despesa.data_aprovacao = timezone.now()
#     despesa.save()
#     messages.success(
#         request, f"Despesa de {despesa.descricao} aprovada com sucesso.")
#     return redirect('servico_campo:lista_despesas_pendentes')


# @login_required
# # Assumindo permissão de exclusão para rejeitar
# @permission_required('servico_campo.delete_despesa', raise_exception=True)
# @require_POST
# def rejeitar_despesa(request, pk):
#     despesa = get_object_or_404(Despesa, pk=pk)
#     descricao_despesa = despesa.descricao
#     despesa.delete()
#     messages.warning(
#         request, f"Despesa de {descricao_despesa} foi rejeitada e removida.")
#     return redirect('servico_campo:lista_despesas_pendentes')

# NOVO FORMULÁRIO (TEMPORÁRIO, NÃO NO forms.py) para lidar com o comentário
class ComentarioAprovacaoForm(forms.Form):
    comentario = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 3, 'class': 'form-control'}), required=False, label=_("Comentário"))


# NOVA VIEW: Para lidar com a aprovação/rejeição de despesas
class DespesaAprovarRejeitarView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_despesa'
    model = Despesa
    template_name = 'servico_campo/despesa_confirm_acao.html'
    form_class = ComentarioAprovacaoForm

    # Remova completamente o método get_form (ou qualquer super().get_form_class() se tiver)
    # ou sobrescreva-o para não passar 'instance'.
    # A maneira mais fácil é remover o form_class e instanciar o formulário manualmente no post e get.

    def get(self, request, *args, **kwargs):
        # Para GET, precisamos instanciar o formulário de comentário
        self.object = self.get_object()  # Obtém a instância da despesa
        form = self.form_class(
            initial={'comentario': self.object.comentario_aprovacao})
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # Obtém a instância da despesa
        # Instancia o formulário COM os dados do POST
        form = self.form_class(request.POST)

        acao = self.kwargs.get('acao')  # 'aprovar' ou 'rejeitar'

        if acao == 'rejeitar':
            # Comentário obrigatório na rejeição
            form.fields['comentario'].required = True

        if form.is_valid():
            comentario = form.cleaned_data.get('comentario', '')

            if acao == 'aprovar':
                self.object.status_aprovacao = 'APROVADA'
                messages.success(
                    request, _(f"Despesa de {self.object.descricao} aprovada com sucesso."))

                # NOVO: Lógica para criar entrada em ContaPagar
                ContaPagar.objects.get_or_create(
                    despesa=self.object,
                    defaults={
                        'status_pagamento': 'PENDENTE',
                        # Opcional: registrar quem aprovou como responsável inicial pelo pagamento
                        'responsavel_pagamento': request.user
                    }
                )

            elif acao == 'rejeitar':
                self.object.status_aprovacao = 'REJEITADA'
                messages.warning(
                    request, _(f"Despesa de {self.object.descricao} rejeitada."))

                # Se a despesa for rejeitada, certifique-se de que não haja um ContaPagar associado
                # ou que ele seja marcado como 'CANCELADO' ou excluído (dependendo da regra de negócio)
                # Para manter o histórico, vamos marcar o ContaPagar existente como 'CANCELADO'
                # se por acaso já existia (ex: foi aprovada e depois rejeitada)
                if hasattr(self.object, 'conta_a_pagar'):
                    conta_existente = self.object.conta_a_pagar
                    if conta_existente.status_pagamento != 'CANCELADO':
                        conta_existente.status_pagamento = 'CANCELADO'
                        conta_existente.comentario = _(
                            "Pagamento cancelado devido à rejeição da despesa.")
                        conta_existente.responsavel_pagamento = request.user
                        conta_existente.save()

            self.object.aprovado_por = request.user
            self.object.data_aprovacao = timezone.now()
            self.object.comentario_aprovacao = comentario
            self.object.save()  # Salva a instância da Despesa (self.object)

            return redirect('servico_campo:lista_despesas_pendentes')
        else:
            messages.error(
                request, _("Erro na validação do comentário: ") + str(form.errors.as_text()))
            return self.render_to_response(self.get_context_data(object=self.object, form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        despesa = self.get_object()  # Ou self.object, que já foi definido no get/post
        context['despesa'] = despesa
        context['acao'] = self.kwargs.get('acao')

        context['comentario_obrigatorio'] = (context['acao'] == 'rejeitar')

        if context['acao'] == 'aprovar':
            context['form_title'] = _("Aprovar Despesa")
        elif context['acao'] == 'rejeitar':
            context['form_title'] = _("Rejeitar Despesa")
        else:
            raise ImproperlyConfigured(
                "Ação inválida para DespesaAprovarRejeitarView.")

        return context

    # Embora não seja mais uma UpdateView pura, mantenha para compatibilidade
    def get_success_url(self):
        return reverse_lazy('servico_campo:lista_despesas_pendentes')


def relatorio_campo_pdf_view(request, pk):
    relatorio = get_object_or_404(RelatorioCampo, pk=pk)
    template = get_template('servico_campo/relatorio_pdf_template.html')
    html = template.render({'relatorio': relatorio})
    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)
    if not pdf.err:
        response = HttpResponse(
            result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_os_{relatorio.ordem_servico.numero_os}.pdf"'
        return response
    return HttpResponse("Erro ao gerar PDF: %s" % pdf.err, status=400)


def check_open_point_api(request, os_pk):
    if request.user.is_authenticated:
        ponto_aberto = RegistroPonto.objects.filter(
            tecnico=request.user, ordem_servico__pk=os_pk, hora_saida__isnull=True).exists()
        return JsonResponse({'has_open_point': ponto_aberto})
    return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

# (Você pode criar um GestorFinanceiroRequiredMixin se tiver um grupo específico para isso)


class ContaPagarListView(LoginRequiredMixin, ListView):  # Ou LoginRequiredMixin
    permission_required = 'servico_campo.view_contapagar'
    model = ContaPagar
    template_name = 'servico_campo/contas_a_pagar_list.html'
    context_object_name = 'contas_a_pagar'
    paginate_by = 10

    def get_queryset(self):
        # Apenas despesas APROVADAS que ainda não estão PAGAS ou CANCELADAS
        # Ou todas as contas, se você quiser histórico
        # Para a tela de contas a pagar, geralmente queremos as PENDENTES, EM_ANALISE

        qs = ContaPagar.objects.filter(
            status_pagamento__in=['PENDENTE', 'EM_ANALISE']
        ).select_related('despesa', 'despesa__ordem_servico', 'despesa__tecnico', 'responsavel_pagamento')

        # Filtros (opcional, pode adicionar depois)
        status_filter = self.request.GET.get('status_pagamento')
        if status_filter and status_filter != 'TODOS':
            qs = qs.filter(status_pagamento=status_filter)

        return qs.order_by('status_pagamento', 'despesa__data_despesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Gestão de Contas a Pagar")
        context['status_pagamento_choices'] = ContaPagar.STATUS_PAGAMENTO_CHOICES
        context['filters'] = {
            'status_pagamento': self.request.GET.get('status_pagamento', ''),
        }

        # NOVO: Obtém a política de despesa ativa
        context['politica_despesa_ativa'] = PoliticaDespesa.objects.filter(
            ativa=True).first()

        return context


class ContaPagarUpdateView(GestorRequiredMixin, UpdateView):  # Ou LoginRequiredMixin
    permission_required = 'servico_campo.change_contapagar'
    model = ContaPagar
    form_class = ContaPagarForm
    template_name = 'servico_campo/conta_a_pagar_form.html'
    context_object_name = 'conta_a_pagar'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Atualizar Status de Pagamento")
        return context

    def form_valid(self, form):
        # Atribui o usuário logado como responsável pelo pagamento
        form.instance.responsavel_pagamento = self.request.user
        messages.success(self.request, _(
            "Status de pagamento atualizado com sucesso!"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('servico_campo:lista_contas_a_pagar')


# -------------------------------------------------------------
# Views de Fluxo (OS e objetos relacionados)
# -------------------------------------------------------------

# <-- ADICIONADO PermissionRequiredMixin
class OrdemServicoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = OrdemServico
    template_name = 'servico_campo/ordem_servico_list.html'
    context_object_name = 'ordens_servico'
    paginate_by = 10
    # <-- Permissão necessária para visualizar a lista de OS
    permission_required = 'servico_campo.view_ordemservico'

    def get_template_names(self):
        return [self.template_name]

    def get_queryset(self):
        user = self.request.user
        empresas_do_usuario = user.empresas_associadas.all()

        if not empresas_do_usuario.exists():
            # Opcional: Você pode adicionar uma mensagem aqui se quiser avisar o usuário.
            messages.info(
                self.request, "Seu perfil não está associado a nenhuma empresa. Nenhuma Ordem de Serviço será exibida.")
            return OrdemServico.objects.none()

        base_qs = OrdemServico.objects.filter(
            cliente__in=empresas_do_usuario
        )

        # Coleta os parâmetros de filtro
        filters = {
            'numero_os': self.request.GET.get('numero_os'),
            'cliente': self.request.GET.get('cliente'),
            'equipamento': self.request.GET.get('equipamento'),
            'titulo_servico': self.request.GET.get('titulo_servico'),
            'tecnico_nome': self.request.GET.get('tecnico_nome'),
            'data_abertura': self.request.GET.get('data_abertura'),
            'status': self.request.GET.get('status'),
        }

        # Aplica os filtros
        if filters['numero_os']:
            base_qs = base_qs.filter(numero_os__icontains=filters['numero_os'])
        if filters['cliente']:
            base_qs = base_qs.filter(
                cliente__razao_social__icontains=filters['cliente'])
        if filters['equipamento']:
            base_qs = base_qs.filter(
                Q(equipamento__nome__icontains=filters['equipamento']) |
                Q(equipamento__modelo__icontains=filters['equipamento'])
            )
        if filters['titulo_servico']:
            base_qs = base_qs.filter(
                titulo_servico__icontains=filters['titulo_servico'])

        if filters['tecnico_nome']:
            base_qs = base_qs.filter(
                Q(tecnico_responsavel__first_name__icontains=filters['tecnico_nome']) |
                Q(tecnico_responsavel__last_name__icontains=filters['tecnico_nome']) |
                Q(tecnico_responsavel__username__icontains=filters['tecnico_nome'])
            )
        if filters['data_abertura']:
            try:
                from datetime import datetime  # Já deve estar importado no início do arquivo
                data_abertura_obj = datetime.strptime(
                    filters['data_abertura'], '%Y-%m-%d').date()
                base_qs = base_qs.filter(data_abertura__date=data_abertura_obj)
            except ValueError:
                pass

        if filters['status']:
            base_qs = base_qs.filter(status=filters['status'])

        return base_qs.select_related('cliente', 'equipamento', 'tecnico_responsavel').order_by('-data_abertura')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Passa os valores dos filtros para o template manter o estado (AGORA COM OS NOVOS CAMPOS)
        context['filters'] = {
            'numero_os': self.request.GET.get('numero_os', ''),
            'cliente': self.request.GET.get('cliente', ''),
            'equipamento': self.request.GET.get('equipamento', ''),  # NOVO
            # NOVO
            'titulo_servico': self.request.GET.get('titulo_servico', ''),
            'tecnico_nome': self.request.GET.get('tecnico_nome', ''),
            'data_abertura': self.request.GET.get('data_abertura', ''),
            'status': self.request.GET.get('status', ''),
        }

        context['status_choices'] = OrdemServico.STATUS_CHOICES
        return context


class OrdemServicoDetailView(LoginRequiredMixin, DetailView):
    model = OrdemServico
    template_name = 'servico_campo/ordem_servico_detail.html'
    context_object_name = 'os'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        os = self.get_object()

        is_team_member = False
        if self.request.user == os.tecnico_responsavel:
            is_team_member = True
        else:
            if os.equipe.filter(usuario=self.request.user).exists():
                is_team_member = True

        context['is_team_member'] = is_team_member

        context['ponto_aberto'] = os.registros_ponto.filter(
            tecnico=self.request.user, hora_saida__isnull=True).first()

        # Coleta todos os problemas identificados de todos os relatórios desta OS
        # NOVO BLOCO
        problemas_detalhados = []
        for relatorio in os.relatorios_campo.all():
            for problema in relatorio.problemas_identificados_detalhes.all().select_related('categoria', 'subcategoria'):
                problemas_detalhados.append({
                    'categoria': problema.categoria.nome,
                    'subcategoria': problema.subcategoria.nome if problema.subcategoria else '',
                    'observacao': problema.observacao,
                })
        context['problemas_detalhados_os'] = problemas_detalhados
        # FIM DO NOVO BLOCO

        tem_responsavel = os.tecnico_responsavel is not None
        tem_relatorio = os.relatorios_campo.exists()
        # Esta variável verifica SE EXISTE algum ponto, não a quantidade
        tem_ponto = os.registros_ponto.exists()
        context['pode_concluir'] = tem_responsavel and tem_relatorio and tem_ponto

        context['os_tipo_manutencao_display'] = os.tipo_manutencao.nome

        # === ADICIONE ESTA LINHA PARA PASSAR TODOS OS REGISTROS DE PONTO PARA O TEMPLATE ===
        context['registros_ponto'] = os.registros_ponto.all().order_by(
            'data', 'hora_entrada')

        context['documentos_os'] = os.documentos.all()
        context['relatorios_campo'] = os.relatorios_campo.all()

        # Você já tinha esta linha:
        context['registros_ponto'] = os.registros_ponto.all().order_by(
            'data', 'hora_entrada')

        # Status choices para o dropdown de mudança de status
        # Aqui, você precisa definir quais status são disponíveis para mudança
        context['status_choices_disponiveis'] = [
            ('PLANEJADA', _('Planejada')),
            ('AGUARDANDO_PLANEJAMENTO', _('Aguardando Planejamento')),
            ('EM_EXECUCAO', _('Em Execução')),
            ('CONCLUIDA', _('Concluída')),
            ('CANCELADA', _('Cancelada')),
            ('PENDENTE_APROVACAO', _('Pendente de Aprovação'))
        ]

        return context


class DocumentoOSCreateView(LoginRequiredMixin, CreateView):
    model = DocumentoOS
    form_class = DocumentoOSForm
    template_name = 'servico_campo/documento_os_form.html'

    def form_valid(self, form):
        os = get_object_or_404(OrdemServico, pk=self.kwargs.get('os_pk'))
        form.instance.ordem_servico = os
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, _(
            f'Documento "{form.instance.titulo}" anexado com sucesso.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.kwargs.get('os_pk')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = get_object_or_404(
            OrdemServico, pk=self.kwargs.get('os_pk'))
        return context


# Use GestorRequiredMixin para permissão
class OrdemServicoDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_ordemservico'  # Permissão necessária
    model = OrdemServico
    template_name = 'servico_campo/ordem_servico_confirm_delete.html'
    # Redireciona para a lista de OSs após exclusão
    success_url = reverse_lazy('servico_campo:lista_os')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = self.get_object()  # Passa o objeto OS para o template
        return context

    def post(self, request, *args, **kwargs):
        try:
            # Tenta excluir o objeto
            response = super().post(request, *args, **kwargs)
            messages.success(request, _(
                f"Ordem de Serviço {self.object.numero_os} excluída com sucesso."))
            return response
        except models.ProtectedError:  # Importe models do django.db para isso
            # Se houver objetos relacionados que impedem a exclusão (ex: Registros de Ponto, Relatórios, Despesas)
            messages.error(request, _(
                "Não foi possível excluir esta Ordem de Serviço. Há registros de Ponto, Relatórios ou Despesas associados a ela."))
            # Redireciona de volta para a página de confirmação para mostrar a mensagem de erro
            return self.get(request, *args, **kwargs)


class RegistroPontoCreateView(LoginRequiredMixin, CreateView):
    model = RegistroPonto
    form_class = RegistroPontoEntradaForm  # AGORA USA O NOVO FORMULÁRIO

    def post(self, request, *args, **kwargs):
        os = get_object_or_404(OrdemServico, pk=self.kwargs.get('os_pk'))

        if RegistroPonto.objects.filter(tecnico=request.user, ordem_servico=os, hora_saida__isnull=True).exists():
            messages.error(request, _(
                'Você já possui um ponto em aberto para esta OS.'))
        else:
            form = self.get_form()  # form agora é RegistroPontoEntradaForm
            if form.is_valid():
                # form.cleaned_data['localizacao'] e ['observacoes'] já estão aqui
                ponto = form.save(commit=False)

                ponto.ordem_servico = os
                ponto.tecnico = request.user
                ponto.data = timezone.localdate()
                ponto.hora_entrada = timezone.localtime().time()

                # NOVO: Lógica para data_inicio_real e status da OS
                if not os.registros_ponto.exists() and os.data_inicio_real is None:
                    os.data_inicio_real = timezone.now()
                    if os.status in ['AGUARDANDO_PLANEJAMENTO', 'PLANEJADA', 'PENDENTE_APROVACAO']:
                        os.status = 'EM_EXECUCAO'
                    os.save(update_fields=['data_inicio_real', 'status'])

                ponto.observacoes_entrada = form.cleaned_data.get(
                    'observacoes_entrada')  # NOVO CAMPO

                # A lógica de localização já é tratada pelo RegistroPontoEntradaForm
                # e o nome do campo no POST é 'localizacao' para o campo de formulário 'localizacao'
                gps_coords = form.cleaned_data.get(
                    'gps_coords')  # Pega do cleaned_data
                manual_location = form.cleaned_data.get(
                    'localizacao')  # Pega do cleaned_data

                if manual_location:
                    ponto.localizacao = manual_location
                elif gps_coords and gps_coords not in ['PERMISSION_DENIED', 'POSITION_UNAVAILABLE', 'TIMEOUT', 'NOT_SUPPORTED'] and not gps_coords.startswith('ERROR:'):
                    ponto.localizacao = f"GPS: {gps_coords}"
                else:
                    ponto.localizacao = _(
                        "Localização não informada/disponível")

                ponto.save()
                messages.success(request, _(
                    'Ponto de entrada marcado com sucesso.'))
            else:
                messages.error(request, _(
                    f"Erro ao marcar ponto: {form.errors}"))
        return redirect('servico_campo:detalhe_os', pk=os.pk)


class RegistroPontoEncerramentoView(LoginRequiredMixin, UpdateView):
    model = RegistroPonto
    form_class = RegistroPontoSaidaForm  # AGORA USA O NOVO FORMULÁRIO
    # Mantém o template genérico, mas pode ser um específico para saída se preferir.
    template_name = 'servico_campo/registro_ponto_form_edit.html'
    # Na verdade, esta view é chamada pelo JS do modal, então não renderiza um template HTML direto.

    def get_object(self, queryset=None):
        return get_object_or_404(RegistroPonto, pk=self.kwargs.get('pk'), tecnico=self.request.user, hora_saida__isnull=True)

    # Não precisamos de get_context_data aqui, pois esta view é apenas para processamento POST do modal.

    def post(self, request, *args, **kwargs):
        # A instância do ponto que está sendo encerrado
        current_ponto = self.get_object()

        # Cria o formulário com os dados do POST e a instância atual
        form = self.form_class(request.POST, instance=current_ponto)

        if form.is_valid():
            # Preenche hora_saida automaticamente na view
            current_ponto.hora_saida = timezone.localtime().time()

            # Pega os dados dos campos do formulário (cleaned_data)
            current_ponto.localizacao_saida = form.cleaned_data.get(
                'localizacao_saida')
            current_ponto.observacoes = form.cleaned_data.get('observacoes')
            gps_coords_saida = form.cleaned_data.get('gps_coords_saida')

            # Lógica de localização de saída, similar à de entrada
            if current_ponto.localizacao_saida:  # Já preenchido se veio do manual
                pass  # Nada a fazer, já está no current_ponto.localizacao_saida
            elif gps_coords_saida and gps_coords_saida not in ['PERMISSION_DENIED', 'POSITION_UNAVAILABLE', 'TIMEOUT', 'NOT_SUPPORTED'] and not gps_coords_saida.startswith('ERROR:'):
                current_ponto.localizacao_saida = f"GPS: {gps_coords_saida}"
            else:
                current_ponto.localizacao_saida = _(
                    "Localização de saída não informada/disponível")

            current_ponto.save()  # Salva o objeto atualizado
            messages.success(request, _(
                'Ponto de saída encerrado com sucesso.'))
        else:
            messages.error(request, _(
                f"Erro ao encerrar ponto: {form.errors}"))

        return redirect('servico_campo:detalhe_os', pk=current_ponto.ordem_servico.pk)


class RegistroPontoEditView(LoginRequiredMixin, UpdateView):
    model = RegistroPonto
    form_class = RegistroPontoForm  # Este continua usando o form completo para edição
    template_name = 'servico_campo/registro_ponto_form_edit.html'
    context_object_name = 'registro_ponto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = self.get_object().ordem_servico
        context['form_action_title'] = _("Editar Registro de Ponto")
        return context

    def form_valid(self, form):
        # Aqui, form.save() vai persistir os dados do formulário sem lógica extra
        messages.success(self.request, _(
            'Registro de ponto atualizado com sucesso!'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.ordem_servico.pk})


# A exclusão de ponto pode ser sensível, então restrita.
class RegistroPontoDeleteView(GestorRequiredMixin, DeleteView):
    # Permissão para excluir registro de ponto
    permission_required = 'servico_campo.delete_registroponto'
    model = RegistroPonto
    # Template a ser criado/verificado
    template_name = 'servico_campo/registro_ponto_confirm_delete.html'
    context_object_name = 'registro_ponto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passa a OS para o breadcrumb e para o template de confirmação
        context['os'] = self.get_object().ordem_servico
        return context

    def get_success_url(self):
        registro = self.get_object()  # Pega o objeto antes da exclusão para obter a OS
        messages.success(self.request, _(
            f"Registro de ponto de {registro.tecnico.get_full_name()} em {registro.data.strftime('%d/%m/%Y')} removido com sucesso."))
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': registro.ordem_servico.pk})

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, _(
                "Não foi possível excluir este registro de ponto. Há registros relacionados que o impedem."))
            return self.get(request, *args, **kwargs)


class RegistroPontoDetailView(LoginRequiredMixin, DetailView):
    model = RegistroPonto
    template_name = 'servico_campo/registro_ponto_detail.html'  # Criaremos este template
    context_object_name = 'registro_ponto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passa a OS para o breadcrumb
        context['os'] = self.get_object().ordem_servico
        return context


class RelatorioCampoCreateView(LoginRequiredMixin, CreateView):
    model = RelatorioCampo
    form_class = RelatorioCampoForm
    template_name = 'servico_campo/relatorio_campo_form.html'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.ordem_servico.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = get_object_or_404(
            OrdemServico, pk=self.kwargs.get('os_pk'))
        context['form_action_title'] = 'Preencher Novo Relatório'
        # NOVO: Adiciona o formset vazio ao contexto
        if self.request.POST:
            context['problema_formset'] = ProblemaRelatorioFormSet(
                self.request.POST, self.request.FILES)
        else:
            context['problema_formset'] = ProblemaRelatorioFormSet()
        return context

    def form_valid(self, form):
        # A instância do RelatorioCampo ainda não foi salva no banco
        form.instance.ordem_servico = get_object_or_404(
            OrdemServico, pk=self.kwargs.get('os_pk'))
        # Garante que o técnico é o usuário logado
        form.instance.tecnico = self.request.user

        context = self.get_context_data()
        problema_formset = context['problema_formset']

        if form.is_valid() and problema_formset.is_valid():
            self.object = form.save()  # Salva o RelatorioCampo
            # Associa o formset ao RelatorioCampo salvo
            problema_formset.instance = self.object
            problema_formset.save()  # Salva os ProblemaRelatorio

            messages.success(self.request, _(
                f'Relatório de Campo para OS {self.object.ordem_servico.numero_os} salvo com sucesso!'))
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, _(
                "Ocorreram erros na validação do formulário ou dos problemas identificados."))
            # Se o formulário principal for inválido, renderiza-o novamente com os erros
            # Passa o form principal com erros de volta
            return self.render_to_response(self.get_context_data(form=form))


class RelatorioCampoUpdateView(LoginRequiredMixin, UpdateView):
    model = RelatorioCampo
    form_class = RelatorioCampoForm
    template_name = 'servico_campo/relatorio_campo_form.html'

    def get_queryset(self):
        # Opcional: Filtrar para que o usuário só possa editar seus próprios relatórios
        return super().get_queryset().filter(tecnico=self.request.user)

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.ordem_servico.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = self.get_object().ordem_servico
        context['form_action_title'] = 'Editar Relatório'
        # NOVO: Adiciona o formset com instâncias existentes ou vazio
        if self.request.POST:
            context['problema_formset'] = ProblemaRelatorioFormSet(
                self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['problema_formset'] = ProblemaRelatorioFormSet(
                instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        problema_formset = context['problema_formset']

        if form.is_valid() and problema_formset.is_valid():
            self.object = form.save()  # Salva o RelatorioCampo
            # Garante que o formset esteja associado à instância correta
            problema_formset.instance = self.object
            problema_formset.save()  # Salva os ProblemaRelatorio (cria, atualiza, deleta)

            messages.success(self.request, _(
                f'Relatório de Campo para OS {self.object.ordem_servico.numero_os} atualizado com sucesso!'))
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, _(
                "Ocorreram erros na validação do formulário ou dos problemas identificados."))
            # Se o formulário principal for inválido, renderiza-o novamente com os erros
            return self.render_to_response(self.get_context_data(form=form))


class FotoRelatorioCreateView(LoginRequiredMixin, CreateView):
    model = FotoRelatorio
    form_class = FotoRelatorioForm
    template_name = 'servico_campo/foto_relatorio_form.html'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.relatorio.ordem_servico.pk})

    def form_valid(self, form):
        relatorio = get_object_or_404(
            RelatorioCampo, pk=self.kwargs.get('relatorio_pk'))
        form.instance.relatorio = relatorio
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['relatorio'] = get_object_or_404(
            RelatorioCampo, pk=self.kwargs.get('relatorio_pk'))
        context['os'] = context['relatorio'].ordem_servico
        return context


class DespesaCreateView(LoginRequiredMixin, CreateView):
    model = Despesa
    form_class = DespesaForm
    template_name = 'servico_campo/despesa_form.html'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.kwargs.get('os_pk')})

    def form_valid(self, form):
        os = get_object_or_404(OrdemServico, pk=self.kwargs.get('os_pk'))
        form.instance.ordem_servico = os
        form.instance.tecnico = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = get_object_or_404(
            OrdemServico, pk=self.kwargs.get('os_pk'))
        return context
# NOVO: DespesaUpdateView


class DespesaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Despesa
    form_class = DespesaForm
    template_name = 'servico_campo/despesa_form.html'
    permission_required = 'servico_campo.change_despesa'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.ordem_servico.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action_title'] = _("Editar Despesa")
        context['os'] = self.object.ordem_servico  # Para o breadcrumb e título
        return context

    def form_valid(self, form):
        # Obtém a instância da despesa antes de salvar o formulário
        despesa_antiga = self.get_object()

        # Verifica se o status atual não é PENDENTE e se houve alguma alteração relevante
        # Consideramos "relevante" qualquer alteração, pois qualquer mudança pode exigir nova aprovação.
        # Se você quiser ser mais específico (ex: só se mudar valor ou descrição), a lógica seria mais complexa.

        # Salva o formulário (isso atualiza a instância self.object com os novos dados)
        response = super().form_valid(form)

        # Após salvar, self.object já contém os dados atualizados
        # Agora, verificamos o status ANTERIOR e o status ATUAL (que ainda seria o antigo se não mudamos)
        # Se o status ANTERIOR não era PENDENTE, ele deve voltar a ser PENDENTE.
        if despesa_antiga.status_aprovacao != 'PENDENTE':
            self.object.status_aprovacao = 'PENDENTE'
            self.object.aprovado_por = None
            self.object.data_aprovacao = None
            # Limpa o comentário de aprovação anterior
            self.object.comentario_aprovacao = None
            self.object.save()  # Salva novamente para atualizar o status e limpar os campos

            messages.info(self.request, _(
                "Despesa editada e status de aprovação resetado para 'Pendente' para nova avaliação."))
        else:
            messages.success(self.request, _(
                "Despesa atualizada com sucesso."))

        return response

# NOVO: DespesaDeleteView


class DespesaDetailView(LoginRequiredMixin, DetailView):
    model = Despesa
    template_name = 'servico_campo/despesa_detail.html'  # Novo template a ser criado
    context_object_name = 'despesa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passa a OS para o breadcrumb e para o template
        context['os'] = self.get_object().ordem_servico

        # Tenta obter a ContaPagar associada, se existir
        try:
            context['conta_a_pagar'] = self.get_object().conta_a_pagar
        except Despesa.conta_a_pagar.RelatedObjectDoesNotExist:
            context['conta_a_pagar'] = None

        return context


# Geralmente a exclusão é restrita a gestores
class DespesaDeleteView(GestorRequiredMixin, DeleteView):
    # Permissão para excluir despesa
    permission_required = 'servico_campo.delete_despesa'
    model = Despesa
    # Template a ser criado/verificado
    template_name = 'servico_campo/despesa_confirm_delete.html'
    context_object_name = 'despesa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passa a OS para o breadcrumb e para o template de confirmação
        context['os'] = self.get_object().ordem_servico
        return context

    def get_success_url(self):
        despesa = self.get_object()  # Pega o objeto antes da exclusão para obter a OS
        messages.success(self.request, _(
            f"Despesa de {despesa.descricao} removida com sucesso."))
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': despesa.ordem_servico.pk})

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, _(
                "Não foi possível excluir esta despesa. Há registros relacionados que a impedem."))
            return self.get(request, *args, **kwargs)


class DespesaPendenteListView(GestorRequiredMixin, ListView):
    permission_required = 'servico_campo.change_despesa'
    model = Despesa
    template_name = 'servico_campo/despesa_pendente_list.html'
    context_object_name = 'despesas_pendentes'

    def get_queryset(self):
        return Despesa.objects.filter(status_aprovacao='PENDENTE').order_by('-data_despesa')


class OrdemServicoCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'servico_campo.add_ordemservico'
    model = OrdemServico
    form_class = OrdemServicoCreateForm  # <-- MUDANÇA AQUI
    template_name = 'servico_campo/ordem_servico_form.html'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Abrir Nova Ordem de Serviço'
        return context


class OrdemServicoUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_ordemservico'
    model = OrdemServico
    # Aponte para o novo formulário de edição
    form_class = OrdemServicoUpdateForm
    # Reutilize o template de formulário genérico
    template_name = 'servico_campo/ordem_servico_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Define um título dinâmico para a página
        context['form_title'] = f"Editar Ordem de Serviço - {self.object.numero_os}"
        return context

    def get_success_url(self):
        # Após salvar, volta para a tela de detalhes da OS
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.pk})


class OrdemServicoEncerramentoView(LoginRequiredMixin, UpdateView):
    model = OrdemServico
    form_class = EncerramentoOSForm
    template_name = 'servico_campo/ordem_servico_encerramento.html'
    context_object_name = 'os'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        os_instance = form.save(commit=False)
        os_instance.status = 'CONCLUIDA'
        os_instance.data_fechamento = timezone.now()
        os_instance.save()
        messages.success(self.request, _(
            f"Ordem de Serviço {os_instance.numero_os} encerrada com sucesso!"))
        return HttpResponseRedirect(self.get_success_url())


class ClienteListView(GestorRequiredMixin, ListView):
    permission_required = 'servico_campo.view_cliente'
    model = Cliente
    template_name = 'servico_campo/gestao/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10


class ClienteDetailView(GestorRequiredMixin, DetailView):
    permission_required = 'servico_campo.view_cliente'
    model = Cliente
    template_name = 'servico_campo/gestao/cliente_detail.html'
    context_object_name = 'cliente'


class ClienteCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'servico_campo.add_cliente'
    model = Cliente
    form_class = ClienteForm
    template_name = 'servico_campo/gestao/cliente_form.html'
    success_url = reverse_lazy('servico_campo:lista_clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Adicionar Novo Cliente'
        return context


class ClienteUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_cliente'
    model = Cliente
    form_class = ClienteForm
    template_name = 'servico_campo/gestao/cliente_form.html'
    success_url = reverse_lazy('servico_campo:lista_clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Cliente'
        return context


class ClienteDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_cliente'
    model = Cliente
    template_name = 'servico_campo/gestao/cliente_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_clientes')


class EquipamentoListView(GestorRequiredMixin, ListView):
    permission_required = 'servico_campo.view_equipamento'
    model = Equipamento
    template_name = 'servico_campo/gestao/equipamento_list.html'
    context_object_name = 'equipamentos'
    paginate_by = 10


class EquipamentoCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'servico_campo.add_equipamento'
    model = Equipamento
    form_class = EquipamentoForm
    template_name = 'servico_campo/gestao/equipamento_form.html'
    success_url = reverse_lazy('servico_campo:lista_equipamentos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Adicionar Novo Equipamento'
        return context


class EquipamentoUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_equipamento'
    model = Equipamento
    form_class = EquipamentoForm
    template_name = 'servico_campo/gestao/equipamento_form.html'
    success_url = reverse_lazy('servico_campo:lista_equipamentos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Equipamento'
        return context


class EquipamentoDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_equipamento'
    model = Equipamento
    template_name = 'servico_campo/gestao/equipamento_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_equipamentos')


class UserListView(GestorRequiredMixin, ListView):
    permission_required = 'auth.view_user'
    model = User
    template_name = 'servico_campo/gestao/user_list.html'
    context_object_name = 'usuarios'
    queryset = User.objects.all().order_by('username')


class UserCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'auth.add_user'
    form_class = UserCreationFormCustom
    template_name = 'servico_campo/gestao/user_form.html'
    success_url = reverse_lazy('servico_campo:lista_usuarios')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Adicionar Novo Usuário'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # REMOVER ESTE BLOCO, POIS O FORM.SAVE() JÁ LIDA COM ISSO AGORA
        # group = form.cleaned_data.get('groups')
        # if group:
        #    self.object.groups.add(group)
        return response


class UserUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'auth.change_user'
    model = User
    form_class = UserUpdateFormCustom
    template_name = 'servico_campo/gestao/user_form.html'
    success_url = reverse_lazy('servico_campo:lista_usuarios')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Usuário'
        return context


class GroupListView(GestorRequiredMixin, ListView):
    permission_required = 'auth.view_group'
    model = Group
    template_name = 'servico_campo/gestao/group_list.html'
    context_object_name = 'grupos'
    queryset = Group.objects.all().order_by('name')


class GroupCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'auth.add_group'
    model = Group
    form_class = GroupForm
    template_name = 'servico_campo/gestao/group_form.html'
    success_url = reverse_lazy('servico_campo:lista_grupos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Criar Novo Grupo'
        # Adiciona as permissões organizadas ao contexto
        context['permissoes_organizadas'] = organizar_permissoes()
        return context


class GroupUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'auth.change_group'
    model = Group
    form_class = GroupForm
    template_name = 'servico_campo/gestao/group_form.html'
    success_url = reverse_lazy('servico_campo:lista_grupos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Grupo'
        # Adiciona as permissões organizadas ao contexto
        context['permissoes_organizadas'] = organizar_permissoes()
        return context


class GroupDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'auth.delete_group'
    model = Group
    template_name = 'servico_campo/gestao/group_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_grupos')


@login_required
@require_POST
@permission_required('servico_campo.change_ordemservico', raise_exception=True)
def mudar_status_os(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)
    novo_status = request.POST.get('novo_status')

    status_validos = [choice[0] for choice in OrdemServico.STATUS_CHOICES]

    if novo_status in status_validos:
        os.status = novo_status
        os.save(update_fields=['status'])
        messages.success(
            request, f"O status da OS {os.numero_os} foi alterado para '{os.get_status_display()}'.")
    else:
        messages.error(request, "Status inválido.")

    return redirect('servico_campo:detalhe_os', pk=os.pk)


class DocumentoOSDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_documentoos'
    model = DocumentoOS
    template_name = 'servico_campo/gestao/documento_os_confirm_delete.html'

    def get_success_url(self):
        # Após deletar, volta para a página de detalhes da OS a que o doc pertencia
        documento = self.get_object()
        messages.success(
            self.request, f"Documento '{documento.titulo}' removido com sucesso.")
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': documento.ordem_servico.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = self.get_object().ordem_servico
        return context


class OrdemServicoClienteCreateView(LoginRequiredMixin, CreateView):
    model = OrdemServico
    form_class = OrdemServicoClienteForm
    template_name = 'servico_campo/ordem_servico_form.html'  # Reutilizamos o template

    def form_valid(self, form):
        # Define o status inicial como 'Aguardando Planejamento'
        form.instance.status = 'AGUARDANDO_PLANEJAMENTO'
        messages.success(
            self.request, "Chamado aberto com sucesso! Nossa equipe fará o planejamento em breve.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Abrir Novo Chamado de Serviço'
        return context


class OrdemServicoPlanejamentoUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_ordemservico'
    model = OrdemServico
    form_class = OrdemServicoPlanejamentoForm  # <-- MUDANÇA AQUI
    template_name = 'servico_campo/ordem_servico_planejamento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = MembroEquipeFormSet(
                self.request.POST, instance=self.object)
        else:
            context['formset'] = MembroEquipeFormSet(instance=self.object)
        context['form_title'] = f"Planejar Atendimento - OS {self.object.numero_os}"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            # Define o status para 'Planejada'
            form.instance.status = 'PLANEJADA'
            self.object = form.save()

            formset.instance = self.object
            formset.save()

            messages.success(
                self.request, "Ordem de Serviço planejada e atribuída com sucesso!")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.pk})


class DocumentoOSDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_documentoos'
    model = DocumentoOS
    template_name = 'servico_campo/gestao/documento_os_confirm_delete.html'

    def get_success_url(self):
        # Após deletar, volta para a página de detalhes da OS a que o doc pertencia
        documento = self.get_object()
        messages.success(
            self.request, f"Documento '{documento.titulo}' removido com sucesso.")
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': documento.ordem_servico.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = self.get_object().ordem_servico
        return context


# <-- ADICIONADO PermissionRequiredMixin
class GanttChartView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = OrdemServico
    template_name = 'servico_campo/gantt_chart.html'
    context_object_name = 'ordens_servico_para_gantt'
    permission_required = 'servico_campo.view_ordemservico'

    def get_queryset(self):
        user = self.request.user
        empresas_do_usuario = user.empresas_associadas.all()

        if not empresas_do_usuario.exists():
            return OrdemServico.objects.none()

        qs = OrdemServico.objects.filter(
            cliente__in=empresas_do_usuario,
            tecnico_responsavel__isnull=False
        )

        qs = qs.select_related('tecnico_responsavel', 'cliente', 'equipamento')
        return qs.order_by('tecnico_responsavel__first_name', 'data_abertura')


class GanttDataJsonView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'servico_campo.view_ordemservico'

    def get_queryset(self):
        user = self.request.user
        empresas_do_usuario = user.empresas_associadas.all()

        if not empresas_do_usuario.exists():
            return OrdemServico.objects.none()

        hoje = timezone.localdate()
        # Período padrão se nenhum filtro for fornecido (ex: último mês)
        default_start_date = hoje - timedelta(days=30)
        default_end_date = hoje + timedelta(days=7)  # Até uma semana no futuro

        # --- NOVO: Receber filtros de data da requisição GET ---
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        # Converter strings para objetos date
        try:
            filter_start_date = datetime.strptime(
                start_date_str, '%Y-%m-%d').date() if start_date_str else default_start_date
        except ValueError:
            filter_start_date = default_start_date

        try:
            filter_end_date = datetime.strptime(
                end_date_str, '%Y-%m-%d').date() if end_date_str else default_end_date
        except ValueError:
            filter_end_date = default_end_date

        # Garantir que a data final não seja anterior à inicial
        if filter_end_date < filter_start_date:
            filter_end_date = filter_start_date + timedelta(days=1)

        # Condições Q (mantidas como antes)
        status_or_completed_q = (
            Q(status__in=['PLANEJADA', 'EM_EXECUCAO', 'PENDENTE_APROVACAO', 'AGUARDANDO_PLANEJAMENTO']) |
            # Use a data de início do filtro
            Q(status='CONCLUIDA', data_fechamento__date__gte=filter_start_date)
        )

        # Otimizar o filtro de data para o período selecionado
        # Tarefas que começam ou terminam dentro do período filtrado
        time_window_q = (
            # Abertas até a data final do filtro
            Q(data_abertura__date__lte=filter_end_date) &
            # Ou com previsão a partir da data inicial do filtro
            Q(data_previsao_conclusao__gte=filter_start_date) |
            # Ou com fechamento a partir da data inicial do filtro
            Q(data_fechamento__date__gte=filter_start_date)
        )
        # Mais simples: Abertas dentro OU antes do período, e terminando dentro OU depois do período.
        # Basicamente: as barras da OS devem cruzar a janela de tempo do filtro.
        time_window_q = (
            # A OS começou ANTES ou NO DIA do fim do filtro
            Q(data_abertura__date__lte=filter_end_date) &
            # E terminou DEPOIS ou NO DIA do início do filtro (ou não tem fim)
            (Q(data_fechamento__isnull=True) | Q(
                data_fechamento__date__gte=filter_start_date))
        )

        qs = OrdemServico.objects.filter(
            status_or_completed_q,
            time_window_q,  # Agora usa o filtro de janela de tempo
            cliente__in=empresas_do_usuario,
            tecnico_responsavel__isnull=False,
        )

        qs = qs.select_related('tecnico_responsavel', 'cliente', 'equipamento').order_by(
            'tecnico_responsavel__first_name', 'data_abertura')
        return qs

    def render_to_response(self, context, **response_kwargs):
        timeline_data = []
        timeline_data.append(['Técnico', 'Ordem de Serviço',
                             'Início', 'Fim', 'Estilo', 'Tooltip'])

        status_fill_color_map = {
            'CONCLUIDA': '#28a745',
            'EM_EXECUCAO': '#ffc107',
            'PLANEJADA': '#17a2b8',
            'AGUARDANDO_PLANEJAMENTO': '#6c757d',
            'CANCELADA': '#dc3545',
            'PENDENTE_APROVACAO': '#6f42c1',
        }

        for os in self.get_queryset():
            tecnico_nome_completo = os.tecnico_responsavel.get_full_name(
            ) or os.tecnico_responsavel.username

            # Lógica para a Data de Início (Prioridade: Real > Planejado > Abertura)
            start_date_obj = None
            if os.data_inicio_real:  # Campo que será adicionado para "início real"
                start_date_obj = os.data_inicio_real.date()
            elif os.data_inicio_planejado:  # Campo "início planejado"
                start_date_obj = os.data_inicio_planejado
            else:  # Fallback para data de abertura se nada mais estiver disponível
                start_date_obj = os.data_abertura.date()

            # Lógica para a Data de Fim (Prioridade: Fechamento > Previsão de Conclusão)
            end_date_obj = None
            if os.data_fechamento:
                end_date_obj = os.data_fechamento.date()
            elif os.data_previsao_conclusao:
                end_date_obj = os.data_previsao_conclusao

            # Garante que a data de fim não seja nula e seja pelo menos um dia após o início
            if end_date_obj is None:
                if start_date_obj:
                    end_date_obj = start_date_obj + timedelta(days=1)
                else:
                    # Se não tem nem data de início, pula esta OS, pois não pode ser exibida no Gantt.
                    continue

            # Se por algum motivo a data de fim for anterior à de início, ajuste-a para ser pelo menos 1 dia.
            if end_date_obj < start_date_obj:
                end_date_obj = start_date_obj + timedelta(days=1)

            current_fill_color = status_fill_color_map.get(
                os.status, '#CCCCCC')

            start_date_js = f"new Date({start_date_obj.year}, {start_date_obj.month - 1}, {start_date_obj.day})"
            end_date_js = f"new Date({end_date_obj.year}, {end_date_obj.month - 1}, {end_date_obj.day})"

            bar_fill_style = current_fill_color

            # --- Lógica do Tooltip (ajustada para novas datas) ---
            status_display = os.get_status_display()

            # Use a data_inicio_planejado para o tooltip, se disponível, senão a data de abertura
            inicio_text = (os.data_inicio_real.strftime('%d/%m/%Y') if os.data_inicio_real else
                           os.data_inicio_planejado.strftime('%d/%m/%Y') if os.data_inicio_planejado else
                           os.data_abertura.strftime('%d/%m/%Y'))

            # Use data_previsao_conclusao para o tooltip
            prazo_text = os.data_previsao_conclusao.strftime(
                '%d/%m/%Y') if os.data_previsao_conclusao else "Não definido"

            # Use data_fechamento para o tooltip
            conclusao_text = os.data_fechamento.strftime(
                '%d/%m/%Y') if os.data_fechamento else "Não concluída"

            # Adaptação para o tooltip: Mantenha a lógica de PRAZO_TEXT e CONCLUSAO_TEXT.
            if os.status == 'EM_EXECUCAO' and os.data_previsao_conclusao:
                dias_restantes_tooltip = (
                    os.data_previsao_conclusao - timezone.localdate()).days
                if dias_restantes_tooltip < 0:
                    prazo_text += f" <span style='color:#dc3545;'>(ATRASADA {abs(dias_restantes_tooltip)} dias)</span>"
                elif dias_restantes_tooltip <= 3:
                    prazo_text += f" <span style='color:#fd7e14;'>(URGENTE - {dias_restantes_tooltip} dias)</span>"

            if os.status == 'CONCLUIDA' and os.data_fechamento and os.data_previsao_conclusao:
                if os.data_fechamento.date() <= os.data_previsao_conclusao:
                    conclusao_text += f" <span style='color:#28a745;'>(NO PRAZO)</span>"
                else:
                    dias_atraso_conclusao = (
                        os.data_fechamento.date() - os.data_previsao_conclusao).days
                    conclusao_text += f" <span style='color:#dc3545;'>(ATRASOU {dias_atraso_conclusao} dias)</span>"

            tooltip_html = f"""
                <div class="timeline-tooltip-content" style="max-width: 400px; white-space: normal; overflow: visible; height: auto;">
                    <div class="tooltip-header">
                        OS {os.numero_os}: {os.titulo_servico}
                    </div>
                    <div class="tooltip-body">
                        <div class="tooltip-item">
                            <span class="tooltip-label">Cliente:</span>
                            <span class="tooltip-value">{os.cliente.razao_social}</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Equipamento:</span>
                            <span class="tooltip-value">{os.equipamento.nome} ({os.equipamento.modelo or 'N/A'})</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Técnico:</span>
                            <span class="tooltip-value">{tecnico_nome_completo}</span>
                        </div>
                        <div class="tooltip-divider"></div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Status:</span>
                            <span class="tooltip-status" style="color:{current_fill_color};">{status_display}</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Início Real/Planejado:</span>
                            <span class="tooltip-value">{inicio_text}</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Prazo de Conclusão:</span>
                            <span class="tooltip-value">{prazo_text}</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Conclusão Real:</span>
                            <span class="tooltip-value">{conclusao_text}</span>
                        </div>
                    </div>
                </div>
            """

            timeline_data.append([
                tecnico_nome_completo,
                f"OS {os.numero_os}: {os.titulo_servico}",
                start_date_js,
                end_date_js,
                bar_fill_style,
                tooltip_html
            ])

        final_json_data = {
            'data': timeline_data
        }

        return JsonResponse(final_json_data, safe=False)


class UserDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'auth.delete_user'
    model = User
    template_name = 'servico_campo/gestao/user_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_usuarios')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, "Não foi possível excluir o usuário. Ele está associado a Ordens de Serviço, Registros de Ponto ou Relatórios de Campo. Remova as associações antes de tentar novamente.")
            # Redireciona de volta para a página de confirmação com a mensagem de erro
            return self.get(request, *args, **kwargs)


class RegraJornadaTrabalhoListView(GestorRequiredMixin, ListView):
    # Permissão para visualizar
    permission_required = 'servico_campo.view_regrajornadatrabalho'
    model = RegraJornadaTrabalho
    template_name = 'servico_campo/gestao/regra_jornada_trabalho_list.html'
    context_object_name = 'regras'
    ordering = ['-is_default', 'nome']  # Exibe a padrão primeiro

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Gestão de Regras de Jornada de Trabalho")
        return context


class RegraJornadaTrabalhoCreateView(GestorRequiredMixin, CreateView):
    # Permissão para adicionar
    permission_required = 'servico_campo.add_regrajornadatrabalho'
    model = RegraJornadaTrabalho
    form_class = RegraJornadaTrabalhoForm
    template_name = 'servico_campo/gestao/regra_jornada_trabalho_form.html'
    success_url = reverse_lazy('servico_campo:lista_regras_jornada')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Nova Regra de Jornada")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Regra de jornada adicionada com sucesso!"))
        return super().form_valid(form)


class RegraJornadaTrabalhoUpdateView(GestorRequiredMixin, UpdateView):
    # Permissão para editar
    permission_required = 'servico_campo.change_regrajornadatrabalho'
    model = RegraJornadaTrabalho
    form_class = RegraJornadaTrabalhoForm
    template_name = 'servico_campo/gestao/regra_jornada_trabalho_form.html'
    success_url = reverse_lazy('servico_campo:lista_regras_jornada')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Regra de Jornada")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Regra de jornada atualizada com sucesso!"))
        return super().form_valid(form)


class RegraJornadaTrabalhoDeleteView(GestorRequiredMixin, DeleteView):
    # Permissão para excluir
    permission_required = 'servico_campo.delete_regrajornadatrabalho'
    model = RegraJornadaTrabalho
    template_name = 'servico_campo/gestao/regra_jornada_trabalho_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_regras_jornada')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:  # Importe models do django.db se necessário
            messages.error(request, _(
                "Não foi possível excluir esta regra de jornada pois ela está associada a usuários ou outras entidades."))
            return self.get(request, *args, **kwargs)

# Views para CategoriaProblema


class CategoriaProblemaListView(GestorRequiredMixin, ListView):
    permission_required = 'servico_campo.view_categoriaproblema'
    model = CategoriaProblema
    template_name = 'servico_campo/gestao/categoria_problema_list.html'
    context_object_name = 'categorias'


class CategoriaProblemaCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'servico_campo.add_categoriaproblema'
    model = CategoriaProblema
    form_class = CategoriaProblemaForm
    template_name = 'servico_campo/gestao/categoria_problema_form.html'
    success_url = reverse_lazy('servico_campo:lista_categorias_problema')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Novo Tipo de Categoria")
        return context


class CategoriaProblemaUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_categoriaproblema'
    model = CategoriaProblema
    form_class = CategoriaProblemaForm
    template_name = 'servico_campo/gestao/categoria_problema_form.html'
    success_url = reverse_lazy('servico_campo:lista_categorias_problema')


class CategoriaProblemaDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_categoriaproblema'
    model = CategoriaProblema
    template_name = 'servico_campo/gestao/categoria_problema_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_categorias_problema')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, _(
                "Não foi possível excluir esta categoria pois ela está associada a subcategorias ou problemas existentes."))
            return self.get(request, *args, **kwargs)


# Views para SubcategoriaProblema
class SubcategoriaProblemaListView(GestorRequiredMixin, ListView):
    permission_required = 'servico_campo.view_subcategoriaproblema'
    model = SubcategoriaProblema
    template_name = 'servico_campo/gestao/subcategoria_problema_list.html'
    context_object_name = 'subcategorias'


class SubcategoriaProblemaCreateView(GestorRequiredMixin, CreateView):
    permission_required = 'servico_campo.add_subcategoriaproblema'
    model = SubcategoriaProblema
    form_class = SubcategoriaProblemaForm
    template_name = 'servico_campo/gestao/subcategoria_problema_form.html'
    success_url = reverse_lazy('servico_campo:lista_subcategorias_problema')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Novo Tipo de Subcategoria")
        return context


class SubcategoriaProblemaUpdateView(GestorRequiredMixin, UpdateView):
    permission_required = 'servico_campo.change_subcategoriaproblema'
    model = SubcategoriaProblema
    form_class = SubcategoriaProblemaForm
    template_name = 'servico_campo/gestao/subcategoria_problema_form.html'
    success_url = reverse_lazy('servico_campo:lista_subcategorias_problema')


class SubcategoriaProblemaDeleteView(GestorRequiredMixin, DeleteView):
    permission_required = 'servico_campo.delete_subcategoriaproblema'
    model = SubcategoriaProblema
    template_name = 'servico_campo/gestao/subcategoria_problema_confirm_delete.html'
    success_url = reverse_lazy('servico_campo:lista_subcategorias_problema')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, _(
                "Não foi possível excluir esta subcategoria pois ela está associada a problemas existentes."))
            return self.get(request, *args, **kwargs)


# API para carregar subcategorias dinamicamente
def load_subcategorias_problema(request):
    categoria_id = request.GET.get('categoria_id')
    subcategorias = SubcategoriaProblema.objects.filter(
        categoria_id=categoria_id, ativo=True).order_by('nome')
    return JsonResponse(list(subcategorias.values('id', 'nome')), safe=False)


class MinhasDespesasListView(LoginRequiredMixin, ListView):
    model = Despesa
    # Novo template a ser criado
    template_name = 'servico_campo/minhas_despesas_list.html'
    context_object_name = 'minhas_despesas'
    paginate_by = 10  # Opcional: para paginar a lista

    def get_queryset(self):
        user = self.request.user

        # Filtra as despesas registradas pelo usuário logado
        qs = Despesa.objects.filter(tecnico=user).select_related(
            'ordem_servico', 'categoria_despesa', 'tipo_pagamento', 'aprovado_por',
            'conta_a_pagar'  # Para acessar informações da ContaPagar diretamente
        )

        # Opcional: Adicione filtros se desejar que o usuário filtre suas próprias despesas
        status_aprovacao_filter = self.request.GET.get('status_aprovacao')
        status_pagamento_filter = self.request.GET.get('status_pagamento')
        data_despesa_filter = self.request.GET.get('data_despesa')

        if status_aprovacao_filter and status_aprovacao_filter != 'TODOS':
            qs = qs.filter(status_aprovacao=status_aprovacao_filter)

        # Filtro para status de pagamento. Note que o status de pagamento está em ContaPagar.
        if status_pagamento_filter and status_pagamento_filter != 'TODOS':
            if status_pagamento_filter == 'NAO_GERADO':  # Despesas aprovadas mas sem ContaPagar
                qs = qs.filter(status_aprovacao='APROVADA',
                               conta_a_pagar__isnull=True)
            elif status_pagamento_filter == 'NAO_PAGO':  # ContaPagar existe mas não está PAGO
                qs = qs.filter(status_aprovacao='APROVADA', conta_a_pagar__status_pagamento__in=[
                               'PENDENTE', 'EM_ANALISE', 'CANCELADO'])
            else:
                qs = qs.filter(
                    conta_a_pagar__status_pagamento=status_pagamento_filter)

        if data_despesa_filter:
            try:
                from datetime import datetime
                data_obj = datetime.strptime(
                    data_despesa_filter, '%Y-%m-%d').date()
                qs = qs.filter(data_despesa=data_obj)
            except ValueError:
                pass  # Ignora filtro de data inválido

        return qs.order_by('-data_despesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Minhas Despesas")
        context['status_aprovacao_choices'] = Despesa.STATUS_APROVACAO_CHOICES
        # Reutiliza as choices de ContaPagar
        context['status_pagamento_choices'] = ContaPagar.STATUS_PAGAMENTO_CHOICES

        # Adiciona opções extras para o filtro de status de pagamento
        context['status_pagamento_choices'] = list(context['status_pagamento_choices']) + [
            # Despesa aprovada, mas ContaPagar não criada
            ('NAO_GERADO', _('Não Gerado Contas a Pagar')),
            # ContaPagar existe mas não está PAGO
            ('NAO_PAGO', _('Não Pago (Conta a Pagar Existente)'))
        ]

        # Passa os filtros atuais para o template manter o estado
        context['filters'] = {
            'status_aprovacao': self.request.GET.get('status_aprovacao', ''),
            'status_pagamento': self.request.GET.get('status_pagamento', ''),
            'data_despesa': self.request.GET.get('data_despesa', ''),
        }
        return context


# Usa FormView para o formulário de upload
class BulkClientUploadView(GestorRequiredMixin, FormView):
    # Permissão para adicionar cliente
    permission_required = 'servico_campo.add_cliente'
    template_name = 'servico_campo/gestao/bulk_client_upload.html'  # Novo template
    form_class = BulkClientUploadForm
    # Redireciona para a lista de clientes após sucesso
    success_url = reverse_lazy('servico_campo:lista_clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Cadastro em Massa de Clientes")
        # Exemplo de cabeçalho para o template CSV
        context['sample_csv_header'] = "razao_social,cnpj_cpf,endereco,cidade,estado,cep,telefone,email,contato_principal,telefone_contato,email_contato"
        # Obtém erros de importação da sessão, se houver
        if 'failed_rows_import' in self.request.session:
            context['failed_rows'] = self.request.session.pop(
                'failed_rows_import')
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']

            # Garante que o arquivo é CSV (já validado pelo FileExtensionValidator, mas bom ter redundância)
            if not csv_file.name.lower().endswith('.csv'):
                messages.error(self.request, _(
                    "O arquivo deve ser no formato CSV."))
                return self.form_invalid(form)

            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            # Cabeçalhos esperados no CSV
            expected_headers = [
                'razao_social', 'cnpj_cpf', 'endereco', 'cidade', 'estado',
                'cep', 'telefone', 'email', 'contato_principal', 'telefone_contato', 'email_contato'
            ]

            # Valida se os cabeçalhos do CSV correspondem aos esperados
            if not all(header in reader.fieldnames for header in expected_headers):
                missing_headers = [
                    h for h in expected_headers if h not in reader.fieldnames]
                messages.error(self.request, _(
                    f"Cabeçalhos CSV inválidos. Faltam: {', '.join(missing_headers)}. Cabeçalhos esperados: {', '.join(expected_headers)}"))
                return self.form_invalid(form)

            successful_imports = 0
            failed_rows = []

            # Usa uma transação atômica para garantir que ou todas as inserções são bem-sucedidas,
            # ou nada é salvo se houver erros no meio do processo.
            with transaction.atomic():
                try:
                    # Começa do 2 para contar a linha do cabeçalho como 1
                    for row_num, row_data in enumerate(reader, start=2):
                        client_data = {}
                        # Mapeia e limpa dados da linha
                        for header in expected_headers:
                            value = row_data.get(header, '').strip()
                            # Trata valores vazios para campos nullable ou blank=True
                            client_data[header] = value if value else None

                        # Limpeza específica de dados para CNPJ/CPF e CEP (remover não-dígitos)
                        if client_data['cnpj_cpf']:
                            client_data['cnpj_cpf'] = ''.join(
                                filter(str.isdigit, client_data['cnpj_cpf']))
                        if client_data['cep']:
                            client_data['cep'] = ''.join(
                                filter(str.isdigit, client_data['cep']))

                        try:
                            # Tenta encontrar cliente existente pelo CNPJ/CPF
                            cliente_obj, created = Cliente.objects.get_or_create(
                                cnpj_cpf=client_data['cnpj_cpf'],
                                defaults=client_data  # Dados para criar se não existir
                            )

                            if not created:
                                # Se o cliente já existe, atualiza os outros campos
                                for key, value in client_data.items():
                                    # Evita atualizar o CNPJ e só atualiza se houver mudança
                                    if key != 'cnpj_cpf' and getattr(cliente_obj, key) != value:
                                        setattr(cliente_obj, key, value)
                                cliente_obj.save()
                                messages.info(self.request, _(
                                    f"Cliente '{cliente_obj.razao_social}' (CNPJ/CPF: {cliente_obj.cnpj_cpf}) atualizado."))

                            successful_imports += 1

                        except Exception as e:
                            # Captura erros de validação do Django ou outros erros durante a criação/atualização
                            failed_rows.append({
                                'row': row_num,
                                'data': row_data,
                                'error': str(e)
                            })
                            # Força o rollback da transação em caso de qualquer erro na linha
                            raise DjangoValidationError(
                                f"Erro na linha {row_num}: {str(e)}")

                except DjangoValidationError:
                    # Se uma DjangoValidationError foi levantada, a transação já está marcada para rollback
                    pass
                except Exception as e:
                    # Captura qualquer outra exceção que possa ter escapado e não é DjangoValidationError
                    transaction.set_rollback(True)
                    messages.error(self.request, _(
                        f"Ocorreu um erro inesperado durante o processamento do arquivo: {str(e)}. Nenhuma alteração foi salva."))

            # Verifica se houve falhas após o bloco try-except da transação
            if failed_rows:
                messages.warning(self.request, _(
                    f"Importação concluída com {successful_imports} clientes importados/atualizados e {len(failed_imports)} falhas."))
                # Armazena na sessão para exibir após o redirect
                self.request.session['failed_rows_import'] = failed_rows
            else:
                messages.success(self.request, _(
                    f"Todos os {successful_imports} clientes foram importados/atualizados com sucesso!"))

            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        # Limpa erros de importação da sessão ao carregar a página via GET
        if 'failed_rows_import' in request.session:
            del request.session['failed_rows_import']
        return super().get(request, *args, **kwargs)


class BulkEquipmentUploadView(GestorRequiredMixin, FormView):
    # Permissão para adicionar equipamento
    permission_required = 'servico_campo.add_equipamento'
    template_name = 'servico_campo/gestao/bulk_equipment_upload.html'  # Novo template
    form_class = BulkEquipmentUploadForm
    # Redireciona para a lista de equipamentos
    success_url = reverse_lazy('servico_campo:lista_equipamentos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Cadastro em Massa de Equipamentos")
        # Exemplo de cabeçalho para o template CSV
        context['sample_csv_header'] = "cliente_cnpj_cpf,nome,modelo,numero_serie,descricao,localizacao"
        # Obtém erros de importação da sessão, se houver
        if 'failed_rows_import' in self.request.session:
            context['failed_rows'] = self.request.session.pop(
                'failed_rows_import')
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']

            if not csv_file.name.lower().endswith('.csv'):
                messages.error(self.request, _(
                    "O arquivo deve ser no formato CSV."))
                return self.form_invalid(form)

            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            # Cabeçalhos esperados no CSV
            expected_headers = [
                'cliente_cnpj_cpf', 'nome', 'modelo', 'numero_serie', 'descricao', 'localizacao'
            ]

            if not all(header in reader.fieldnames for header in expected_headers):
                missing_headers = [
                    h for h in expected_headers if h not in reader.fieldnames]
                messages.error(self.request, _(
                    f"Cabeçalhos CSV inválidos. Faltam: {', '.join(missing_headers)}. Cabeçalhos esperados: {', '.join(expected_headers)}"))
                return self.form_invalid(form)

            successful_imports = 0
            failed_rows = []

            with transaction.atomic():
                try:
                    for row_num, row_data in enumerate(reader, start=2):
                        equipment_data = {}
                        for header in expected_headers:
                            value = row_data.get(header, '').strip()
                            equipment_data[header] = value if value else None

                        # Limpeza específica para numero_serie
                        if equipment_data['numero_serie']:
                            # Se tiver formato específico, limpe aqui.
                            equipment_data['numero_serie'] = equipment_data['numero_serie']

                        try:
                            # 1. Encontrar o cliente pela CNPJ/CPF
                            client_cnpj_cpf = ''.join(
                                filter(str.isdigit, equipment_data.pop('cliente_cnpj_cpf')))
                            try:
                                cliente = Cliente.objects.get(
                                    cnpj_cpf=client_cnpj_cpf)
                            except Cliente.DoesNotExist:
                                raise DjangoValidationError(
                                    f"Cliente com CNPJ/CPF '{client_cnpj_cpf}' não encontrado.")

                            # 2. Criar ou atualizar o equipamento
                            # Associa o objeto Cliente
                            equipment_data['cliente'] = cliente

                            # Tenta encontrar equipamento existente pelo numero_serie e cliente
                            # Pode haver equipamentos com mesmo nome/modelo em clientes diferentes
                            # ou mesmo numero_serie se não for globalmente único
                            equipment_obj, created = Equipamento.objects.get_or_create(
                                cliente=cliente,
                                # Usar numero_serie como identificador único dentro do cliente
                                numero_serie=equipment_data['numero_serie'],
                                defaults=equipment_data  # Dados para criar
                            )

                            if not created:
                                # Se o equipamento já existe, atualiza os outros campos
                                for key, value in equipment_data.items():
                                    if key not in ['cliente', 'numero_serie'] and getattr(equipment_obj, key) != value:
                                        setattr(equipment_obj, key, value)
                                equipment_obj.save()
                                messages.info(self.request, _(
                                    f"Equipamento '{equipment_obj.nome}' (Cliente: {cliente.razao_social}) atualizado."))

                            successful_imports += 1

                        except DjangoValidationError as e:
                            failed_rows.append({
                                'row': row_num,
                                'data': row_data,
                                'error': str(e)
                            })
                            raise  # Força o rollback

                        except Exception as e:
                            failed_rows.append({
                                'row': row_num,
                                'data': row_data,
                                'error': f"Erro inesperado: {str(e)}"
                            })
                            raise  # Força o rollback

                except DjangoValidationError:
                    pass
                except Exception as e:
                    transaction.set_rollback(True)
                    messages.error(self.request, _(
                        f"Ocorreu um erro inesperado durante o processamento do arquivo: {str(e)}. Nenhuma alteração foi salva."))

            if failed_rows:
                messages.warning(self.request, _(
                    f"Importação concluída com {successful_imports} equipamentos importados/atualizados e {len(failed_imports)} falhas."))
                self.request.session['failed_rows_import'] = failed_rows
            else:
                messages.success(self.request, _(
                    f"Todos os {successful_imports} equipamentos foram importados/atualizados com sucesso!"))

            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        if 'failed_rows_import' in request.session:
            del request.session['failed_rows_import']
        return super().get(request, *args, **kwargs)
