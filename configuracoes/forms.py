# configuracoes/forms.py
from django import forms
from .models import TipoManutencao, TipoDocumento, FormaPagamento, CategoriaDespesa, PoliticaDespesa


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
