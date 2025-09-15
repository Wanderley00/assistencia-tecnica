# servico_campo/context_processors.py

from .models import Despesa, OrdemServico, ContaPagar


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

    return {'pending_counts': counts}
