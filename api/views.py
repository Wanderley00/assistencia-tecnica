# api/views.py

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from django.utils import timezone
from datetime import datetime
from rest_framework.exceptions import PermissionDenied
import pytz
from django.contrib.auth.models import User

from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from rest_framework import status

from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
from .serializers import TipoRelatorioSerializer, HorasRelatorioTecnicoSerializer
from configuracoes.models import TipoRelatorio
from servico_campo.models import RegraJornadaTrabalho

from servico_campo.models import (
    OrdemServico, RelatorioCampo, Despesa, DocumentoOS, RegistroPonto, Tecnico,
    HorasRelatorioTecnico, RegraJornadaTrabalho, ProblemaRelatorio, CategoriaProblema,
    FotoRelatorio
)
from configuracoes.models import (
    TipoDocumento, CategoriaDespesa, FormaPagamento, TipoRelatorio
)
from .serializers import (
    DespesaCreateSerializer, OrdemServicoListSerializer,
    OrdemServicoDetailSerializer, RelatorioCampoSerializer,
    CategoriaDespesaSerializer, DespesaDetailSerializer,
    FormaPagamentoSerializer, DespesaListSerializer,
    DocumentoOSCreateSerializer, RegistroPontoSerializer,
    RegistroPontoCreateSerializer, RegistroPontoUpdateSerializer,
    TipoDocumentoSerializer, DocumentoOSSerializer,
    DocumentoOSUpdateSerializer, TipoRelatorioSerializer,
    HorasRelatorioTecnicoSerializer, RelatorioCampoCreateSerializer,
    CategoriaProblemaSerializer, FotoRelatorioSerializer,
    RelatorioCampoDetailSerializer, RelatorioCampoUpdateSerializer,
    OrdemServicoConclusaoSerializer
)

from rest_framework.permissions import IsAuthenticated

# View da lista principal (agora usa o ListSerializer)


class DespesaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    # Sobrescrevemos este método para escolher o serializer correto
    def get_serializer_class(self):
        if self.action in ['create']:
            return DespesaCreateSerializer
        return DespesaListSerializer

    def get_queryset(self):
        try:
            tecnico = Tecnico.objects.get(user=self.request.user)
            return Despesa.objects.filter(tecnico=tecnico).order_by('-data_despesa')
        except Tecnico.DoesNotExist:
            return Despesa.objects.none()

    # O método perform_create ainda é necessário para associar o técnico
    def perform_create(self, serializer):
        tecnico = Tecnico.objects.get(user=self.request.user)
        serializer.save(tecnico=tecnico)


class DespesaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Permite ver, atualizar ou deletar uma despesa específica.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DespesaDetailSerializer  # Usando o serializer de detalhe

    def get_queryset(self):
        """
        A Lógica de permissão foi movida para cá.
        Esta função garante que o usuário só pode acessar despesas de Ordens de Serviço
        às quais ele está associado (como técnico, equipe ou gestor).
        """
        user = self.request.user

        # 1. Encontra todas as OS que o usuário logado pode acessar
        accessible_os_ids = OrdemServico.objects.filter(
            Q(tecnico_responsavel=user) |
            Q(equipe__usuario=user) |
            Q(gestor_responsavel=user)
        ).values_list('id', flat=True).distinct()

        # 2. Retorna apenas as despesas que pertencem a essas OS acessíveis
        return Despesa.objects.filter(ordem_servico_id__in=accessible_os_ids)


class DespesaCreateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Despesa.objects.all()
    serializer_class = DespesaCreateSerializer

    def perform_create(self, serializer):
        tecnico = Tecnico.objects.get(user=self.request.user)
        serializer.save(tecnico=tecnico)


class OrdemServicoListAPIView(generics.ListAPIView):
    serializer_class = OrdemServicoListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = OrdemServico.objects.filter(
            Q(tecnico_responsavel=user) | Q(equipe__usuario=user)
        ).select_related(
            'cliente', 'equipamento', 'tecnico_responsavel', 'gestor_responsavel'
        ).distinct()
        return queryset

# --- NOVAS VIEWS ---

# View para os detalhes de uma OS específica


class OrdemServicoDetailAPIView(generics.RetrieveAPIView):
    """
    View para os detalhes de uma OS específica (COM DEBUG).
    """
    # FORÇA O USO DO SERIALIZER DE DETALHES
    serializer_class = OrdemServicoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A otimização de consulta que você já tem é ótima e pode permanecer
        return OrdemServico.objects.select_related(
            'cliente',
            'equipamento',
            'tipo_manutencao',
            'tecnico_responsavel',
            'gestor_responsavel'
        ).prefetch_related(
            'despesas__tecnico',
            'despesas__categoria_despesa',
            'despesas__tipo_pagamento',
            'despesas__aprovado_por',
            'despesas__conta_a_pagar__responsavel_pagamento',
            'equipe__usuario',
            'documentos',
            # Garante que os relacionamentos dos relatórios também sejam pré-carregados
            'relatorios_campo__tipo_relatorio',
            'relatorios_campo__problemas_identificados_detalhes',
            'relatorios_campo__horas_por_tecnico',
            'registros_ponto'
        ).all()

    def retrieve(self, request, *args, **kwargs):
        """
        Sobrescreve o método que busca os dados para adicionar um print de debug.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # --- PASSO DE DEBUG MAIS IMPORTANTE ---
        # Printa o JSON final que será enviado para o Flutter no console do Django
        # import json
        # print("\n--- DEBUG: JSON ENVIADO PARA O APP ---")
        # print(json.dumps(serializer.data, indent=2))
        # print("--- FIM DO DEBUG ---\n")
        # --- FIM DO DEBUG ---

        return super().retrieve(request, *args, **kwargs)


class RelatorioCampoCreateAPIView(generics.CreateAPIView):
    """
    Endpoint da API para criar um novo RelatorioCampo.
    """
    serializer_class = RelatorioCampoCreateSerializer
    permission_classes = [IsAuthenticated]

    # --- MÉTODO ADICIONADO PARA CORRIGIR O ERRO ---
    def get_serializer_context(self):
        """
        Este método passa informações extras (contexto) para o serializer.
        É aqui que adicionamos a 'ordem_servico' que faltava.
        """
        context = super().get_serializer_context()
        # Adiciona o objeto OrdemServico ao contexto, obtido a partir da URL
        context['ordem_servico'] = get_object_or_404(
            OrdemServico, pk=self.kwargs['os_pk'])
        return context

    # ADICIONAMOS ESTE MÉTODO 'create' PARA CAPTURAR O ERRO
    def create(self, request, *args, **kwargs):
        try:
            # Tenta executar o processo de criação padrão
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # Se a base de dados retornar um erro de integridade (por causa do 'unique_together'),
            # nós o capturamos e levantamos uma ValidationError do DRF com uma mensagem amigável.
            raise ValidationError({
                'detail': 'Já existe um relatório deste tipo para esta data. Não é permitido criar duplicatas.'
            })


class DespesaCreateAPIView(generics.CreateAPIView):
    """
    Cria uma nova despesa associada a uma Ordem de Serviço.
    """
    # Use o novo serializer que criamos
    serializer_class = DespesaCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Associa a OS e o técnico automaticamente
        ordem_servico = get_object_or_404(
            OrdemServico, pk=self.kwargs['os_pk'])
        serializer.save(
            ordem_servico=ordem_servico,
            tecnico=self.request.user
        )
    pass

# --- NOVAS VIEWS PARA OS DROPDOWNS ---


class CategoriaDespesaListAPIView(generics.ListAPIView):
    """
    Lista todas as categorias de despesa ativas.
    """
    serializer_class = CategoriaDespesaSerializer
    permission_classes = [IsAuthenticated]
    queryset = CategoriaDespesa.objects.filter(ativo=True)

    pass


class FormaPagamentoListAPIView(generics.ListAPIView):
    """
    Lista todas as formas de pagamento ativas.
    """
    serializer_class = FormaPagamentoSerializer
    permission_classes = [IsAuthenticated]
    queryset = FormaPagamento.objects.filter(ativo=True)

    pass


# View para LISTAR os Tipos de Documento para o app (CORRIGE O ERRO 404)


class TipoDocumentoListAPIView(generics.ListAPIView):
    """
    Lista todos os tipos de documento ativos para serem usados no app mobile.
    """
    serializer_class = TipoDocumentoSerializer
    permission_classes = [IsAuthenticated]
    queryset = TipoDocumento.objects.filter(ativo=True)

    pass


# View para CRIAR (fazer upload) de um novo DocumentoOS
class DocumentoOSCreateAPIView(generics.CreateAPIView):
    """
    Cria um novo documento associado a uma Ordem de Serviço específica.
    """
    serializer_class = DocumentoOSCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Associa a OS e o usuário que fez o upload automaticamente
        ordem_servico = get_object_or_404(
            OrdemServico, pk=self.kwargs['os_pk'])
        serializer.save(
            ordem_servico=ordem_servico,
            uploaded_by=self.request.user
        )

    pass


class DocumentoOSDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # O serializer padrão para GET (visualizar) continua o mesmo
    serializer_class = DocumentoOSSerializer

    # --- ADICIONE ESTE MÉTODO ---
    def get_serializer_class(self):
        # Se a requisição for PUT ou PATCH (edição), usa o novo serializer de update
        if self.request.method in ['PUT', 'PATCH']:
            return DocumentoOSUpdateSerializer
        # Para qualquer outra requisição (GET), usa o serializer padrão
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        accessible_os_ids = OrdemServico.objects.filter(
            Q(tecnico_responsavel=user) |
            Q(equipe__usuario=user) |
            Q(gestor_responsavel=user)
        ).values_list('id', flat=True).distinct()
        return DocumentoOS.objects.filter(ordem_servico_id__in=accessible_os_ids)

# --- NOVAS VIEWS PARA REGISTRO DE PONTO ---


class RegistroPontoListCreateAPIView(generics.ListCreateAPIView):
    """
    Lista os pontos de uma OS ou cria um novo (marca a entrada).
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Usa um serializer diferente para criar (POST) vs. listar (GET)
        if self.request.method == 'POST':
            return RegistroPontoCreateSerializer
        return RegistroPontoSerializer

    def get_queryset(self):
        # Filtra os pontos pela OS especificada na URL
        os_pk = self.kwargs['os_pk']
        return RegistroPonto.objects.filter(ordem_servico_id=os_pk).order_by('-data', '-hora_entrada')

    def perform_create(self, serializer):
        os = get_object_or_404(OrdemServico, pk=self.kwargs['os_pk'])

        # # Impede que um usuário abra um novo ponto se já tiver um em aberto para esta OS
        # open_entry = RegistroPonto.objects.filter(
        #     ordem_servico=os,
        #     tecnico=self.request.user,
        #     hora_saida__isnull=True
        # ).exists()
        # if open_entry:
        #     raise serializers.ValidationError(
        #         {"detail": "Já existe um ponto de entrada em aberto para esta OS."})

        # Salva o novo ponto com os dados automáticos
        is_first_entry = not RegistroPonto.objects.filter(
            ordem_servico=os).exists()

        # 2. Salva o novo registro de ponto
        serializer.save(
            ordem_servico=os,
            tecnico=self.request.user,
            data=serializer.validated_data['data'],
            hora_entrada=serializer.validated_data['hora_entrada'],
            observacoes_entrada=serializer.validated_data.get(
                'observacoes_entrada'),
            localizacao=serializer.validated_data.get('localizacao')
        )

        # 3. Se for o primeiro ponto, atualiza a OS
        if is_first_entry:
            os.status = 'EM_EXECUCAO'
            entry_date = serializer.validated_data['data']
            entry_time = serializer.validated_data['hora_entrada']

            # CORREÇÃO DEFINITIVA: Força o fuso horário de São Paulo
            naive_datetime = datetime.combine(entry_date, entry_time)
            sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
            aware_datetime = sao_paulo_tz.localize(naive_datetime)

            os.data_inicio_real = aware_datetime
            os.save()

    pass


class RegistroPontoUpdateAPIView(generics.UpdateAPIView):
    """
    Atualiza um registro de ponto, usado para marcar a saída.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RegistroPontoUpdateSerializer
    queryset = RegistroPonto.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        # Garante que o usuário só pode editar o seu próprio ponto
        if obj.tecnico != self.request.user:
            raise PermissionDenied(
                "Você não tem permissão para editar este ponto.")
        # Garante que o ponto não foi encerrado ainda
        if obj.hora_saida is not None:
            raise serializers.ValidationError("Este ponto já foi encerrado.")
        return obj

    def perform_update(self, serializer):
        # Concatena as observações de entrada e saída no campo principal 'observacoes'
        entry_obs = serializer.instance.observacoes_entrada or ""
        exit_obs = serializer.validated_data.get('observacoes', "")

        full_observation = f"Entrada: {entry_obs}".strip()
        if exit_obs:
            full_observation += f"\nSaída: {exit_obs}".strip()

        serializer.save(
            observacoes=full_observation.strip(),
            hora_saida=serializer.validated_data['hora_saida'],
            localizacao_saida=serializer.validated_data.get(
                'localizacao_saida')
        )
    pass


@api_view(['GET'])
def calcular_horas_relatorio_api(request, os_pk):
    """
    API para buscar dados iniciais para a tela de criação de relatório.
    Recebe uma data via query param (ex: ?data=2025-08-19) e retorna:
    1. A lista de Tipos de Relatório ativos.
    2. As horas calculadas para a data informada para cada técnico da OS.
    """
    # Pega a Ordem de Serviço ou retorna erro 404
    ordem_servico = get_object_or_404(OrdemServico, pk=os_pk)

    # Pega a data dos parâmetros da URL, se não houver, usa a data de hoje
    data_str = request.query_params.get('data')
    if data_str:
        try:
            data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = timezone.localdate()
    else:
        data_selecionada = timezone.localdate()

    # 1. Busca os Tipos de Relatório ativos
    tipos_relatorio_qs = TipoRelatorio.objects.filter(ativo=True)
    tipos_relatorio_serializer = TipoRelatorioSerializer(
        tipos_relatorio_qs, many=True)

    # 2. Calcula as horas para a data selecionada
    horas_calculadas_data = []
    regra_jornada = RegraJornadaTrabalho.objects.filter(
        is_default=True).first()

    if regra_jornada:
        # Coleta todos os técnicos da OS (responsável + equipe)
        tecnicos = {
            ordem_servico.tecnico_responsavel} if ordem_servico.tecnico_responsavel else set()
        for membro in ordem_servico.equipe.all():
            tecnicos.add(membro.usuario)

        for tecnico in tecnicos:
            if tecnico is None:
                continue

            pontos_do_dia = RegistroPonto.objects.filter(
                ordem_servico=ordem_servico,
                tecnico=tecnico,
                data=data_selecionada,
                hora_saida__isnull=False
            )

            horas_calculadas = {'horas_normais': Decimal('0.00'), 'horas_extras_60': Decimal(
                '0.00'), 'horas_extras_100': Decimal('0.00')}
            if pontos_do_dia.exists():
                horas_calculadas = regra_jornada.calcular_horas(
                    list(pontos_do_dia))

            # Cria uma instância em memória para usar o serializer
            # Isso garante que o formato do JSON seja o mesmo da tela de detalhes
            horas_obj = HorasRelatorioTecnico(
                tecnico=tecnico,
                km_rodado=0,  # KM é preenchido no app
                **horas_calculadas
            )

            serializer = HorasRelatorioTecnicoSerializer(horas_obj)
            horas_calculadas_data.append(serializer.data)

    # 3. Monta a resposta final
    response_data = {
        'tipos_relatorio': tipos_relatorio_serializer.data,
        'horas_calculadas': horas_calculadas_data,
    }

    return Response(response_data)


class CategoriaProblemaListAPIView(generics.ListAPIView):
    """
    Lista todas as Categorias de Problema ativas e suas subcategorias aninhadas.
    """
    serializer_class = CategoriaProblemaSerializer
    permission_classes = [IsAuthenticated]
    # prefetch_related é usado para otimizar a busca das subcategorias
    queryset = CategoriaProblema.objects.filter(
        ativo=True).prefetch_related('subcategorias')


class FotoRelatorioCreateAPIView(generics.CreateAPIView):
    """
    Endpoint da API para adicionar uma nova foto a um RelatorioCampo existente.
    """
    queryset = FotoRelatorio.objects.all()
    serializer_class = FotoRelatorioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Este método é chamado antes de guardar a nova foto.
        Usamo-lo para associar a foto ao relatório correto,
        pegando o ID do relatório a partir da URL.
        """
        # Pega o 'relatorio_pk' da URL (ex: /api/relatorios-campo/27/fotos/)
        relatorio_pk = self.kwargs.get('relatorio_pk')
        relatorio = get_object_or_404(RelatorioCampo, pk=relatorio_pk)

        # Guarda a nova foto, associando-a ao relatório encontrado.
        serializer.save(relatorio=relatorio)


# Mude para RetrieveUpdateAPIView
class RelatorioCampoDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    Endpoint da API para buscar (GET) ou atualizar (PUT/PATCH) os detalhes
    de um único Relatório de Campo.
    """
    queryset = RelatorioCampo.objects.all()
    permission_classes = [IsAuthenticated]

    # Usa um serializer diferente para ler (GET) e para escrever (PUT)
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RelatorioCampoUpdateSerializer
        return RelatorioCampoDetailSerializer


class TipoRelatorioListView(generics.ListAPIView):
    """
    Endpoint que retorna uma lista de todos os Tipos de Relatório ativos.
    """
    queryset = TipoRelatorio.objects.filter(ativo=True).order_by('nome')
    serializer_class = TipoRelatorioSerializer
    permission_classes = [IsAuthenticated]


class ConcluirOrdemServicoAPIView(APIView):
    """
    Endpoint para marcar uma Ordem de Serviço como 'CONCLUIDA' e
    salvar as assinaturas de conclusão.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, os_pk, format=None):
        os = get_object_or_404(OrdemServico, pk=os_pk)

        # Valida os dados recebidos (as assinaturas)
        serializer = OrdemServicoConclusaoSerializer(data=request.data)
        if serializer.is_valid():
            # Pega os arquivos de imagem convertidos pelo Base64ImageField
            assinatura_exec_file = serializer.validated_data['assinatura_executante_data']
            assinatura_cliente_file = serializer.validated_data['assinatura_cliente_data']

            # Atualiza a Ordem de Serviço
            os.status = 'CONCLUIDA'  # Ou o nome do status que você usa
            os.data_fechamento = timezone.now()
            os.assinatura_executante_conclusao = assinatura_exec_file
            os.assinatura_cliente_conclusao = assinatura_cliente_file
            os.save()

            # Retorna uma resposta de sucesso
            return Response(
                {"detail": "Ordem de Serviço concluída com sucesso!"},
                status=status.HTTP_200_OK
            )

        # Se os dados não forem válidos, retorna os erros
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MinhasDespesasListView(generics.ListAPIView):
    """
    Endpoint que retorna uma lista detalhada de todas as despesas
    associadas ao técnico (usuário) que está fazendo a requisição.
    """
    permission_classes = [IsAuthenticated]
    # Reutilizamos o serializer de detalhes
    serializer_class = DespesaDetailSerializer

    def get_queryset(self):
        """
        Esta função é o coração da funcionalidade: ela filtra as despesas
        pelo 'tecnico' que é o usuário logado (self.request.user).
        """
        return Despesa.objects.filter(tecnico=self.request.user).order_by('-data_despesa')
