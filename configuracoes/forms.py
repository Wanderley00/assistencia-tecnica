# configuracoes/forms.py
from django import forms
from .models import TipoManutencao, TipoDocumento, FormaPagamento


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
