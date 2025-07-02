# configuracoes/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import ProtectedError
from . import models

from .models import TipoManutencao, TipoDocumento, FormaPagamento
from .forms import TipoManutencaoForm, TipoDocumentoForm, FormaPagamentoForm

# Mixin de permissão para todas as views de configuração


class ConfiguracaoPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    # Permissão genérica para gerenciar configurações.
    # Você pode querer criar permissões mais específicas se houver diferentes níveis de acesso.
    # Por exemplo: 'configuracoes.change_tipomanutencao'
    # Por enquanto, usaremos uma genérica de alteração para todos os modelos de configuração
    # Requer alteração em qualquer tipo de configuração
    permission_required = 'configuracoes.change_tipomanutencao'

    def handle_no_permission(self):
        messages.error(self.request, _(
            "Você não tem permissão para acessar esta área de configurações."))
        return super().handle_no_permission()

# --- CRUD para TipoManutencao ---


class TipoManutencaoListView(ConfiguracaoPermissionMixin, ListView):
    model = TipoManutencao
    template_name = 'configuracoes/tipo_manutencao_list.html'
    context_object_name = 'tipos_manutencao'
    permission_required = 'configuracoes.view_tipomanutencao'


class TipoManutencaoCreateView(ConfiguracaoPermissionMixin, CreateView):
    model = TipoManutencao
    form_class = TipoManutencaoForm
    template_name = 'configuracoes/tipo_manutencao_form.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_manutencao')
    permission_required = 'configuracoes.add_tipomanutencao'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Novo Tipo de Manutenção")
        return context


class TipoManutencaoUpdateView(ConfiguracaoPermissionMixin, UpdateView):
    model = TipoManutencao
    form_class = TipoManutencaoForm
    template_name = 'configuracoes/tipo_manutencao_form.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_manutencao')
    permission_required = 'configuracoes.change_tipomanutencao'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Tipo de Manutenção")
        return context


class TipoManutencaoDeleteView(ConfiguracaoPermissionMixin, DeleteView):
    model = TipoManutencao
    template_name = 'configuracoes/tipo_manutencao_confirm_delete.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_manutencao')
    permission_required = 'configuracoes.delete_tipomanutencao'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:  # ALTERADO: Removido 'models.'
            messages.error(request, _(
                "Não foi possível excluir este tipo de manutenção pois ele está associado a Ordens de Serviço existentes."))
            return self.get(request, *args, **kwargs)


# --- CRUD para TipoDocumento ---
class TipoDocumentoListView(ConfiguracaoPermissionMixin, ListView):
    model = TipoDocumento
    template_name = 'configuracoes/tipo_documento_list.html'
    context_object_name = 'tipos_documento'
    permission_required = 'configuracoes.view_tipodocumento'


class TipoDocumentoCreateView(ConfiguracaoPermissionMixin, CreateView):
    model = TipoDocumento
    form_class = TipoDocumentoForm
    template_name = 'configuracoes/tipo_documento_form.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_documento')
    permission_required = 'configuracoes.add_tipodocumento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Novo Tipo de Documento")
        return context


class TipoDocumentoUpdateView(ConfiguracaoPermissionMixin, UpdateView):
    model = TipoDocumento
    form_class = TipoDocumentoForm
    template_name = 'configuracoes/tipo_documento_form.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_documento')
    permission_required = 'configuracoes.change_tipodocumento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Tipo de Documento")
        return context


class TipoDocumentoDeleteView(ConfiguracaoPermissionMixin, DeleteView):
    model = TipoDocumento
    template_name = 'configuracoes/tipo_documento_confirm_delete.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_documento')
    permission_required = 'configuracoes.delete_tipodocumento'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:  # ALTERADO: Removido 'models.'
            messages.error(request, _(
                "Não foi possível excluir este tipo de documento pois ele está associado a Ordens de Serviço existentes."))
            return self.get(request, *args, **kwargs)


# --- CRUD para FormaPagamento ---
class FormaPagamentoListView(ConfiguracaoPermissionMixin, ListView):
    model = FormaPagamento
    template_name = 'configuracoes/forma_pagamento_list.html'
    context_object_name = 'formas_pagamento'
    permission_required = 'configuracoes.view_formapagamento'


class FormaPagamentoCreateView(ConfiguracaoPermissionMixin, CreateView):
    model = FormaPagamento
    form_class = FormaPagamentoForm
    template_name = 'configuracoes/forma_pagamento_form.html'
    success_url = reverse_lazy('configuracoes:lista_formas_pagamento')
    permission_required = 'configuracoes.add_formapagamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Nova Forma de Pagamento")
        return context


class FormaPagamentoUpdateView(ConfiguracaoPermissionMixin, UpdateView):
    model = FormaPagamento
    form_class = FormaPagamentoForm
    template_name = 'configuracoes/forma_pagamento_form.html'
    success_url = reverse_lazy('configuracoes:lista_formas_pagamento')
    permission_required = 'configuracoes.change_formapagamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Forma de Pagamento")
        return context


class FormaPagamentoDeleteView(ConfiguracaoPermissionMixin, DeleteView):
    model = FormaPagamento
    template_name = 'configuracoes/forma_pagamento_confirm_delete.html'
    success_url = reverse_lazy('configuracoes:lista_formas_pagamento')
    permission_required = 'configuracoes.delete_formapagamento'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:  # ALTERADO: Removido 'models.'
            messages.error(request, _(
                "Não foi possível excluir esta forma de pagamento pois ele está associado a Ordens de Serviço existentes."))
            return self.get(request, *args, **kwargs)
