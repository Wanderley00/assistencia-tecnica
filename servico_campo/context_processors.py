# servico_campo/context_processors.py

from .models import Despesa, OrdemServico, ContaPagar, Notificacao


def pending_counts_processor(request):
    """
    Disponibiliza a contagem de itens pendentes para o menu em todas as páginas.
    """
    # Inicia o dicionário de contagens zerado
    counts = {
        'aprovar_despesas': 0,
        'aprovar_ordens': 0,
        'contas_a_pagar': 0,
    }

    # Dicionário para as notificações (NOVO)
    notifications_data = {
        'nao_lidas_count': 0,
        'lista_recente': [],
    }

    # Só executa as queries se o usuário estiver logado
    if request.user.is_authenticated:

        # 1. Contagem de Despesas Pendentes de Aprovação
        if request.user.has_perm('servico_campo.change_despesa'):
            counts['aprovar_despesas'] = Despesa.objects.filter(
                status_aprovacao='PENDENTE').count()

        # 2. Contagem de Ordens de Serviço Pendentes de Aprovação (apenas para o gestor logado)
        if request.user.has_perm('servico_campo.view_ordemservico'):
            counts['aprovar_ordens'] = OrdemServico.objects.filter(
                gestor_responsavel=request.user,
                status='PENDENTE_APROVACAO'
            ).count()

        # 3. Contagem de Contas a Pagar Pendentes
        if request.user.has_perm('servico_campo.view_contapagar'):
            counts['contas_a_pagar'] = ContaPagar.objects.filter(
                status_pagamento__in=['PENDENTE', 'EM_ANALISE']
            ).count()

        # --- LÓGICA DE NOTIFICAÇÕES ADICIONADA AQUI ---
        # 2. Busca todas as notificações do usuário logado
        todas_notificacoes = Notificacao.objects.filter(
            destinatario=request.user)

        # 3. Conta quantas delas ainda não foram lidas
        notifications_data['nao_lidas_count'] = todas_notificacoes.filter(
            lida=False).count()

        # 4. Pega as 5 mais recentes para exibir no dropdown
        notifications_data['lista_recente'] = todas_notificacoes.order_by(
            '-data_criacao')[:5]
        # --- FIM DA LÓGICA DE NOTIFICAÇÕES ---

    # 5. Retorna ambos os dicionários para o contexto
    return {
        'pending_counts': counts,
        'user_notifications': notifications_data,  # NOVO
    }
