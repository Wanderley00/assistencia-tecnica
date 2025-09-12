# api/serializers.py

from django.core.files.base import ContentFile
import base64
import uuid
from django.contrib.auth.models import User
from servico_campo.models import FotoRelatorio

from rest_framework import serializers
from servico_campo.models import (
    OrdemServico, Cliente, Equipamento, RelatorioCampo, Despesa, MembroEquipe,
    DocumentoOS, RegistroPonto,  ProblemaRelatorio, HorasRelatorioTecnico,
    CategoriaProblema, SubcategoriaProblema
)
from configuracoes.models import (
    TipoDocumento, CategoriaDespesa, FormaPagamento, TipoRelatorio
)
import mimetypes

# --- SERIALIZERS DE APOIO (sem alterações) ---


class Base64ImageField(serializers.Field):
    """
    Um campo de serializer para lidar com uploads de imagem em base64.
    """

    # SUBSTITUA ESTE MÉTODO INTEIRO
    def to_internal_value(self, data):
        if data is None:
            return None

        # Verifica se o dado está no formato Data URI e extrai apenas o conteúdo Base64
        if ';base64,' in data:
            header, data = data.split(';base64,')

        try:
            # Tenta decodificar o base64
            decoded_file = base64.b64decode(data)
            # Gera um nome de arquivo aleatório para evitar conflitos
            file_name = f"{uuid.uuid4()}.png"
            return ContentFile(decoded_file, name=file_name)
        except (TypeError, ValueError):
            self.fail('invalid_image')


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


class TipoRelatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoRelatorio
        fields = ['id', 'nome']


class CategoriaDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDespesa
        fields = ['id', 'nome']


class FormaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = ['id', 'nome']


class ProblemaRelatorioSerializer(serializers.ModelSerializer):
    categoria = serializers.StringRelatedField()
    subcategoria = serializers.CharField(
        source='subcategoria.nome', read_only=True, allow_null=True)

    class Meta:
        model = ProblemaRelatorio
        fields = ['categoria', 'subcategoria',
                  'observacao', 'solucao_aplicada']


class HorasRelatorioTecnicoSerializer(serializers.ModelSerializer):
    tecnico = serializers.StringRelatedField()
    horas_normais_hhmm = serializers.SerializerMethodField()
    horas_extras_60_hhmm = serializers.SerializerMethodField()
    horas_extras_100_hhmm = serializers.SerializerMethodField()

    class Meta:
        model = HorasRelatorioTecnico
        fields = [
            'tecnico', 'horas_normais', 'horas_extras_60', 'horas_extras_100', 'km_rodado',
            'horas_normais_hhmm', 'horas_extras_60_hhmm', 'horas_extras_100_hhmm'
        ]

    def _decimal_to_hhmm(self, decimal_hours):
        from decimal import Decimal
        if decimal_hours is None:
            return "00:00"
        try:
            decimal_hours = Decimal(decimal_hours)
            hours = int(decimal_hours)
            minutes = int((decimal_hours - hours) * 60)
            return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            return "00:00"

    def get_horas_normais_hhmm(self, obj):
        return self._decimal_to_hhmm(obj.horas_normais)

    def get_horas_extras_60_hhmm(self, obj):
        return self._decimal_to_hhmm(obj.horas_extras_60)

    def get_horas_extras_100_hhmm(self, obj):
        return self._decimal_to_hhmm(obj.horas_extras_100)


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

    numero_os = serializers.CharField(
        source='ordem_servico.numero_os', read_only=True)
    titulo_os = serializers.CharField(
        source='ordem_servico.titulo_servico', read_only=True)

    class Meta:
        model = Despesa
        fields = [
            'id', 'descricao', 'valor', 'data_despesa', 'tecnico',
            # Adicionado 'comprovante_anexo' para consistência
            'local_despesa', 'is_adiantamento', 'comprovante_anexo',
            'categoria_despesa', 'tipo_pagamento', 'status_aprovacao',
            'aprovado_por', 'data_aprovacao', 'comentario_aprovacao',
            'status_pagamento', 'responsavel_pagamento', 'data_pagamento',
            'comentario_pagamento', 'ordem_servico', 'numero_os',
            'titulo_os',
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
    tipo_documento = TipoDocumentoSerializer(read_only=True)
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


# --- SERIALIZER DE LISTA DA OS ---
class OrdemServicoListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para a lista de Ordens de Serviço.
    """
    # --- CORREÇÃO APLICADA AQUI ---
    # Usa os serializers de objeto para consistência com o Flutter
    cliente = ClienteSerializer(read_only=True)
    equipamento = EquipamentoSerializer(read_only=True)
    # -----------------------------
    tecnico_responsavel = serializers.StringRelatedField(read_only=True)
    gestor_responsavel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero_os', 'titulo_servico', 'cliente',
            'equipamento', 'status', 'data_abertura', 'tecnico_responsavel',
            'gestor_responsavel'
        ]


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


class ProblemaRelatorioCreateSerializer(serializers.Serializer):
    # Define explicitamente os campos que esperamos receber do app
    categoria = serializers.IntegerField()
    # allow_null=True é importante caso o usuário não selecione uma subcategoria
    subcategoria = serializers.IntegerField(required=False, allow_null=True)
    observacao = serializers.CharField(allow_blank=True)
    solucao_aplicada = serializers.CharField(allow_blank=True)


class RelatorioCampoCreateSerializer(serializers.ModelSerializer):
    # Serializer para criar um novo Relatório de Campo.

    # 1. Declaramos os campos que vamos receber do Flutter, com os nomes exatos.
    #    'write_only=True' significa que eles servem apenas para a criação.
    problemas = ProblemaRelatorioCreateSerializer(
        many=True, required=False, write_only=True)
    horas = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False)
    assinatura_executante_data = Base64ImageField(
        required=False, allow_null=True, write_only=True)
    assinatura_cliente_data = Base64ImageField(
        required=False, allow_null=True, write_only=True)

    class Meta:
        model = RelatorioCampo
        # 2. A lista de fields contém os campos do modelo que recebem dados simples.
        #    As assinaturas e os dados aninhados serão tratados no método 'create'.
        fields = [
            'data_relatorio',
            'tipo_relatorio',
            'descricao_atividades',
            'material_utilizado',
            'observacoes_adicionais',
            'local_servico',
            'problemas',
            'horas',
            'assinatura_executante_data',
            'assinatura_cliente_data',
        ]

    def create(self, validated_data):
        """
        Este método agora controla explicitamente todo o processo de criação.
        """
        # 3. Removemos os dados especiais do dicionário principal.
        #    Neste ponto, 'assinatura_executante_data' já foi processado pelo
        #    Base64ImageField e agora é um objeto de arquivo (ContentFile).
        problemas_data = validated_data.pop('problemas', [])
        horas_data = validated_data.pop('horas', [])
        assinatura_exec_file = validated_data.pop(
            'assinatura_executante_data', None)
        assinatura_cliente_file = validated_data.pop(
            'assinatura_cliente_data', None)

        # Pega a OS e o usuário do contexto que a View vai fornecer.
        ordem_servico = self.context['ordem_servico']
        tecnico = self.context['request'].user

        # 4. Cria o objeto RelatorioCampo, passando os arquivos de assinatura
        #    explicitamente para os campos corretos do modelo.
        relatorio = RelatorioCampo.objects.create(
            ordem_servico=ordem_servico,
            tecnico=tecnico,
            assinatura_executante=assinatura_exec_file,
            assinatura_cliente=assinatura_cliente_file,
            **validated_data
        )

        # 5. O resto da lógica para salvar problemas e horas (que já está correta).
        for problema_data in problemas_data:
            if problema_data.get('categoria'):
                problema_data['categoria_id'] = problema_data.pop('categoria')
                if 'subcategoria' in problema_data and problema_data['subcategoria']:
                    problema_data['subcategoria_id'] = problema_data.pop(
                        'subcategoria')
                ProblemaRelatorio.objects.create(
                    relatorio=relatorio, **problema_data)

        for hora_data in horas_data:
            tecnico_username = hora_data.pop('tecnico', None)
            try:
                tecnico_user = User.objects.get(username=tecnico_username)
                HorasRelatorioTecnico.objects.create(
                    relatorio=relatorio,
                    tecnico=tecnico_user,
                    **hora_data
                )
            except User.DoesNotExist:
                print(
                    f"AVISO: Usuário técnico '{tecnico_username}' não encontrado.")

        return relatorio


class SubcategoriaProblemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubcategoriaProblema
        fields = ['id', 'nome']


class CategoriaProblemaSerializer(serializers.ModelSerializer):
    # 'subcategorias' é o related_name no modelo SubcategoriaProblema
    subcategorias = SubcategoriaProblemaSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriaProblema
        fields = ['id', 'nome', 'subcategorias']


class FotoRelatorioSerializer(serializers.ModelSerializer):
    """ Serializer para exibir os detalhes de uma foto, agora com a URL completa. """

    # 1. Novo campo para a URL completa da imagem.
    imagem_url = serializers.SerializerMethodField()

    class Meta:
        model = FotoRelatorio
        # 2. 'imagem' é o campo do ficheiro, 'imagem_url' é o que o app irá usar.
        fields = ['id', 'imagem', 'imagem_url', 'descricao']
        # 'imagem' não precisa de ser read_only
        read_only_fields = ['id', 'imagem_url']

    # 3. Método que constrói a URL completa.
    def get_imagem_url(self, obj):
        request = self.context.get('request')
        if obj.imagem and request:
            return request.build_absolute_uri(obj.imagem.url)
        return None


class RelatorioCampoSerializer(serializers.ModelSerializer):
    tipo_relatorio = TipoRelatorioSerializer(read_only=True)
    problemas = ProblemaRelatorioSerializer(
        source='problemas_identificados_detalhes', many=True, read_only=True)
    horas = HorasRelatorioTecnicoSerializer(
        source='horas_por_tecnico', many=True, read_only=True)
    tecnico = serializers.StringRelatedField(read_only=True)

    # --- INÍCIO DA CORREÇÃO ---
    # 1. Adiciona o campo para serializar a lista de fotos.
    #    O 'source' usa o 'related_name' do seu modelo FotoRelatorio.
    fotos = FotoRelatorioSerializer(many=True, read_only=True)
    # --- FIM DA CORREÇÃO ---

    class Meta:
        model = RelatorioCampo
        # 2. Adiciona 'fotos' à lista de campos a serem incluídos.
        fields = [
            'id',
            'tipo_relatorio',
            'data_relatorio',
            'tecnico',
            'descricao_atividades',
            'material_utilizado',
            'observacoes_adicionais',
            'local_servico',
            'problemas',
            'horas',
            'fotos'  # <-- Campo adicionado
        ]

# --- SERIALIZER DE DETALHE DA OS (ATUALIZADO) ---


class RelatorioCampoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para ATUALIZAR um RelatorioCampo existente, com tratamento explícito de todos os campos.
    """
    problemas = ProblemaRelatorioCreateSerializer(many=True, required=False)
    horas = serializers.ListField(
        child=serializers.DictField(), required=False)

    # Os campos de assinatura continuam a usar a fonte correta do payload
    assinatura_executante_data = Base64ImageField(
        required=False, allow_null=True)
    assinatura_cliente_data = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = RelatorioCampo
        fields = [
            'tipo_relatorio', 'data_relatorio', 'descricao_atividades',
            'material_utilizado', 'observacoes_adicionais', 'local_servico',
            'problemas', 'horas',
            # A lista de fields também usa o nome com '_data'
            'assinatura_executante_data', 'assinatura_cliente_data'
        ]

    def update(self, instance, validated_data):
        # 1. Removemos os dados das assinaturas do dicionário.
        #    A chave em validated_data agora é 'assinatura_executante_data'.
        #    O valor será um ContentFile (se houver assinatura) ou None (se o app enviou nulo).
        assinatura_exec_file = validated_data.pop(
            'assinatura_executante_data', None)
        assinatura_cliente_file = validated_data.pop(
            'assinatura_cliente_data', None)

        # 2. Atribuímos o resultado diretamente ao campo do modelo (que NÃO tem '_data').
        #    Isto lida com ambos os casos de forma explícita:
        #    - Se houver assinatura, salva o novo arquivo, sobrescrevendo o antigo.
        #    - Se não houver (app enviou nulo), salva None, limpando o campo.
        instance.assinatura_executante = assinatura_exec_file
        instance.assinatura_cliente = assinatura_cliente_file

        # 3. Removemos os dados dos outros campos complexos.
        problemas_data = validated_data.pop('problemas', None)
        horas_data = validated_data.pop('horas', None)

        # 4. Deixamos o `super().update()` cuidar de todos os campos simples restantes.
        instance = super().update(instance, validated_data)

        # 5. Processamos os problemas e horas como antes.
        if problemas_data is not None:
            instance.problemas_identificados_detalhes.all().delete()
            for problema_data in problemas_data:
                if problema_data.get('categoria'):
                    problema_data['categoria_id'] = problema_data.pop(
                        'categoria')
                    if 'subcategoria' in problema_data and problema_data['subcategoria']:
                        problema_data['subcategoria_id'] = problema_data.pop(
                            'subcategoria')
                    ProblemaRelatorio.objects.create(
                        relatorio=instance, **problema_data)

        if horas_data is not None:
            instance.horas_por_tecnico.all().delete()
            for hora_data in horas_data:
                tecnico_username = hora_data.pop('tecnico')
                try:
                    tecnico_user = User.objects.get(username=tecnico_username)
                    HorasRelatorioTecnico.objects.create(
                        relatorio=instance, tecnico=tecnico_user, **hora_data)
                except User.DoesNotExist:
                    print(
                        f"AVISO: Usuário '{tecnico_username}' não encontrado ao atualizar horas.")

        # O super().update() já chamou o save(), mas como alteramos as assinaturas
        # manualmente, um save() final garante que tudo seja persistido.
        instance.save()
        return instance


class OrdemServicoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para a tela de detalhes da Ordem de Serviço.
    """
    # Relacionamentos que precisam de detalhes (objetos)
    cliente = ClienteSerializer(read_only=True)
    equipamento = EquipamentoSerializer(read_only=True)
    relatorios_campo = RelatorioCampoSerializer(many=True, read_only=True)
    despesas = DespesaDetailSerializer(many=True, read_only=True)
    equipe = MembroEquipeSerializer(many=True, read_only=True)
    documentos = DocumentoOSSerializer(many=True, read_only=True)
    pontos = RegistroPontoSerializer(
        many=True, read_only=True, source='registros_ponto')

    # Relacionamentos que podem ser apenas texto (String)
    tecnico_responsavel = serializers.StringRelatedField(read_only=True)
    gestor_responsavel = serializers.StringRelatedField(read_only=True)
    tipo_manutencao = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OrdemServico
        fields = '__all__'


class RelatorioCampoDetailSerializer(serializers.ModelSerializer):
    """ Serializer para exibir todos os detalhes de um Relatório de Campo. """
    tipo_relatorio = TipoRelatorioSerializer(read_only=True)
    tecnico = serializers.StringRelatedField(read_only=True)
    problemas = ProblemaRelatorioSerializer(
        source='problemas_identificados_detalhes', many=True, read_only=True)
    horas = HorasRelatorioTecnicoSerializer(
        source='horas_por_tecnico', many=True, read_only=True)
    # Usa o novo FotoRelatorioSerializer para a lista de fotos
    fotos = FotoRelatorioSerializer(many=True, read_only=True)

    class Meta:
        model = RelatorioCampo
        fields = [
            'id', 'tipo_relatorio', 'data_relatorio', 'tecnico',
            'descricao_atividades', 'material_utilizado', 'observacoes_adicionais',
            'problemas', 'horas', 'fotos'  # Adiciona o campo 'fotos'
        ]


class OrdemServicoConclusaoSerializer(serializers.Serializer):
    """
    Serializer para validar os dados da conclusão de uma Ordem de Serviço.
    """
    assinatura_executante_data = Base64ImageField(
        required=True, allow_null=False)
    assinatura_cliente_data = Base64ImageField(required=True, allow_null=False)
