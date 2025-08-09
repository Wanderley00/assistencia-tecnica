# api/serializers.py

from rest_framework import serializers
from servico_campo.models import (
    OrdemServico, Cliente, Equipamento, RelatorioCampo, Despesa, MembroEquipe,
    DocumentoOS, Despesa, RegistroPonto
)

from configuracoes.models import (
    TipoDocumento, CategoriaDespesa, FormaPagamento,
)

import mimetypes


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['razao_social']


class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        fields = ['nome', 'modelo']

# NOVO SERIALIZER PARA LISTAR OS TIPOS DE DOCUMENTO


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ['id', 'nome']

# --- NOVOS SERIALIZERS ---


class RelatorioCampoSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RelatorioCampo
        fields = ['id', 'ordem_servico', 'descricao_atividades',
                  'solucoes_aplicadas', 'material_utilizado', 'data_relatorio', 'tecnico']
        read_only_fields = ['ordem_servico']


class DespesaSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Despesa
        fields = ['id', 'ordem_servico', 'descricao',
                  'valor', 'data_despesa', 'tecnico']
        read_only_fields = ['ordem_servico']


class MembroEquipeSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = MembroEquipe
        fields = ['usuario', 'funcao']

# NOVO: Serializer para Documentos


# Altere o serializer de DocumentoOS para incluir o tipo do arquivo
class DocumentoOSSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.StringRelatedField()
    uploaded_by = serializers.StringRelatedField()
    arquivo_url = serializers.SerializerMethodField()
    mime_type = serializers.SerializerMethodField()  # NOVO CAMPO

    class Meta:
        model = DocumentoOS
        fields = [
            'id', 'titulo', 'tipo_documento', 'arquivo',
            'arquivo_url', 'mime_type', 'data_upload', 'uploaded_by'  # ADICIONE 'mime_type'
        ]
        read_only_fields = ['arquivo_url', 'mime_type',
                            'data_upload', 'uploaded_by']  # ADICIONE 'mime_type'

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if obj.arquivo and request:
            return request.build_absolute_uri(obj.arquivo.url)
        return None

    # NOVA FUNÇÃO para pegar o tipo do arquivo
    def get_mime_type(self, obj):
        if obj.arquivo:
            # Tenta adivinhar o tipo do arquivo pelo nome
            mime_type, _ = mimetypes.guess_type(obj.arquivo.name)
            return mime_type
        return None

# NOVO: Serializer para criar/fazer upload de Documentos


class DocumentoOSCreateSerializer(serializers.ModelSerializer):
    # Permite que o app envie o ID do tipo de documento
    tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all())

    class Meta:
        model = DocumentoOS
        fields = ['titulo', 'tipo_documento', 'arquivo', 'descricao']


# --- SERIALIZER DE DETALHE DA OS (ATUALIZADO) ---
class OrdemServicoDetailSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    equipamento = EquipamentoSerializer(read_only=True)
    tecnico_responsavel = serializers.StringRelatedField(read_only=True)
    gestor_responsavel = serializers.StringRelatedField(read_only=True)
    tipo_manutencao = serializers.StringRelatedField(read_only=True)

    relatorios_campo = RelatorioCampoSerializer(many=True, read_only=True)
    despesas = DespesaSerializer(many=True, read_only=True)
    equipe = MembroEquipeSerializer(many=True, read_only=True)
    # ADICIONADO: Usando o related_name 'documentos' do seu models.py
    documentos = DocumentoOSSerializer(many=True, read_only=True)

    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero_os', 'titulo_servico', 'descricao_problema', 'cliente',
            'equipamento', 'status', 'data_abertura', 'tecnico_responsavel',
            'gestor_responsavel', 'observacoes_gerais', 'data_inicio_planejado',
            'data_inicio_real',
            'data_previsao_conclusao',
            'data_fechamento',
            'tipo_manutencao',
            'relatorios_campo', 'despesas', 'equipe', 'documentos'  # Adicionado 'documentos'
        ]


class OrdemServicoListSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    equipamento = EquipamentoSerializer(read_only=True)
    tecnico_responsavel = serializers.StringRelatedField(read_only=True)
    gestor_responsavel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero_os', 'titulo_servico', 'descricao_problema', 'cliente',
            'equipamento', 'status', 'data_abertura', 'tecnico_responsavel',
            'gestor_responsavel'
        ]

# --- NOVOS SERIALIZERS PARA OS DROPDOWNS ---


class CategoriaDespesaSerializer(serializers.ModelSerializer):
    """
    Serializer para listar as categorias de despesa.
    """
    class Meta:
        model = CategoriaDespesa
        fields = ['id', 'nome']


class FormaPagamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para listar as formas de pagamento.
    """
    class Meta:
        model = FormaPagamento
        fields = ['id', 'nome']


# --- NOVO SERIALIZER PARA CRIAR DESPESAS ---

class DespesaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para receber os dados do app e criar uma nova despesa.
    """
    # Permite que o app envie o ID da categoria e da forma de pagamento
    categoria_despesa = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaDespesa.objects.filter(ativo=True)
    )
    tipo_pagamento = serializers.PrimaryKeyRelatedField(
        queryset=FormaPagamento.objects.filter(ativo=True)
    )

    class Meta:
        model = Despesa
        # Lista de campos que o app irá enviar
        fields = [
            'data_despesa',
            'valor',
            'categoria_despesa',
            'descricao',
            'local_despesa',
            'tipo_pagamento',
            'is_adiantamento',
            'comprovante_anexo'
        ]

# --- NOVOS SERIALIZERS PARA REGISTRO DE PONTO ---


class RegistroPontoSerializer(serializers.ModelSerializer):
    """ Serializer para listar os pontos já registrados. """
    tecnico = serializers.StringRelatedField()
    # Pega o valor da propriedade 'duracao_formatada' do seu model
    duracao_formatada = serializers.CharField(read_only=True)

    class Meta:
        model = RegistroPonto
        fields = [
            'id',
            'tecnico',
            'data',
            'hora_entrada',
            'hora_saida',
            'duracao_formatada',
            'observacoes',  # Este campo terá as observações de entrada e saída juntas
            # Usado apenas para exibir a obs. de entrada isoladamente se necessário
            'observacoes_entrada',
        ]


class RegistroPontoCreateSerializer(serializers.ModelSerializer):
    """ Serializer para criar um novo ponto (marcar entrada). """
    # Adicionando campos para receber data e hora do app
    data = serializers.DateField(write_only=True)
    hora_entrada = serializers.TimeField(write_only=True)

    class Meta:
        model = RegistroPonto
        # Atualize os fields para incluir os novos campos
        fields = ['data', 'hora_entrada', 'observacoes_entrada', 'localizacao']


class RegistroPontoUpdateSerializer(serializers.ModelSerializer):
    """ Serializer para atualizar um ponto (marcar saída). """
    # Adicionando campo para receber a hora de saída do app
    hora_saida = serializers.TimeField(write_only=True)

    class Meta:
        model = RegistroPonto
        # Atualize os fields para incluir o novo campo
        fields = ['hora_saida', 'observacoes', 'localizacao_saida']
