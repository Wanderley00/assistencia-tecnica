# servico_campo/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal

from .models import RegistroPonto, RelatorioCampo, HorasRelatorioTecnico, RegraJornadaTrabalho


@receiver([post_save, post_delete], sender=RegistroPonto)
def recalcular_horas_relatorio(sender, instance, **kwargs):
    """
    Este sinal é acionado sempre que um RegistroPonto é salvo ou deletado.
    Ele recalcula e atualiza as horas em qualquer relatório existente para a data correspondente.
    """
    ordem_servico = instance.ordem_servico
    data_ponto = instance.data
    tecnico = instance.tecnico

    # 1. Verifica se existe um relatório para esta OS nesta data
    relatorio_existente = RelatorioCampo.objects.filter(
        ordem_servico=ordem_servico,
        data_relatorio=data_ponto
    ).first()

    # Se não houver relatório, não há nada a fazer.
    if not relatorio_existente:
        return

    # 2. Se existe um relatório, busca o registro de horas para o técnico específico
    horas_tecnico_relatorio, created = HorasRelatorioTecnico.objects.get_or_create(
        relatorio=relatorio_existente,
        tecnico=tecnico
    )

    # 3. Busca a regra de jornada de trabalho padrão para fazer o cálculo
    regra_jornada = RegraJornadaTrabalho.objects.filter(
        is_default=True).first()
    if not regra_jornada:
        print(
            f"AVISO: Nenhuma regra de jornada de trabalho padrão encontrada. As horas para o técnico {tecnico.username} não serão recalculadas.")
        return

    # 4. Busca TODOS os pontos concluídos do técnico para esta OS nesta data
    pontos_do_dia = RegistroPonto.objects.filter(
        ordem_servico=ordem_servico,
        tecnico=tecnico,
        data=data_ponto,
        hora_saida__isnull=False
    )

    # 5. Calcula as horas
    if pontos_do_dia.exists():
        horas_calculadas = regra_jornada.calcular_horas(list(pontos_do_dia))
    else:
        # Se não há mais pontos (ex: o último foi deletado), zera as horas
        horas_calculadas = {
            'horas_normais': Decimal('0.00'),
            'horas_extras_60': Decimal('0.00'),
            'horas_extras_100': Decimal('0.00')
        }

    # 6. Atualiza o registro de HorasRelatorioTecnico com os novos valores
    horas_tecnico_relatorio.horas_normais = horas_calculadas['horas_normais']
    horas_tecnico_relatorio.horas_extras_60 = horas_calculadas['horas_extras_60']
    horas_tecnico_relatorio.horas_extras_100 = horas_calculadas['horas_extras_100']

    # Usamos update_fields para otimizar a query e evitar disparar outros sinais desnecessariamente
    horas_tecnico_relatorio.save(
        update_fields=['horas_normais', 'horas_extras_60', 'horas_extras_100'])

    print(
        f"Horas para o relatório da OS {ordem_servico.numero_os} na data {data_ponto} recalculadas para o técnico {tecnico.username}.")
