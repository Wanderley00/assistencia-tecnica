# configuracoes/forms.py
from django import forms
from .models import TipoManutencao, TipoDocumento, FormaPagamento, CategoriaDespesa, PoliticaDespesa, ConfiguracaoEmail, TipoRelatorio


class TipoManutencaoForm(forms.ModelForm):
    class Meta:
        model = TipoManutencao
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Corretiva, Preventiva'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})


class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Desenho Técnico, Manual'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})


class FormaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FormaPagamento
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Dinheiro, PIX, Cartão de Crédito'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})


# NOVO FORMULÁRIO: CategoriaDespesaForm
class CategoriaDespesaForm(forms.ModelForm):
    class Meta:
        model = CategoriaDespesa
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': ('Ex: Refeição, Hotel, Material')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})


class PoliticaDespesaForm(forms.ModelForm):
    class Meta:
        model = PoliticaDespesa
        fields = '__all__'
        widgets = {
            'arquivo': forms.FileInput(),  # Certifica que é um FileInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativa'].widget.attrs.update({'class': 'form-check-input'})
        # O campo 'arquivo' é FileInput e não precisa de 'form-control'


class ConfiguracaoEmailForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoEmail
        fields = '__all__'
        widgets = {
            # Campo de senha
            'email_host_password': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.PasswordInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})


class ConfiguracaoEmailForm(forms.ModelForm):
    # Este método mágico aplica a classe a todos os campos
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Não aplica a classe a campos escondidos ou botões
            if field.widget.input_type != 'hidden':
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = ConfiguracaoEmail
        fields = ['email_host', 'email_port',
                  'email_host_user', 'email_host_password']
        widgets = {
            'email_host_password': forms.PasswordInput(render_value=True),
        }


class TipoRelatorioForm(forms.ModelForm):
    class Meta:
        model = TipoRelatorio
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Relatório Fotográfico, Medição de Obra'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['ativo'].widget.attrs.update({'class': 'form-check-input'})
