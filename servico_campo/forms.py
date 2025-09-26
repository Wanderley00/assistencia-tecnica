# servico_campo/forms.py

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.core.validators import FileExtensionValidator
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .utils import get_email_backend
from configuracoes.models import ConfiguracaoEmail

from .models import (
    OrdemServico,
    Cliente,
    Equipamento,
    DocumentoOS,
    RegistroPonto,
    RelatorioCampo,
    FotoRelatorio,
    Despesa,
    MembroEquipe,
    RegraJornadaTrabalho,
    CategoriaProblema,
    SubcategoriaProblema,
    ProblemaRelatorio,
    ContaPagar,
    PerfilUsuario,
    HorasRelatorioTecnico,
)

from configuracoes.models import TipoManutencao, TipoDocumento, FormaPagamento, CategoriaDespesa

from django.contrib.auth.models import User


class PasswordResetFormCustom(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',  # Adiciona a classe Bootstrap
            'placeholder': _('Seu endereço de e-mail')  # Placeholder útil
        })


class OrdemServicoCreateForm(forms.ModelForm):
    """Formulário simplificado, usado apenas na criação da OS."""
    class Meta:
        model = OrdemServico
        fields = ['numero_os', 'cliente', 'equipamento', 'titulo_servico',
                  'tipo_manutencao', 'gestor_responsavel', 'descricao_problema']
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

        # Filtra usuários que são gestores (exemplo: se tiver um grupo 'Gestores')
        # self.fields['gestor_responsavel'].queryset = User.objects.filter(groups__name='Gestores').order_by('first_name')
        # OU, para listar todos os usuários, como fallback:
        self.fields['gestor_responsavel'].queryset = User.objects.all().order_by(
            'first_name', 'username')  # NOVO: Define o queryset para gestor_responsavel


class OrdemServicoUpdateForm(forms.ModelForm):
    """Formulário para editar os dados principais de uma Ordem de Serviço."""
    class Meta:
        model = OrdemServico
        fields = ['numero_os', 'cliente', 'equipamento', 'titulo_servico',
                  'tipo_manutencao', 'gestor_responsavel', 'descricao_problema', 'status']
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

        # Filtra usuários que são gestores (exemplo: se tiver um grupo 'Gestores')
        # self.fields['gestor_responsavel'].queryset = User.objects.filter(groups__name='Gestores').order_by('first_name')
        # OU, para listar todos os usuários, como fallback:
        self.fields['gestor_responsavel'].queryset = User.objects.all().order_by(
            'first_name', 'username')  # NOVO: Define o queryset para gestor_responsavel


class OrdemServicoPlanejamentoForm(forms.ModelForm):
    """Formulário completo, usado na tela de planejamento."""
    class Meta:
        model = OrdemServico
        fields = ['tecnico_responsavel', 'data_inicio_planejado',
                  'data_previsao_conclusao', 'observacoes_gerais']
        widgets = {
            'data_inicio_planejado': forms.DateInput(attrs={'type': 'date'}),
            'data_previsao_conclusao': forms.DateInput(attrs={'type': 'date'}),
            'observacoes_gerais': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # NOVO: Define o queryset para tecnico_responsavel e garante que ele seja opcional no formulário
        self.fields['tecnico_responsavel'].queryset = User.objects.all().order_by(
            'first_name', 'username')
        # Adiciona uma opção vazia
        self.fields['tecnico_responsavel'].empty_label = "--------"
        # Garante que o campo possa ser nulo
        self.fields['tecnico_responsavel'].required = False


class MembroEquipeForm(forms.ModelForm):
    """Formulário para um único membro da equipe (apenas usuários do sistema)."""
    usuario = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('first_name', 'username'),
        required=True,
        label="Membro da Equipe",
        widget=forms.Select(
            attrs={'class': 'form-control membro-usuario-select'})
    )

    class Meta:
        model = MembroEquipe
        # ALTERADO: Adicionado 'funcao' de volta
        fields = ['usuario', 'funcao']  # <--- MUDE AQUI

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        # Se você quiser adicionar uma classe específica ao campo 'funcao'
        # self.fields['funcao'].widget.attrs.update({'class': 'form-control minha-classe-funcao'})


# O inlineformset_factory continuará usando este formulário MembroEquipeForm
# Nenhuma mudança aqui.
MembroEquipeFormSet = inlineformset_factory(
    OrdemServico,
    MembroEquipe,
    form=MembroEquipeForm,
    extra=1,
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
        # Este será o formulário para EDIÇÃO COMPLETA
        fields = ['data', 'hora_entrada', 'hora_saida',
                  'localizacao', 'localizacao_saida', 'observacoes_entrada', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora_entrada': forms.TimeInput(attrs={'type': 'time'}),
            'hora_saida': forms.TimeInput(attrs={'type': 'time'}),
            'observacoes_entrada': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['localizacao'].label = _("Localização de Entrada")
        self.fields['localizacao_saida'].label = _("Localização de Saída")
        self.fields['observacoes'].label = _("Observações de Saída")


# NOVO FORMULÁRIO: Para Marcar Ponto de Entrada
class RegistroPontoEntradaForm(forms.ModelForm):
    observacoes_entrada = forms.CharField(
        max_length=255, required=False, label=_("Observações (Opcional)"))
    localizacao = forms.CharField(
        max_length=255, required=False, label=_("Localização (Opcional)"))
    gps_coords = forms.CharField(
        max_length=255, required=False, widget=forms.HiddenInput())  # Campo para GPS

    class Meta:
        model = RegistroPonto
        # Apenas os campos que vêm do formulário (localização manual e observações, se tiver)
        # data, hora_entrada, tecnico, os serão preenchidos na view
        # observacoes agora será do modal de entrada também
        fields = ['localizacao', 'observacoes_entrada']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['localizacao'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': _('Ex: Cliente A, Centro')})
        self.fields['observacoes_entrada'].widget.attrs.update(
            {'class': 'form-control', 'rows': 2, 'placeholder': _('Observações iniciais (opcional)')})


# NOVO FORMULÁRIO: Para Encerrar Ponto de Saída
class RegistroPontoSaidaForm(forms.ModelForm):
    # Campos que o usuário pode preencher ao encerrar o ponto
    localizacao_saida = forms.CharField(
        max_length=255, required=False, label=_("Localização de Saída (Opcional)"))
    observacoes = forms.CharField(
        max_length=255, required=False, label=_("Observações (Opcional)"))
    gps_coords_saida = forms.CharField(
        max_length=255, required=False, widget=forms.HiddenInput())  # Campo para GPS de saída

    class Meta:
        model = RegistroPonto
        # Apenas os campos que podem ser atualizados na saída
        # hora_saida será preenchida na view
        fields = ['localizacao_saida', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['localizacao_saida'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': _('Ex: Saída do Cliente')})
        self.fields['observacoes'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': _('Ex: Término do dia'), 'rows': 2})


class RelatorioCampoForm(forms.ModelForm):
    # ADIÇÃO: Crie campos para receber os dados Base64 do Javascript.
    # Os nomes 'assinatura_executante_data' e 'assinatura_cliente_data'
    # correspondem aos IDs dos inputs no seu JavaScript.
    assinatura_executante_data = forms.CharField(
        widget=forms.HiddenInput(), required=False)
    assinatura_cliente_data = forms.CharField(
        widget=forms.HiddenInput(), required=False)

    class Meta:
        model = RelatorioCampo
        # REMOÇÃO: Tire os campos de assinatura originais da lista de fields.
        # Eles serão preenchidos na view, não diretamente pelo formulário.
        fields = [
            'tipo_relatorio', 'data_relatorio', 'descricao_atividades',
            'material_utilizado',
            'local_servico', 'observacoes_adicionais',
        ]
        widgets = {
            'data_relatorio': forms.DateInput(
                format='%Y-%m-%d', attrs={'type': 'date'}),
            'descricao_atividades': forms.Textarea(attrs={'rows': 5}),
            'material_utilizado': forms.Textarea(attrs={'rows': 3}),
            'observacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
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
                  'tipo_pagamento', 'categoria_despesa',  # NOVO CAMPO AQUI
                  'comprovante_anexo', 'local_despesa',
                  'is_adiantamento']
        widgets = {'data_despesa': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Aplica 'form-control' a maioria dos campos
            if not isinstance(field.widget, forms.CheckboxInput):  # Exclui checkboxes
                field.widget.attrs.update({'class': 'form-control'})
            # Adiciona classe para checkboxes se desejar estilização específica
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

        # Define o queryset para tipo_pagamento
        self.fields['tipo_pagamento'].queryset = FormaPagamento.objects.filter(
            ativo=True)

        # NOVO: Define o queryset para categoria_despesa
        self.fields['categoria_despesa'].queryset = CategoriaDespesa.objects.filter(
            ativo=True)


class EncerramentoOSForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['assinatura_cliente', 'assinatura_executante']
        widgets = {'assinatura_cliente': forms.HiddenInput(),
                   'assinatura_executante': forms.HiddenInput(),
                   }


class ClienteForm(forms.ModelForm):
    # --- CAMPO PERSONALIZADO CORRIGIDO ---
    usuarios_associados = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by('first_name', 'last_name', 'username'),

        # 1. Usaremos checkboxes para uma melhor UX.
        widget=forms.CheckboxSelectMultiple,

        required=False,
        label="Usuários com Acesso"
    )
    # --- FIM DO CAMPO PERSONALIZADO ---

    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplica a classe 'form-control' a todos os campos, exceto o nosso.
        for field_name, field in self.fields.items():
            # Exclui o campo de múltipla escolha do estilo padrão 'form-control'
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})

        # --- NOVO: Sobrescreve o label de cada checkbox ---
        # Esta é a forma correta de customizar o que é exibido para cada usuário.
        self.fields['usuarios_associados'].label_from_instance = lambda obj: obj.get_full_name(
        ) or obj.username


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
        queryset=Cliente.objects.all().order_by('razao_social'),  # Garante a ordenação
        # VOLTOU para CheckboxSelectMultiple
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Empresas Associadas"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Adicione 'is_active' aqui para que apareça no formulário de criação
        fields = UserCreationForm.Meta.fields + \
            ('first_name', 'last_name', 'email', 'groups', 'empresas', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Aplica form-control a campos de texto/seleção, e form-check-input para checkboxes
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.Select, forms.PasswordInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                # Para CheckboxSelectMultiple (campo 'empresas'), não aplicar form-control diretamente ao widget principal
                # A estilização dos itens internos é feita pelo template e pelo CSS personalizado
                pass

    def save(self, commit=True):
        # Salva o usuário primeiro, mas não comita ainda
        user = super().save(commit=False)
        if commit:
            user.save()  # Agora comita o usuário no banco de dados

            # Adiciona o grupo selecionado (que é um único objeto Group)
            group = self.cleaned_data.get('groups')
            if group:
                # Usa set() com uma LISTA contendo o único grupo
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
        queryset=Cliente.objects.all().order_by('razao_social'),  # Garante a ordenação
        # VOLTOU para CheckboxSelectMultiple
        widget=forms.CheckboxSelectMultiple(),
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
            # Aplica form-control a campos de texto/seleção, e form-check-input para checkboxes
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.Select)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                # Para CheckboxSelectMultiple (campo 'empresas'), não aplicar form-control diretamente ao widget principal
                # A estilização dos itens internos é feita pelo template e pelo CSS personalizado
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Adiciona o grupo selecionado (que é um único objeto Group)
            group = self.cleaned_data.get('groups')
            if group:
                # Usa set() com uma LISTA contendo o único grupo
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
    # Seu formulário de login (sem alterações)
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Usuário'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Senha'}))


class OrdemServicoClienteForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['cliente', 'equipamento',
                  'titulo_servico', 'descricao_problema']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class RegraJornadaTrabalhoForm(forms.ModelForm):
    class Meta:
        model = RegraJornadaTrabalho
        fields = '__all__'  # Inclui todos os campos do modelo
        widgets = {
            'inicio_jornada_normal': forms.TimeInput(attrs={'type': 'time'}),
            'fim_jornada_normal': forms.TimeInput(attrs={'type': 'time'}),
            'inicio_extra_60': forms.TimeInput(attrs={'type': 'time'}),
            'fim_extra_60': forms.TimeInput(attrs={'type': 'time'}),
            'inicio_extra_100': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Aplica 'form-control' a maioria dos campos, exceto checkboxes
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            # Adiciona classe para checkboxes também, se desejar
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean_is_default(self):
        """
        Garante que apenas uma regra de jornada de trabalho seja marcada como padrão (is_default).
        """
        is_default = self.cleaned_data.get('is_default')
        if is_default:
            # Se esta regra está sendo marcada como padrão, desmarque as outras
            qs = RegraJornadaTrabalho.objects.filter(is_default=True)
            if self.instance.pk:  # Se for uma edição, exclui a própria instância da query
                qs = qs.exclude(pk=self.instance.pk)
            qs.update(is_default=False)
        return is_default

    def clean(self):
        cleaned_data = super().clean()
        inicio_normal = cleaned_data.get('inicio_jornada_normal')
        fim_normal = cleaned_data.get('fim_jornada_normal')
        inicio_extra_60 = cleaned_data.get('inicio_extra_60')
        fim_extra_60 = cleaned_data.get('fim_extra_60')
        inicio_extra_100 = cleaned_data.get('inicio_extra_100')

        # Validação de ordem dos horários
        if inicio_normal and fim_normal and inicio_normal >= fim_normal:
            self.add_error('fim_jornada_normal', _(
                "O fim da jornada normal deve ser depois do início."))
        if inicio_extra_60 and fim_extra_60 and inicio_extra_60 >= fim_extra_60:
            self.add_error('fim_extra_60', _(
                "O fim da hora extra 50% deve ser depois do início."))
        if inicio_extra_60 and inicio_extra_100 and inicio_extra_60 >= inicio_extra_100:
            self.add_error('inicio_extra_100', _(
                "O início da hora extra 100% deve ser depois do início da hora extra 50%."))

        # Validação de sobreposição de faixas de horário (básica)
        if fim_normal and inicio_extra_60 and fim_normal > inicio_extra_60:
            self.add_error('inicio_extra_60', _(
                "O início da hora extra 50% deve ser após o fim da jornada normal."))
        if fim_extra_60 and inicio_extra_100 and fim_extra_60 > inicio_extra_100:
            self.add_error('inicio_extra_100', _(
                "O início da hora extra 100% deve ser após o fim da hora extra 50%."))

        return cleaned_data


class CategoriaProblemaForm(forms.ModelForm):
    class Meta:
        model = CategoriaProblema
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': _('Ex: Elétrica, Mecânica')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})


class SubcategoriaProblemaForm(forms.ModelForm):
    class Meta:
        model = SubcategoriaProblema
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': _('Ex: Curto-circuito, Falha de Software')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].widget.attrs.update({'class': 'form-control'})
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})

# Formulário para um problema individual em um relatório


class ProblemaRelatorioForm(forms.ModelForm):
    class Meta:
        model = ProblemaRelatorio
        fields = ['categoria', 'subcategoria',
                  'observacao', 'solucao_aplicada']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select problema-categoria-select'}),
            'subcategoria': forms.Select(attrs={'class': 'form-select problema-subcategoria-select'}),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Detalhes específicos do problema...')
            }),
            # ADICIONE O WIDGET PARA O NOVO CAMPO
            'solucao_aplicada': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Descreva a solução aplicada a este problema...')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['categoria'].queryset = CategoriaProblema.objects.filter(
            ativo=True)

        # 1. Obter o ID da subcategoria que está sendo validada (seja do POST ou da instância)
        subcategoria_id_from_data = None
        if 'subcategoria' in self.data and self.data.get('subcategoria'):
            try:
                subcategoria_id_from_data = int(self.data['subcategoria'])
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.subcategoria:
            subcategoria_id_from_data = self.instance.subcategoria.pk

        # 2. Iniciar o queryset da subcategoria com um conjunto vazio ou filtrado pela categoria,
        #    mas *sempre adicionar* a subcategoria que veio nos dados do formulário (POST ou instância).
        #    Isso garante que o valor submetido possa ser "encontrado" pelo widget.

        # Começa com o queryset de todas as subcategorias ativas.
        # A validação de pertinência à categoria é feita no clean().
        qs_subcategorias = SubcategoriaProblema.objects.filter(
            ativo=True).order_by('nome')

        # Se há uma subcategoria vindo dos dados (POST ou instância),
        # garanta que ela esteja no queryset do campo.
        if subcategoria_id_from_data:
            try:
                # Tenta obter a subcategoria do banco de dados
                subcategoria_do_banco = SubcategoriaProblema.objects.get(
                    pk=subcategoria_id_from_data)
                # Adiciona essa subcategoria ao queryset, garantindo que ela seja uma opção.
                qs_subcategorias = (qs_subcategorias | SubcategoriaProblema.objects.filter(
                    pk=subcategoria_do_banco.pk)).distinct().order_by('nome')
            except SubcategoriaProblema.DoesNotExist:
                # Se a subcategoria do POST não existe mais, ela não será adicionada,
                # e o erro de "escolha inválida" poderá persistir se não houver outra opção válida.
                # Neste caso, o clean() deve pegar o erro de qualquer forma.
                pass

        self.fields['subcategoria'].queryset = qs_subcategorias

        # Observação não é obrigatória
        self.fields['observacao'].required = False

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get('categoria')
        subcategoria = cleaned_data.get('subcategoria')

        # Validação da combinação categoria/subcategoria
        if categoria and subcategoria:
            if subcategoria.categoria != categoria:
                self.add_error(
                    'subcategoria',
                    _("A subcategoria selecionada não pertence à categoria principal.")
                )
        # Se você quiser que a subcategoria seja obrigatória se uma categoria for selecionada, adicione:
        # elif categoria and not subcategoria:
        #     self.add_error('subcategoria', _("Por favor, selecione uma subcategoria para a categoria escolhida."))

        # A observação é opcional, então não precisa de validação extra aqui para obrigatoriedade.

        return cleaned_data

    # O inline formset para ProblemaRelatorio (definido na view)
ProblemaRelatorioFormSet = inlineformset_factory(
    RelatorioCampo,
    ProblemaRelatorio,
    form=ProblemaRelatorioForm,
    extra=1,  # Começa com um campo vazio
    can_delete=True,
    can_delete_extra=True
)


class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        # Excluímos 'despesa' e 'responsavel_pagamento' porque serão preenchidos na view.
        # 'data_criacao' e 'data_atualizacao' são automáticas.
        fields = ['status_pagamento', 'valor_pago',
                  'comentario', 'comprovante_pagamento']
        widgets = {
            # Widget para número
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 150.75'}),
            'comentario': forms.Textarea(attrs={'rows': 4}),
            # 'comprovante_pagamento': forms.ClearableFileInput(), # Já é o padrão, mas para explicitar
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Aplica 'form-control' a maioria dos campos, exceto FileInput (comprovante)
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})

# NOVO FORMULÁRIO: Para upload de clientes em massa


class BulkClientUploadForm(forms.Form):
    csv_file = forms.FileField(
        label=_("Arquivo CSV de Clientes"),
        help_text=_("Faça o upload de um arquivo CSV com os dados dos clientes. "
                    "O arquivo deve ter as colunas: razao_social, cnpj_cpf, endereco, cidade, estado, cep, telefone, email, contato_principal, telefone_contato, email_contato."),
        # Valida a extensão do arquivo
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].widget.attrs.update({'class': 'form-control'})


# NOVO FORMULÁRIO: Para upload de equipamentos em massa
class BulkEquipmentUploadForm(forms.Form):
    csv_file = forms.FileField(
        label=_("Arquivo CSV de Equipamentos"),
        help_text=_("Faça o upload de um arquivo CSV com os dados dos equipamentos. "
                    "O arquivo deve ter as colunas: cliente_cnpj_cpf, nome, modelo, numero_serie, descricao, localizacao."),
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].widget.attrs.update({'class': 'form-control'})


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Sobrescreve o método de envio para usar nossa função auxiliar,
        garantindo que as credenciais do banco de dados sejam sempre usadas.
        """
        email_backend = get_email_backend()
        if not email_backend:
            print(
                f"Falha ao enviar e-mail para {to_email}: Nenhuma configuração de e-mail encontrada.")
            return

        subject = render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())

        body = render_to_string(email_template_name, context)
        html_content = render_to_string(html_email_template_name, context)

        # Usamos o e-mail configurado no banco como remetente
        from_email = email_backend.username

        email_message = EmailMultiAlternatives(
            subject, body, from_email, [to_email],
            connection=email_backend  # Força o uso da nossa conexão!
        )
        email_message.attach_alternative(html_content, 'text/html')

        try:
            email_message.send()
        except Exception as e:
            print(
                f"Erro ao enviar e-mail de redefinição de senha para {to_email}: {e}")


class ConfiguracaoEmailForm(forms.ModelForm):
    # Seu formulário de configuração de e-mail (sem alterações)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.input_type != 'hidden':
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = ConfiguracaoEmail
        fields = ['email_host', 'email_port',
                  'email_host_user', 'email_host_password']
        widgets = {
            'email_host_password': forms.PasswordInput(render_value=True),
        }


class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulário para editar os dados do Perfil de Usuário (incluindo dados bancários).
    """
    class Meta:
        model = PerfilUsuario
        fields = [
            'cpf_titular_conta', 'nome_titular_conta',
            'banco_codigo', 'banco_nome', 'tipo_conta', 'agencia',
            'numero_conta', 'digito_conta',
            'chave_pix_tipo', 'chave_pix_valor'
        ]
        labels = {
            'cpf_titular_conta': _('CPF do Titular da Conta'),
            'nome_titular_conta': _('Nome Completo do Titular'),
            'banco_codigo': _('Código do Banco'),
            'banco_nome': _('Nome do Banco'),
            'tipo_conta': _('Tipo de Conta'),
            'agencia': _('Número da Agência'),
            'numero_conta': _('Número da Conta'),
            'digito_conta': _('Dígito Verificador (Conta)'),
            'chave_pix_tipo': _('Tipo de Chave PIX'),
            'chave_pix_valor': _('Valor da Chave PIX'),
        }
        widgets = {
            'cpf_titular_conta': forms.TextInput(attrs={'placeholder': _('Ex: 123.456.789-00')}),
            'banco_codigo': forms.TextInput(attrs={'placeholder': _('Ex: 237')}),
            'agencia': forms.TextInput(attrs={'placeholder': _('Ex: 0001 ou 0001-0')}),
            'numero_conta': forms.TextInput(attrs={'placeholder': _('Ex: 12345678')}),
            'digito_conta': forms.TextInput(attrs={'placeholder': _('Ex: 9')}),
            'chave_pix_valor': forms.TextInput(attrs={'placeholder': _('Sua chave PIX')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Select)):
                field.widget.attrs.update({'class': 'form-control'})


class HorasRelatorioTecnicoForm(forms.ModelForm):
    class Meta:
        model = HorasRelatorioTecnico
        fields = ['tecnico', 'horas_normais',
                  'horas_extras_60', 'horas_extras_100', 'km_rodado']
        # --- CORREÇÃO AQUI ---
        # Define os widgets dos campos de horas como HiddenInput
        widgets = {
            'tecnico': forms.HiddenInput(),
            'horas_normais': forms.HiddenInput(),
            'horas_extras_60': forms.HiddenInput(),
            'horas_extras_100': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # O campo KM Rodado continua visível e com a classe de estilo
        self.fields['km_rodado'].widget.attrs.update(
            {'class': 'form-control form-control-sm'})


HorasRelatorioTecnicoFormSet = inlineformset_factory(
    RelatorioCampo,
    HorasRelatorioTecnico,
    form=HorasRelatorioTecnicoForm,
    extra=0,  # Não adiciona campos extras vazios por padrão
    can_delete=False,  # Não permite deletar entradas
)
