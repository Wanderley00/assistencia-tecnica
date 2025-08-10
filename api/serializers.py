# api/serializers.py

from rest_framework import serializers
from servico_campo.models import (
    OrdemServico, Cliente, Equipamento, RelatorioCampo, Despesa, MembroEquipe,
    DocumentoOS, RegistroPonto, Tecnico, Gestor
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


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ['id', 'nome']


class RelatorioCampoSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RelatorioCampo
        fields = ['id', 'ordem_servico', 'descricao_atividades',
                  'solucoes_aplicadas', 'material_utilizado', 'data_relatorio', 'tecnico']
        read_only_fields = ['ordem_servico']


class CategoriaDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDespesa
        fields = ['id', 'nome']


class FormaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = ['id', 'nome']


class GestorSerializer(serializers.ModelSerializer):
    nome_completo = serializers.CharField(
        source='user.first_name', read_only=True)

    class Meta:
        model = Gestor
        fields = ['id', 'nome_completo']


class DespesaSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField(read_only=True)
    categoria_despesa = CategoriaDespesaSerializer(read_only=True)
    tipo_pagamento = FormaPagamentoSerializer(
        source='forma_pagamento', read_only=True)
    aprovado_por = GestorSerializer(read_only=True)

    class Meta:
        model = Despesa
        fields = [
            'id',
            'ordem_servico',
            'descricao',
            'valor',
            'data_despesa',
            'tecnico',
            'categoria_despesa',
            'tipo_pagamento',  # Adicionado: Forma de pagamento
            'is_adiantamento',
            'local_despesa',
            'status_aprovacao',
            'data_aprovacao',
            'comentario_aprovacao',
            'paga',  # Adicionado: Status do Pagamento
            'data_pagamento',  # Adicionado: Data do Pagamento
            'aprovado_por',  # Adicionado: Aprovado por
            # O campo 'responsável pelo pagamento' não existe no modelo Despesa
            # Você deve usar o campo 'aprovado_por' para isso, ou criar um novo no seu modelo.
        ]
        read_only_fields = ['ordem_servico']


class DespesaCreateSerializer(serializers.ModelSerializer):
    categoria_despesa = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaDespesa.objects.all())
    tipo_pagamento = serializers.PrimaryKeyRelatedField(
        queryset=FormaPagamento.objects.all(), source='forma_pagamento')

    class Meta:
        model = Despesa
        fields = ['data_despesa', 'valor', 'categoria_despesa', 'descricao',
                  'local_despesa', 'tipo_pagamento', 'is_adiantamento', 'comprovante_anexo']


class MembroEquipeSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = MembroEquipe
        fields = ['usuario', 'funcao']


class DocumentoOSSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.StringRelatedField()
    uploaded_by = serializers.StringRelatedField()
    arquivo_url = serializers.SerializerMethodField()
    mime_type = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoOS
        fields = [
            'id', 'titulo', 'tipo_documento', 'arquivo',
            'arquivo_url', 'mime_type', 'data_upload', 'uploaded_by'
        ]
        read_only_fields = ['arquivo_url',
                            'mime_type', 'data_upload', 'uploaded_by']

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if obj.arquivo and request:
            return request.build_absolute_uri(obj.arquivo.url)
        return None

    def get_mime_type(self, obj):
        if obj.arquivo:
            mime_type, _ = mimetypes.guess_type(obj.arquivo.name)
            return mime_type
        return None


class OrdemServicoDetailSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    equipamento = EquipamentoSerializer(read_only=True)
    tecnico_responsavel = serializers.StringRelatedField(read_only=True)
    gestor_responsavel = serializers.StringRelatedField(read_only=True)
    tipo_manutencao = serializers.StringRelatedField(read_only=True)
    relatorios_campo = RelatorioCampoSerializer(many=True, read_only=True)
    despesas = DespesaSerializer(many=True, read_only=True)
    equipe = MembroEquipeSerializer(many=True, read_only=True)
    documentos = DocumentoOSSerializer(many=True, read_only=True)

    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero_os', 'titulo_servico', 'descricao_problema', 'cliente',
            'equipamento', 'status', 'data_abertura', 'tecnico_responsavel',
            'gestor_responsavel', 'observacoes_gerais', 'data_inicio_planejado',
            'data_inicio_real', 'data_previsao_conclusao', 'data_fechamento',
            'tipo_manutencao', 'relatorios_campo', 'despesas', 'equipe', 'documentos'
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


class DocumentoOSCreateSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all())

    class Meta:
        model = DocumentoOS
        fields = ['titulo', 'tipo_documento', 'arquivo', 'descricao']


class RegistroPontoSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField()
    duracao_formatada = serializers.CharField(read_only=True)

    class Meta:
        model = RegistroPonto
        fields = [
            'id', 'tecnico', 'data', 'hora_entrada', 'hora_saida',
            'duracao_formatada', 'observacoes', 'observacoes_entrada',
        ]


class RegistroPontoCreateSerializer(serializers.ModelSerializer):
    data = serializers.DateField(write_only=True)
    hora_entrada = serializers.TimeField(write_only=True)

    class Meta:
        model = RegistroPonto
        fields = ['data', 'hora_entrada', 'observacoes_entrada', 'localizacao']


class RegistroPontoUpdateSerializer(serializers.ModelSerializer):
    hora_saida = serializers.TimeField(write_only=True)

    class Meta:
        model = RegistroPonto
        fields = ['hora_saida', 'observacoes', 'localizacao_saida']
