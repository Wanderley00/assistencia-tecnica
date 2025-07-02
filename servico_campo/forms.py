# servico_campo/forms.py

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory

from .models import (
    OrdemServico,
    Cliente,
    Equipamento,
    DocumentoOS,
    RegistroPonto,
    RelatorioCampo,
    FotoRelatorio,
    Despesa,
    MembroEquipe
)

from configuracoes.models import TipoManutencao, TipoDocumento, FormaPagamento


class OrdemServicoCreateForm(forms.ModelForm):
    """Formulário simplificado, usado apenas na criação da OS."""
    class Meta:
        model = OrdemServico
        fields = ['numero_os', 'cliente', 'equipamento', 'titulo_servico',
                  'tipo_manutencao', 'descricao_problema']
        widgets = {
            'descricao_problema': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['equipamento'].queryset = Equipamento.objects.none()
        if 'cliente' in self.data:
            try:
                cliente_id = int(self.data.get('cliente'))
                self.fields['equipamento'].queryset = Equipamento.objects.filter(
                    cliente_id=cliente_id).order_by('nome')
            except (ValueError, TypeError):
                pass
        # NOVO: Define o queryset para tipo_manutencao
        self.fields['tipo_manutencao'].queryset = TipoManutencao.objects.filter(
            ativo=True)


class OrdemServicoUpdateForm(forms.ModelForm):
    """Formulário para editar os dados principais de uma Ordem de Serviço."""
    class Meta:
        model = OrdemServico
        fields = ['numero_os', 'cliente', 'equipamento', 'titulo_servico',
                  'tipo_manutencao', 'descricao_problema', 'status']
        widgets = {
            'descricao_problema': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        if self.instance and self.instance.cliente:
            self.fields['equipamento'].queryset = Equipamento.objects.filter(
                cliente=self.instance.cliente).order_by('nome')
        # NOVO: Define o queryset para tipo_manutencao
        self.fields['tipo_manutencao'].queryset = TipoManutencao.objects.filter(
            ativo=True)


class OrdemServicoPlanejamentoForm(forms.ModelForm):
    """Formulário completo, usado na tela de planejamento."""
    class Meta:
        model = OrdemServico
        fields = ['tecnico_responsavel',
                  'data_previsao_conclusao', 'observacoes_gerais']
        widgets = {
            'data_previsao_conclusao': forms.DateInput(attrs={'type': 'date'}),
            'observacoes_gerais': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class MembroEquipeForm(forms.ModelForm):
    """Formulário para um único membro da equipe."""
    class Meta:
        model = MembroEquipe
        fields = ['nome_completo', 'funcao', 'identificacao']

    # --- MÉTODO QUE FALTAVA ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


MembroEquipeFormSet = inlineformset_factory(
    OrdemServico,
    MembroEquipe,
    form=MembroEquipeForm,
    extra=0,
    can_delete=True,
    can_delete_extra=True
)


class DocumentoOSForm(forms.ModelForm):
    class Meta:
        model = DocumentoOS
        fields = ['tipo_documento', 'titulo', 'arquivo', 'descricao']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        # NOVO: Define o queryset para tipo_documento
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(
            ativo=True)


class RegistroPontoForm(forms.ModelForm):
    class Meta:
        model = RegistroPonto
        fields = ['localizacao', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class RelatorioCampoForm(forms.ModelForm):
    class Meta:
        model = RelatorioCampo
        fields = [
            'tipo_relatorio', 'data_relatorio', 'descricao_atividades',
            'problemas_identificados', 'solucoes_aplicadas', 'material_utilizado',
            'horas_normais', 'horas_extras_60', 'horas_extras_100', 'km_rodado',
            'local_servico', 'observacoes_adicionais', 'assinatura_executante_data',
        ]
        widgets = {
            'data_relatorio': forms.DateInput(attrs={'type': 'date'}),
            'descricao_atividades': forms.Textarea(attrs={'rows': 5}),
            'problemas_identificados': forms.Textarea(attrs={'rows': 3}),
            'solucoes_aplicadas': forms.Textarea(attrs={'rows': 3}),
            'material_utilizado': forms.Textarea(attrs={'rows': 3}),
            'observacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
            'assinatura_executante_data': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.update({'class': 'form-control'})


class FotoRelatorioForm(forms.ModelForm):
    class Meta:
        model = FotoRelatorio
        fields = ['imagem', 'descricao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ['data_despesa', 'descricao', 'valor',
                  'tipo_pagamento', 'comprovante_anexo', 'local_despesa']
        widgets = {'data_despesa': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        # NOVO: Define o queryset para tipo_pagamento
        self.fields['tipo_pagamento'].queryset = FormaPagamento.objects.filter(
            ativo=True)


class EncerramentoOSForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['assinatura_cliente_data']
        widgets = {'assinatura_cliente_data': forms.HiddenInput()}


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class UserCreationFormCustom(UserCreationForm):
    # Alterado de volta para ModelChoiceField (dropdown de seleção única)
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,  # Definir como True se a seleção de grupo for obrigatória
        label="Grupo(s)",
        widget=forms.Select  # Força o widget a ser um dropdown padrão
    )

    empresas = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Empresas Associadas"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + \
            ('first_name', 'last_name', 'email', 'groups', 'empresas')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Aplica form-control a todos os campos, exceto CheckboxSelectMultiple
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        # Salva o usuário primeiro, mas não comita ainda
        user = super().save(commit=False)
        if commit:
            user.save()  # Agora comita o usuário no banco de dados

            # Adiciona o grupo selecionado (que é um único objeto Group)
            group = self.cleaned_data.get('groups')
            if group:
                # Usa set() com uma LISTA contendo o único grupo
                # <--- MUDANÇA AQUI: envolver 'group' em uma lista
                user.groups.set([group])

            # Adiciona as empresas associadas
            user.empresas_associadas.set(self.cleaned_data['empresas'])
        return user


class UserUpdateFormCustom(forms.ModelForm):
    # Alterado de volta para ModelChoiceField (dropdown de seleção única)
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Grupo(s)",
        widget=forms.Select  # Força o widget a ser um dropdown padrão
    )

    empresas = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Empresas Associadas"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'groups', 'is_active', 'empresas']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Para Update, a initial do campo groups deve ser o grupo do usuário (o primeiro, se houver)
            self.fields['groups'].initial = self.instance.groups.first()
            self.fields['empresas'].initial = self.instance.empresas_associadas.all()

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Adiciona o grupo selecionado (que é um único objeto Group)
            group = self.cleaned_data.get('groups')
            if group:
                # Usa set() com uma LISTA contendo o único grupo
                # <--- MUDANÇA AQUI: envolver 'group' em uma lista
                user.groups.set([group])

            # Adiciona as empresas associadas
            user.empresas_associadas.set(self.cleaned_data['empresas'])
        return user


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {'permissions': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        perm_choices = []
        for perm in self.fields['permissions'].queryset.select_related('content_type'):
            action_map = {'add': 'Adicionar', 'change': 'Alterar',
                          'delete': 'Excluir', 'view': 'Visualizar'}
            codename_action = perm.codename.split('_')[0]
            action_verb = action_map.get(codename_action, perm.codename)
            model_name = perm.content_type.model_class()._meta.verbose_name
            friendly_name = f"{action_verb} {model_name}"
            perm_choices.append((perm.id, friendly_name))
        self.fields['permissions'].choices = perm_choices


class LoginFormCustom(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'placeholder': 'Usuário', 'required': 'required'})
        self.fields['password'].widget.attrs.update(
            {'placeholder': 'Senha', 'required': 'required'})


class OrdemServicoClienteForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['cliente', 'equipamento',
                  'titulo_servico', 'descricao_problema']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
