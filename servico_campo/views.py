# servico_campo/views.py

# Python / Django Imports
from io import BytesIO
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
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
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

# Imports Locais (do seu app)
from .models import (
    OrdemServico, Cliente, Equipamento, DocumentoOS, RegistroPonto,
    RelatorioCampo, FotoRelatorio, Despesa, MembroEquipe,
)
# NOVO IMPORT
from configuracoes.models import TipoManutencao, TipoDocumento, FormaPagamento

from .forms import (
    DocumentoOSForm, RegistroPontoForm, RelatorioCampoForm,
    FotoRelatorioForm, DespesaForm, EncerramentoOSForm, ClienteForm,
    EquipamentoForm, UserCreationFormCustom, UserUpdateFormCustom, GroupForm, OrdemServicoClienteForm,
    OrdemServicoPlanejamentoForm, OrdemServicoCreateForm, MembroEquipeFormSet, OrdemServicoUpdateForm
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

    if qs_base_despesas.exists():  # qs_base_despesas já está filtrado
        context['despesas_pendentes_count'] = qs_base_despesas.filter(
            aprovada=False).count()
        context['custo_total_reembolso'] = qs_base_despesas.aggregate(total=Sum('valor'))[
            'total'] or 0.00
        # Ultimas despesas registradas devem ser do usuário logado E nas empresas associadas.
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


@login_required
@permission_required('servico_campo.change_despesa', raise_exception=True)
@require_POST
def aprovar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    despesa.aprovada = True
    despesa.aprovado_por = request.user
    despesa.data_aprovacao = timezone.now()
    despesa.save()
    messages.success(
        request, f"Despesa de {despesa.descricao} aprovada com sucesso.")
    return redirect('servico_campo:lista_despesas_pendentes')


@login_required
# Assumindo permissão de exclusão para rejeitar
@permission_required('servico_campo.delete_despesa', raise_exception=True)
@require_POST
def rejeitar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    descricao_despesa = despesa.descricao
    despesa.delete()
    messages.warning(
        request, f"Despesa de {descricao_despesa} foi rejeitada e removida.")
    return redirect('servico_campo:lista_despesas_pendentes')


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
        context['documentos_os'] = os.documentos.all()
        context['registros_ponto'] = os.registros_ponto.all()
        context['ponto_aberto'] = os.registros_ponto.filter(
            tecnico=self.request.user, hora_saida__isnull=True).first()
        context['relatorios_campo'] = os.relatorios_campo.all()
        status_choices_disponiveis = [
            choice for choice in os.STATUS_CHOICES if choice[0] != 'CONCLUIDA'
        ]
        context['status_choices_disponiveis'] = status_choices_disponiveis

        # Verifica se as pré-condições para concluir a OS foram atendidas
        tem_responsavel = os.tecnico_responsavel is not None
        tem_relatorio = os.relatorios_campo.exists()
        tem_ponto = os.registros_ponto.exists()
        context['pode_concluir'] = tem_responsavel and tem_relatorio and tem_ponto

        context['os_tipo_manutencao_display'] = os.tipo_manutencao.nome

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
    form_class = RegistroPontoForm

    def post(self, request, *args, **kwargs):
        os = get_object_or_404(OrdemServico, pk=self.kwargs.get('os_pk'))
        if RegistroPonto.objects.filter(tecnico=request.user, ordem_servico=os, hora_saida__isnull=True).exists():
            messages.error(request, _(
                'Você já possui um ponto em aberto para esta OS.'))
        else:
            form = self.get_form()
            if form.is_valid():
                ponto = form.save(commit=False)
                ponto.ordem_servico = os
                ponto.tecnico = request.user
                ponto.data = timezone.localdate()
                ponto.hora_entrada = timezone.localtime().time()
                ponto.save()
                messages.success(request, _(
                    'Ponto de entrada marcado com sucesso.'))
        return redirect('servico_campo:detalhe_os', pk=os.pk)


class RegistroPontoUpdateView(LoginRequiredMixin, UpdateView):
    model = RegistroPonto
    form_class = RegistroPontoForm

    def get_object(self, queryset=None):
        return get_object_or_404(RegistroPonto, pk=self.kwargs.get('pk'), tecnico=self.request.user, hora_saida__isnull=True)

    def form_valid(self, form):
        ponto = form.save(commit=False)
        ponto.hora_saida = timezone.localtime().time()
        ponto.save()
        messages.success(self.request, _(
            'Ponto de saída encerrado com sucesso.'))
        return redirect('servico_campo:detalhe_os', pk=ponto.ordem_servico.pk)


class RelatorioCampoCreateView(LoginRequiredMixin, CreateView):
    model = RelatorioCampo
    form_class = RelatorioCampoForm
    template_name = 'servico_campo/relatorio_campo_form.html'

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.ordem_servico.pk})

    def form_valid(self, form):
        os = get_object_or_404(OrdemServico, pk=self.kwargs.get('os_pk'))
        form.instance.ordem_servico = os
        form.instance.tecnico = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = get_object_or_404(
            OrdemServico, pk=self.kwargs.get('os_pk'))
        context['form_action_title'] = 'Preencher Novo Relatório'
        return context


class RelatorioCampoUpdateView(LoginRequiredMixin, UpdateView):
    model = RelatorioCampo
    form_class = RelatorioCampoForm
    template_name = 'servico_campo/relatorio_campo_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(tecnico=self.request.user)

    def get_success_url(self):
        return reverse_lazy('servico_campo:detalhe_os', kwargs={'pk': self.object.ordem_servico.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['os'] = self.get_object().ordem_servico
        context['form_action_title'] = 'Editar Relatório'
        return context


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

# -------------------------------------------------------------
# Views de Gestão (CRUDs)
# -------------------------------------------------------------


class DespesaPendenteListView(GestorRequiredMixin, ListView):
    permission_required = 'servico_campo.change_despesa'
    model = Despesa
    template_name = 'servico_campo/despesa_pendente_list.html'
    context_object_name = 'despesas_pendentes'

    def get_queryset(self):
        return Despesa.objects.filter(aprovada=False).order_by('data_despesa')


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
        # --- MUDANÇA AQUI: REMOVIDA a coluna 'Border Class' ---
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

        # REMOVIDO: border_styles_js (não é mais usado)

        for os in self.get_queryset():
            tecnico_nome_completo = os.tecnico_responsavel.get_full_name(
            ) or os.tecnico_responsavel.username

            start_date_obj = os.data_abertura.date()
            end_date_obj = None

            current_fill_color = status_fill_color_map.get(
                os.status, '#CCCCCC')
            # REMOVIDO: current_border_class_name (não é mais usado)

            # Lógica de datas e progresso
            if os.status == 'CONCLUIDA':
                end_date_obj = os.data_fechamento.date(
                ) if os.data_fechamento else start_date_obj + timedelta(days=1)
                # REMOVIDA: Lógica de borda para 'no_prazo' ou 'atrasada' aqui
            elif os.status == 'EM_EXECUCAO':
                if os.data_previsao_conclusao:
                    end_date_obj = os.data_previsao_conclusao
                    dias_restantes = (
                        os.data_previsao_conclusao - timezone.localdate()).days
                    # REMOVIDA: Lógica de borda para 'atrasada' ou 'urgente' aqui
                else:
                    end_date_obj = start_date_obj + timedelta(days=30)
            elif os.status == 'PLANEJADA':
                end_date_obj = os.data_previsao_conclusao if os.data_previsao_conclusao else start_date_obj + \
                    timedelta(days=15)
            elif os.status == 'AGUARDANDO_PLANEJAMENTO':
                end_date_obj = start_date_obj + timedelta(days=3)
            elif os.status == 'PENDENTE_APROVACAO':
                end_date_obj = start_date_obj + timedelta(days=5)
            elif os.status == 'CANCELADA':
                end_date_obj = os.data_fechamento.date(
                ) if os.data_fechamento else start_date_obj + timedelta(days=1)

            if end_date_obj is None or end_date_obj < start_date_obj:
                end_date_obj = start_date_obj + timedelta(days=1)

            if start_date_obj == end_date_obj:
                end_date_obj = end_date_obj + timedelta(days=1)

            start_date_js = f"new Date({start_date_obj.year}, {start_date_obj.month - 1}, {start_date_obj.day})"
            end_date_js = f"new Date({end_date_obj.year}, {end_date_obj.month - 1}, {end_date_obj.day})"

            # Apenas a cor de preenchimento será enviada para role:style
            bar_fill_style = current_fill_color

            # ... (seu código para tooltip_html) ...
            status_display = os.get_status_display()
            prazo_text = os.data_previsao_conclusao.strftime(
                '%d/%m/%Y') if os.data_previsao_conclusao else "Não definido"
            conclusao_text = os.data_fechamento.strftime(
                '%d/%m/%Y') if os.data_fechamento else "Não concluída"

            # Adaptação para o tooltip: SE A BORDA NÃO EXISTE, REMOVA A MENSAGEM DO TOOLTIP TAMBÉM.
            # Se você ainda quer o (ATRASADA), (URGENTE), (NO PRAZO) no TOOLTIP,
            # mantenha a lógica de PRAZO_TEXT e CONCLUSAO_TEXT.
            # Se não, remova essas partes do código.

            # Vamos manter a lógica do tooltip porque ela é informativa, mesmo sem a borda visual.
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
                            <span class="tooltip-label">Abertura:</span>
                            <span class="tooltip-value">{start_date_obj.strftime('%d/%m/%Y')}</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Prazo:</span>
                            <span class="tooltip-value">{prazo_text}</span>
                        </div>
                        <div class="tooltip-item">
                            <span class="tooltip-label">Conclusão:</span>
                            <span class="tooltip-value">{conclusao_text}</span>
                        </div>
                    </div>
                </div>
            """

            # No final do loop, na parte timeline_data.append(...)
            # --- MUDANÇA AQUI: REMOVIDA A COLUNA 'Border Class Name' ---
            timeline_data.append([
                tecnico_nome_completo,
                f"OS {os.numero_os}: {os.titulo_servico}",
                start_date_js,
                end_date_js,
                bar_fill_style,  # Apenas a cor de preenchimento
                tooltip_html
            ])

        # Google Charts espera um JSON com a 'data'
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
