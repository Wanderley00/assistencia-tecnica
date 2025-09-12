# configuracoes/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import ProtectedError
from . import models

from .models import TipoManutencao, TipoDocumento, FormaPagamento, CategoriaDespesa, PoliticaDespesa, ConfiguracaoEmail, TipoRelatorio
from .forms import TipoManutencaoForm, TipoDocumentoForm, FormaPagamentoForm, CategoriaDespesaForm, PoliticaDespesaForm, ConfiguracaoEmailForm, TipoRelatorioForm

# Mixin de permissão para todas as views de configuração

from django.shortcuts import render, redirect
from django.contrib import messages


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
        context['form_title'] = _("Adicionar Novo Tipo de Serviço")
        return context


class TipoManutencaoUpdateView(ConfiguracaoPermissionMixin, UpdateView):
    model = TipoManutencao
    form_class = TipoManutencaoForm
    template_name = 'configuracoes/tipo_manutencao_form.html'
    success_url = reverse_lazy('configuracoes:lista_tipos_manutencao')
    permission_required = 'configuracoes.change_tipomanutencao'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Tipo de Serviço")
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
                "Não foi possível excluir este tipo de Serviço pois ele está associado a Ordens de Serviço existentes."))
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


# Views para CategoriaDespesa
# Ou LoginRequiredMixin, se não for específico de gestor
class CategoriaDespesaListView(LoginRequiredMixin, ListView):
    permission_required = 'configuracoes.view_categoriadespesa'
    model = CategoriaDespesa
    template_name = 'configuracoes/categoria_despesa_list.html'
    context_object_name = 'categorias_despesa'
    ordering = ['nome']


class CategoriaDespesaCreateView(LoginRequiredMixin, CreateView):
    permission_required = 'configuracoes.add_categoriadespesa'
    model = CategoriaDespesa
    form_class = CategoriaDespesaForm
    template_name = 'configuracoes/categoria_despesa_form.html'
    success_url = reverse_lazy('configuracoes:lista_categorias_despesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Nova Categoria de Despesa")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Categoria de despesa adicionada com sucesso!"))
        return super().form_valid(form)


class CategoriaDespesaUpdateView(LoginRequiredMixin, UpdateView):
    permission_required = 'configuracoes.change_categoriadespesa'
    model = CategoriaDespesa
    form_class = CategoriaDespesaForm
    template_name = 'configuracoes/categoria_despesa_form.html'
    success_url = reverse_lazy('configuracoes:lista_categorias_despesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Categoria de Despesa")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Categoria de despesa atualizada com sucesso!"))
        return super().form_valid(form)


class CategoriaDespesaDeleteView(LoginRequiredMixin, DeleteView):
    permission_required = 'configuracoes.delete_categoriadespesa'
    model = CategoriaDespesa
    template_name = 'configuracoes/categoria_despesa_confirm_delete.html'
    success_url = reverse_lazy('configuracoes:lista_categorias_despesa')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, _(
                "Não foi possível excluir esta categoria de despesa pois ela está associada a despesas existentes."))
            return self.get(request, *args, **kwargs)


# Views para PoliticaDespesa
class PoliticaDespesaListView(LoginRequiredMixin, ListView):
    permission_required = 'configuracoes.view_politicadespesa'
    model = PoliticaDespesa
    template_name = 'configuracoes/politica_despesa_list.html'
    context_object_name = 'politicas_despesa'
    ordering = ['-ativa', '-data_upload']  # Ativas primeiro, depois por data


class PoliticaDespesaCreateView(LoginRequiredMixin, CreateView):
    permission_required = 'configuracoes.add_politicadespesa'
    model = PoliticaDespesa
    form_class = PoliticaDespesaForm
    template_name = 'configuracoes/politica_despesa_form.html'
    success_url = reverse_lazy('configuracoes:lista_politicas_despesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Anexar Nova Política de Despesa")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Política de despesa adicionada com sucesso!"))
        return super().form_valid(form)


class PoliticaDespesaUpdateView(LoginRequiredMixin, UpdateView):
    permission_required = 'configuracoes.change_politicadespesa'
    model = PoliticaDespesa
    form_class = PoliticaDespesaForm
    template_name = 'configuracoes/politica_despesa_form.html'
    success_url = reverse_lazy('configuracoes:lista_politicas_despesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Política de Despesa")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Política de despesa atualizada com sucesso!"))
        return super().form_valid(form)


class PoliticaDespesaDeleteView(LoginRequiredMixin, DeleteView):
    permission_required = 'configuracoes.delete_politicadespesa'
    model = PoliticaDespesa
    template_name = 'configuracoes/politica_despesa_confirm_delete.html'
    success_url = reverse_lazy('configuracoes:lista_politicas_despesa')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except models.ProtectedError:
            messages.error(request, _(
                # Nenhuma foreign key, então menos chances de ProtectedError
                "Não foi possível excluir esta política de despesa."))
            return self.get(request, *args, **kwargs)


class ConfiguracaoEmailUpdateView(LoginRequiredMixin, UpdateView):
    permission_required = 'configuracoes.change_configuracaoemail'
    model = ConfiguracaoEmail
    form_class = ConfiguracaoEmailForm
    template_name = 'configuracoes/configuracao_email_form.html'  # Novo template
    # Redireciona para a mesma página
    success_url = reverse_lazy('configuracoes:configuracao_email')

    def get_object(self, queryset=None):
        # Garante que sempre editamos a única instância existente (singleton)
        return ConfiguracaoEmail.get_solo()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Configurações de Envio de E-mail")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(
            "Configurações de e-mail salvas com sucesso!"))
        # IMPORTANTE: Reconfigurar o backend de e-mail do Django IMEDIATAMENTE.
        # Isso garante que as novas configurações sejam usadas sem reiniciar o servidor.
        self._reconfigure_email_backend(form.instance)
        return super().form_valid(form)

    def _reconfigure_email_backend(self, config_instance):
        """
        Reconfigura o backend de e-mail do Django em tempo de execução.
        """
        from django.core.mail import get_connection, backends
        from django.conf import settings

        # Define as configurações do settings temporariamente para a conexão
        settings.EMAIL_BACKEND = config_instance.email_backend
        settings.EMAIL_HOST = config_instance.email_host
        settings.EMAIL_PORT = config_instance.email_port
        settings.EMAIL_USE_TLS = config_instance.email_use_tls
        settings.EMAIL_USE_SSL = config_instance.email_use_ssl
        settings.EMAIL_HOST_USER = config_instance.email_host_user
        settings.EMAIL_HOST_PASSWORD = config_instance.email_host_password
        settings.DEFAULT_FROM_EMAIL = config_instance.default_from_email
        settings.SERVER_EMAIL = config_instance.default_from_email

        # Recria a conexão de e-mail (se o backend já tiver sido acessado)
        # Isso é um pouco hacky, pois reconfigura globalmente.
        # Uma alternativa seria passar a conexão configurada para cada send_mail.
        # Para simplicidade e efeito global, redefinir settings funciona.
        try:
            # Força o Django a recarregar a conexão padrão com as novas settings
            # Isso pode não funcionar perfeitamente em todos os cenários sem reiniciar o app,
            # mas é o melhor que se pode fazer para reconfiguração em runtime.
            if hasattr(backends, '_connections') and 'default' in backends._connections:
                del backends._connections['default']
        except Exception as e:
            print(f"Erro ao reconfigurar conexão de email em runtime: {e}")


def configuracao_email_view(request):
    config, created = ConfiguracaoEmail.objects.get_or_create(pk=1)

    if request.method == 'POST':
        form = ConfiguracaoEmailForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Configurações de e-mail salvas com sucesso!')
            return redirect('configuracoes:configuracao_email')
        else:
            messages.error(
                request, 'O formulário contém erros. Por favor, corrija-os.')
    else:
        form = ConfiguracaoEmailForm(instance=config)

    context = {
        'form': form
    }
    # Opcional: Mover o template para a pasta do app 'configuracoes' também seria uma boa prática
    return render(request, 'configuracoes/configuracao_email.html', context)

# 2. ADICIONE O CRUD COMPLETO PARA TIPORELATORIO
# --- CRUD para TipoRelatorio ---


class TipoRelatorioListView(ConfiguracaoPermissionMixin, ListView):
    model = TipoRelatorio
    template_name = 'configuracoes/tipo_relatorio_list.html'  # << NOVO TEMPLATE
    context_object_name = 'tipos_relatorio'
    permission_required = 'configuracoes.view_tiporelatorio'


class TipoRelatorioCreateView(ConfiguracaoPermissionMixin, CreateView):
    model = TipoRelatorio
    form_class = TipoRelatorioForm
    template_name = 'configuracoes/tipo_relatorio_form.html'  # << NOVO TEMPLATE
    success_url = reverse_lazy(
        'configuracoes:lista_tipos_relatorio')  # << NOVA URL
    permission_required = 'configuracoes.add_tiporelatorio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Adicionar Novo Tipo de Relatório")
        return context


class TipoRelatorioUpdateView(ConfiguracaoPermissionMixin, UpdateView):
    model = TipoRelatorio
    form_class = TipoRelatorioForm
    template_name = 'configuracoes/tipo_relatorio_form.html'  # << NOVO TEMPLATE
    success_url = reverse_lazy(
        'configuracoes:lista_tipos_relatorio')  # << NOVA URL
    permission_required = 'configuracoes.change_tiporelatorio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Editar Tipo de Relatório")
        return context


class TipoRelatorioDeleteView(ConfiguracaoPermissionMixin, DeleteView):
    model = TipoRelatorio
    template_name = 'configuracoes/tipo_relatorio_confirm_delete.html'  # << NOVO TEMPLATE
    success_url = reverse_lazy(
        'configuracoes:lista_tipos_relatorio')  # << NOVA URL
    permission_required = 'configuracoes.delete_tiporelatorio'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, _(
                "Não foi possível excluir este tipo de relatório pois ele está associado a relatórios existentes."))
            return self.get(request, *args, **kwargs)
