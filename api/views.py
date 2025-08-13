# api/views.py

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from django.utils import timezone
from datetime import datetime
from rest_framework.exceptions import PermissionDenied
import pytz

from servico_campo.models import (
    OrdemServico, RelatorioCampo, Despesa, DocumentoOS, RegistroPonto, Tecnico
)
from configuracoes.models import (
    TipoDocumento, CategoriaDespesa, FormaPagamento,
)
from .serializers import (
    DespesaCreateSerializer, OrdemServicoListSerializer,
    OrdemServicoDetailSerializer, RelatorioCampoSerializer,
    CategoriaDespesaSerializer, DespesaDetailSerializer,
    FormaPagamentoSerializer, DespesaListSerializer,
    DocumentoOSCreateSerializer, RegistroPontoSerializer,
    RegistroPontoCreateSerializer, RegistroPontoUpdateSerializer,
    TipoDocumentoSerializer, DocumentoOSSerializer,
    DocumentoOSUpdateSerializer
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
    View para os detalhes de uma OS específica, com consulta otimizada.
    """
    serializer_class = OrdemServicoDetailSerializer
    permission_classes = [IsAuthenticated]

    # --- CORREÇÃO DEFINITIVA ---
    # O método get_queryset nos dá mais controle para otimizar a consulta.
    def get_queryset(self):
        """
        Otimiza a consulta para incluir todos os dados relacionados necessários
        pelo serializer de uma só vez, evitando múltiplas chamadas ao banco.
        """
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
            'despesas__conta_a_pagar__responsavel_pagamento',  # A mágica está aqui!
            'equipe__usuario',
            'documentos',
            'relatorios_campo'
        ).all()


class RelatorioCampoCreateAPIView(generics.CreateAPIView):
    queryset = RelatorioCampo.objects.all()
    serializer_class = RelatorioCampoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Associa a OS e o usuário automaticamente
        ordem_servico = OrdemServico.objects.get(pk=self.kwargs['os_pk'])
        serializer.save(ordem_servico=ordem_servico,
                        usuario_criacao=self.request.user)

    pass

# View para criar uma nova Despesa


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
