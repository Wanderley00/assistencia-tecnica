# api/serializers.py

from rest_framework import serializers
from servico_campo.models import (
    OrdemServico, Cliente, Equipamento, RelatorioCampo, Despesa, MembroEquipe,
    DocumentoOS, RegistroPonto
)
from configuracoes.models import (
    TipoDocumento, CategoriaDespesa, FormaPagamento,
)
import mimetypes

# --- SERIALIZERS DE APOIO (sem alterações) ---


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


class CategoriaDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDespesa
        fields = ['id', 'nome']


class FormaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = ['id', 'nome']


class RelatorioCampoSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RelatorioCampo
        fields = ['id', 'ordem_servico', 'descricao_atividades',
                  'solucoes_aplicadas', 'material_utilizado', 'data_relatorio', 'tecnico']
        read_only_fields = ['ordem_servico']


# --- ALTERAÇÃO 1: Renomeando o serializer resumido ---
# Este será usado apenas para listas onde não precisamos de detalhes.
class DespesaListSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Despesa
        fields = ['id', 'ordem_servico', 'descricao',
                  'valor', 'data_despesa', 'tecnico']
        read_only_fields = ['ordem_servico']


# --- ADIÇÃO: O novo serializer com TODOS os detalhes da despesa ---
class DespesaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo e definitivo para a tela de detalhes da Despesa.
    """
    # Agora podemos buscar os dados de forma mais direta, pois a View já os otimizou.
    tecnico = serializers.StringRelatedField(read_only=True)
    categoria_despesa = CategoriaDespesaSerializer(read_only=True)
    tipo_pagamento = FormaPagamentoSerializer(read_only=True)
    aprovado_por = serializers.StringRelatedField(read_only=True)

    # --- CORREÇÃO FINAL ---
    # Usando 'source' para buscar os dados que já foram pré-carregados pela View.
    status_pagamento = serializers.CharField(
        source='conta_a_pagar.status_pagamento', read_only=True, allow_null=True)
    responsavel_pagamento = serializers.StringRelatedField(
        source='conta_a_pagar.responsavel_pagamento', read_only=True, allow_null=True)
    comentario_pagamento = serializers.CharField(
        source='conta_a_pagar.comentario', read_only=True, allow_null=True)

    # O campo data_pagamento já está no modelo Despesa, então não precisa de source.
    data_pagamento = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Despesa
        fields = [
            'id', 'descricao', 'valor', 'data_despesa', 'tecnico',
            # Adicionado 'comprovante_anexo' para consistência
            'local_despesa', 'is_adiantamento', 'comprovante_anexo',
            'categoria_despesa', 'tipo_pagamento', 'status_aprovacao',
            'aprovado_por', 'data_aprovacao', 'comentario_aprovacao',
            'status_pagamento', 'responsavel_pagamento', 'data_pagamento',
            'comentario_pagamento',
        ]

    def get_tecnico(self, obj):
        if obj.tecnico:
            return obj.tecnico.username
        return None

    def get_comprovante_url(self, obj):
        request = self.context.get('request')
        if obj.comprovante_anexo and hasattr(obj.comprovante_anexo, 'url'):
            return request.build_absolute_uri(obj.comprovante_anexo.url)
        return None

    # --- LÓGICA CORRIGIDA E FINAL ---
    # Este bloco tenta acessar 'obj.conta_a_pagar'. Se não encontrar o objeto
    # relacionado no banco de dados, ele retorna um valor padrão sem quebrar.

    def get_status_pagamento(self, obj):
        try:
            return obj.conta_a_pagar.status_pagamento
        except Despesa.conta_a_pagar.RelatedObjectDoesNotExist:
            return 'PENDENTE'

    def get_responsavel_pagamento(self, obj):
        try:
            if obj.conta_a_pagar.responsavel_pagamento:
                return obj.conta_a_pagar.responsavel_pagamento.username
            return None
        except Despesa.conta_a_pagar.RelatedObjectDoesNotExist:
            return None

    def get_comentario_pagamento(self, obj):
        try:
            return obj.conta_a_pagar.comentario
        except Despesa.conta_a_pagar.RelatedObjectDoesNotExist:
            return None

# --------------------------------------------------------------------


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
        read_only_fields = ['arquivo_url', 'mime_type',
                            'data_upload', 'uploaded_by']

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


class DocumentoOSCreateSerializer(serializers.ModelSerializer):
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

    # --- ALTERAÇÃO 2: Usar o novo serializer de DETALHES da despesa ---
    despesas = DespesaDetailSerializer(many=True, read_only=True)
    # --------------------------------------------------------------

    equipe = MembroEquipeSerializer(many=True, read_only=True)
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
            'relatorios_campo', 'despesas', 'equipe', 'documentos'
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

# ... (O resto do arquivo com os serializers de Create e Ponto permanece inalterado)


class DespesaCreateSerializer(serializers.ModelSerializer):
    categoria_despesa = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaDespesa.objects.filter(ativo=True)
    )
    tipo_pagamento = serializers.PrimaryKeyRelatedField(
        queryset=FormaPagamento.objects.filter(ativo=True)
    )

    class Meta:
        model = Despesa
        fields = [
            'data_despesa', 'valor', 'categoria_despesa', 'descricao',
            'local_despesa', 'tipo_pagamento', 'is_adiantamento',
            'comprovante_anexo'
        ]


class RegistroPontoSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField()
    duracao_formatada = serializers.CharField(read_only=True)

    class Meta:
        model = RegistroPonto
        fields = [
            'id', 'tecnico', 'data', 'hora_entrada',
            'hora_saida', 'duracao_formatada', 'observacoes',
            'observacoes_entrada',
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


class DocumentoOSUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para ATUALIZAR os metadados de um DocumentoOS existente.
    Não requer o campo 'arquivo'.
    """
    tipo_documento = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all()
    )

    class Meta:
        model = DocumentoOS
        fields = ['titulo', 'tipo_documento', 'descricao']
