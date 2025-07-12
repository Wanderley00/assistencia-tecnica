from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from datetime import time, timedelta, datetime
from django.contrib.auth import get_user_model
from django.utils import timezone


from configuracoes.models import TipoManutencao, TipoDocumento, FormaPagamento, CategoriaDespesa  # NOVO IMPORT

from django.core.exceptions import ValidationError

User = get_user_model()  # Obtém o modelo de usuário ativo

# 1. Cliente Model


class Cliente(models.Model):
    razao_social = models.CharField(
        max_length=200, verbose_name="Razão Social / Nome")
    cnpj_cpf = models.CharField(max_length=18, unique=True, verbose_name="CNPJ / CPF",
                                help_text="Formato: XX.XXX.XXX/XXXX-XX ou XXX.XXX.XXX-XX")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(
        max_length=2, verbose_name="Estado", help_text="Sigla do estado (ex: SP, MG)")
    cep = models.CharField(max_length=10, verbose_name="CEP",
                           help_text="Formato: XXXXX-XXX")
    telefone = models.CharField(
        max_length=20, verbose_name="Telefone", null=True, blank=True)
    email = models.EmailField(verbose_name="E-mail", null=True, blank=True)
    contato_principal = models.CharField(
        max_length=100, verbose_name="Contato Principal")
    telefone_contato = models.CharField(
        max_length=20, verbose_name="Telefone do Contato", null=True, blank=True)
    email_contato = models.EmailField(
        verbose_name="E-mail do Contato", null=True, blank=True)
    usuarios_associados = models.ManyToManyField(
        User, related_name="empresas_associadas", blank=True, verbose_name="Usuários com Acesso")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['razao_social']

    def __str__(self):
        return self.razao_social


class Equipamento(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    nome = models.CharField(max_length=100, verbose_name="Nome do Equipamento")
    modelo = models.CharField(
        max_length=100, verbose_name="Modelo", null=True, blank=True)
    numero_serie = models.CharField(
        max_length=100, unique=True, verbose_name="Número de Série", null=True, blank=True)
    descricao = models.TextField(
        verbose_name="Descrição Detalhada do Equipamento", null=True, blank=True)
    localizacao = models.CharField(
        max_length=255, verbose_name="Localização do Equipamento no Cliente", null=True, blank=True)

    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"
        unique_together = ('cliente', 'nome', 'modelo')

    def __str__(self):
        return f"{self.nome} ({self.modelo or 'N/A'}) - Cliente: {self.cliente.razao_social}"


class OrdemServico(models.Model):
    STATUS_CHOICES = [('PLANEJADA', _('Planejada')), ('AGUARDANDO_PLANEJAMENTO', _('Aguardando Planejamento')), ('EM_EXECUCAO', _(
        'Em Execução')), ('CONCLUIDA', _('Concluída')), ('CANCELADA', _('Cancelada')), ('PENDENTE_APROVACAO', _('Pendente de Aprovação'))]
    # REMOVA: TIPO_MANUTENCAO_CHOICES = [('CORRETIVA', 'Manutenção Corretiva'), ('PREVENTIVA', 'Manutenção Preventiva'), ('INSPECAO', 'Inspeção'), ('OUTRO', 'Outro')]
    numero_os = models.CharField(
        max_length=50, unique=True, verbose_name="Número da OS", help_text="Ex: OS-YYYYMMDD-XXX")
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.PROTECT, verbose_name="Equipamento")
    titulo_servico = models.CharField(
        max_length=255, verbose_name="Título do Serviço")
    # ALTERADO: De CharField com choices para ForeignKey
    tipo_manutencao = models.ForeignKey(
        # Sem default agora, será obrigatório
        TipoManutencao, on_delete=models.PROTECT, verbose_name="Tipo de Manutenção")
    descricao_problema = models.TextField(
        verbose_name="Descrição do Problema / Motivo da OS")
    data_abertura = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Abertura")

    # NOVO CAMPO: Data de Início Planejado
    data_inicio_planejado = models.DateField(
        verbose_name="Início Planejado", null=True, blank=True,
        help_text="Data planejada para o início das atividades da OS."
    )

    # NOVO CAMPO: Data de Início Real
    data_inicio_real = models.DateTimeField(
        verbose_name="Início Real", null=True, blank=True,
        help_text="Data e hora do primeiro registro de ponto ou início efetivo."
    )

    data_previsao_conclusao = models.DateField(
        verbose_name="Previsão de Conclusão", null=True, blank=True)
    data_fechamento = models.DateTimeField(
        verbose_name="Data de Fechamento", null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES,
                              default='AGUARDANDO_PLANEJAMENTO', verbose_name="Status da OS")
    tecnico_responsavel = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Técnico Responsável", related_name="ordens_servico_atuais", null=True, blank=True)
    observacoes_gerais = models.TextField(
        verbose_name="Observações Gerais", null=True, blank=True)
    assinatura_cliente_data = models.TextField(
        verbose_name="Dados da Assinatura do Cliente", null=True, blank=True)

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        ordering = ['-data_abertura']

    def __str__(self):
        return f"OS {self.numero_os} - {self.titulo_servico} ({self.cliente.razao_social})"


# 4. DocumentoOS Model


class DocumentoOS(models.Model):
    """
    Representa documentos anexados a uma Ordem de Serviço (desenhos, listas, etc.).
    """
    # REMOVA: TIPO_DOCUMENTO_CHOICES = [('DESENHO', 'Desenho Técnico'), ('LISTA_FERRAMENTAS', 'Lista de Ferramentas'), ('MANUAL', 'Manual'), ('PLANO_ACAO', 'Plano de Ação'), ('OUTRO', 'Outro')]

    ordem_servico = models.ForeignKey(
        OrdemServico, on_delete=models.CASCADE, verbose_name="Ordem de Serviço", related_name="documentos")
    # ALTERADO: De CharField com choices para ForeignKey
    tipo_documento = models.ForeignKey(
        TipoDocumento, on_delete=models.PROTECT, verbose_name="Tipo de Documento")
    titulo = models.CharField(
        max_length=255, verbose_name="Título do Documento")
    arquivo = models.FileField(
        upload_to='documentos_os/', verbose_name="Arquivo")
    descricao = models.TextField(
        verbose_name="Descrição do Documento", null=True, blank=True)
    data_upload = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Upload")
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Enviado por")

    class Meta:
        verbose_name = "Documento da OS"
        verbose_name_plural = "Documentos da OS"
        ordering = ['-data_upload']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.titulo} (OS: {self.ordem_servico.numero_os})"

# 5. RegistroPonto Model


class RegistroPonto(models.Model):
    """
    Registra os horários de entrada e saída do técnico para uma Ordem de Serviço.
    """
    tecnico = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Técnico")
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE,
                                      verbose_name="Ordem de Serviço", related_name="registros_ponto")
    data = models.DateField(verbose_name="Data do Registro")
    hora_entrada = models.TimeField(verbose_name="Hora de Entrada")
    hora_saida = models.TimeField(
        verbose_name="Hora de Saída", null=True, blank=True)
    # Pode ser usado para registro de geolocalização se o app for mobile
    localizacao = models.CharField(
        # Renomeado para 'Localização de Entrada'
        max_length=255, verbose_name="Localização de Entrada (GPS ou Descrição)", null=True, blank=True)
    localizacao_saida = models.CharField(  # NOVO CAMPO
        max_length=255, verbose_name="Localização de Saída (GPS ou Descrição)", null=True, blank=True)
    observacoes_entrada = models.TextField(
        verbose_name="Observações de Entrada", null=True, blank=True)
    observacoes = models.TextField(
        verbose_name="Observações do Ponto", null=True, blank=True)

    class Meta:
        verbose_name = "Registro de Ponto"
        verbose_name_plural = "Registros de Ponto"
        unique_together = ('tecnico', 'ordem_servico', 'data',
                           'hora_entrada')  # Evita registros duplicados
        ordering = ['-data', '-hora_entrada']

    def __str__(self):
        saida = self.hora_saida.strftime(
            "%H:%M") if self.hora_saida else "Aberto"
        return f"Ponto de {self.tecnico.get_full_name()} em {self.data.strftime('%d/%m/%Y')} - Entrada: {self.hora_entrada.strftime('%H:%M')} | Saída: {saida}"

    @property
    def duracao_formatada(self):
        """
        Calcula a duração entre a entrada e a saída e retorna uma string formatada.
        """
        if not self.hora_saida:
            return "N/A"  # Se o ponto ainda está em aberto

        # Combina a data com as horas para criar objetos datetime completos
        start_datetime = datetime.combine(self.data, self.hora_entrada)
        end_datetime = datetime.combine(self.data, self.hora_saida)

        # Garante que a data de saída é maior que a de entrada
        if end_datetime < start_datetime:
            return "Inválido"

        duration = end_datetime - start_datetime

        # Converte a duração para horas e minutos
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return f"{hours}h {minutes}min"

# 6. RelatorioCampo Model (para RDO e FAT)


class RelatorioCampo(models.Model):
    """
    Representa os relatórios de campo (RDO - Registro Diário de Obra e FAT - Ficha de Assistência Técnica).
    """
    TIPO_RELATORIO_CHOICES = [
        ('RDO', 'Registro Diário de Obra (RDO)'),
        ('FAT', 'Ficha de Assistência Técnica (FAT)'),
    ]

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE,
                                      verbose_name="Ordem de Serviço", related_name="relatorios_campo")
    tecnico = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Técnico Executante")
    tipo_relatorio = models.CharField(
        max_length=10, choices=TIPO_RELATORIO_CHOICES, verbose_name="Tipo de Relatório")
    data_relatorio = models.DateField(verbose_name="Data do Relatório")
    descricao_atividades = models.TextField(
        verbose_name="Descrição das Atividades Realizadas")
    # problemas_identificados = models.TextField(
    #     verbose_name="Problemas Identificados", null=True, blank=True)
    solucoes_aplicadas = models.TextField(
        verbose_name="Soluções Aplicadas / Recomendações", null=True, blank=True)
    material_utilizado = models.TextField(
        verbose_name="Materiais/Peças Utilizadas", null=True, blank=True)

    # Campos específicos da FAT e RDO
    horas_normais = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Horas Normais", validators=[MinValueValidator(0)])
    horas_extras_60 = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Horas Extras (60%)", validators=[MinValueValidator(0)])
    horas_extras_100 = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Horas Extras (100%)", validators=[MinValueValidator(0)])
    km_rodado = models.DecimalField(max_digits=7, decimal_places=2, default=0.00,
                                    verbose_name="KM Rodado", validators=[MinValueValidator(0)])
    local_servico = models.CharField(
        max_length=255, verbose_name="Local do Serviço (Endereço)", null=True, blank=True)

    observacoes_adicionais = models.TextField(
        verbose_name="Observações Adicionais", null=True, blank=True)
    assinatura_executante_data = models.TextField(
        verbose_name="Dados da Assinatura do Executante", null=True, blank=True)
    visto_cliente_imagem = models.ImageField(
        upload_to='vistos_clientes_relatorios/', verbose_name="Visto do Cliente", null=True, blank=True)

    data_criacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação do Relatório")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Relatório de Campo"
        verbose_name_plural = "Relatórios de Campo"
        # Um técnico só faz um RDO/FAT por OS por dia
        unique_together = ('ordem_servico', 'tipo_relatorio',
                           'data_relatorio', 'tecnico')
        ordering = ['-data_relatorio', '-data_criacao']

    def __str__(self):
        return f"{self.get_tipo_relatorio_display()} da OS {self.ordem_servico.numero_os} - {self.data_relatorio.strftime('%d/%m/%Y')}"

# Modelo para Fotos no Relatório de Campo (se desejar gerenciar fotos separadamente)


class FotoRelatorio(models.Model):
    relatorio = models.ForeignKey(RelatorioCampo, on_delete=models.CASCADE,
                                  verbose_name="Relatório de Campo", related_name="fotos")
    imagem = models.ImageField(
        upload_to='fotos_relatorios/', verbose_name="Foto")
    descricao = models.CharField(
        max_length=255, verbose_name="Descrição da Foto", null=True, blank=True)
    data_upload = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Upload")

    class Meta:
        verbose_name = "Foto do Relatório"
        verbose_name_plural = "Fotos do Relatório"
        ordering = ['data_upload']

    def __str__(self):
        return f"Foto para {self.relatorio} - {self.descricao or 'Sem descrição'}"


# 7. Despesa Model
class Despesa(models.Model):
    """
    Registra as despesas associadas a uma Ordem de Serviço para reembolso.
    """
    # REMOVA: TIPO_PAGAMENTO_CHOICES = [('DINHEIRO', 'Dinheiro'), ('DEPOSITO_BANCARIO', 'Depósito Bancário'), ('CARTAO_CREDITO', 'Cartão de Crédito'), ('CARTAO_DEBITO', 'Cartão de Débito'), ('PIX', 'PIX'), ('OUTRO', 'Outro')]

    # NOVO CAMPO: Indica se a despesa é um adiantamento
    is_adiantamento = models.BooleanField(
        default=False, verbose_name=_("Adiantamento?"),
        help_text=_(
            "Marque se esta despesa for um adiantamento para o serviço, exigindo pagamento antes do início.")
    )

    ordem_servico = models.ForeignKey(
        OrdemServico, on_delete=models.CASCADE, related_name='despesas', verbose_name=_("Ordem de Serviço"))
    tecnico = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='despesas_registradas', verbose_name=_("Técnico"))
    data_despesa = models.DateField(verbose_name=_("Data da Despesa"))
    descricao = models.CharField(max_length=255, verbose_name=_("Descrição"))
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Valor"))
    tipo_pagamento = models.ForeignKey(
        FormaPagamento, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Forma de Pagamento"))
    categoria_despesa = models.ForeignKey(
        CategoriaDespesa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Categoria da Despesa"))
    is_adiantamento = models.BooleanField(
        default=False, verbose_name=_("É Adiantamento?"),
        help_text=_(
            "Marque se esta despesa for um adiantamento para o serviço, exigindo pagamento antes do início.")
    )
    comprovante_anexo = models.FileField(
        upload_to='comprovantes_despesas/', verbose_name=_("Comprovante (Imagem/PDF)"), null=True, blank=True)
    local_despesa = models.CharField(
        max_length=255, verbose_name=_("Local da Despesa (Estabelecimento)"), null=True, blank=True)

    STATUS_APROVACAO_CHOICES = [
        ('PENDENTE', _('Pendente')),
        ('APROVADA', _('Aprovada')),
        ('REJEITADA', _('Rejeitada')),
    ]
    status_aprovacao = models.CharField(
        max_length=10, choices=STATUS_APROVACAO_CHOICES, default='PENDENTE', verbose_name=_("Status de Aprovação")
    )
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name="despesas_aprovadas", verbose_name=_("Aprovado por"))
    data_aprovacao = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Data de Aprovação"))
    comentario_aprovacao = models.TextField(
        verbose_name=_("Comentário de Aprovação/Rejeição"), null=True, blank=True
    )

    # NOVOS CAMPOS PARA STATUS DE PAGAMENTO
    paga = models.BooleanField(default=False, verbose_name=_("Paga?"))
    data_pagamento = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Data do Pagamento"))

    class Meta:
        verbose_name = _("Despesa")
        verbose_name_plural = _("Despesas")
        ordering = ['-data_despesa', 'descricao']

    def __str__(self):
        return f"Despesa de R$ {self.valor:.2f} em {self.data_despesa.strftime('%d/%m/%Y')} - {self.descricao} (OS: {self.ordem_servico.numero_os})"


class ContaPagar(models.Model):
    despesa = models.OneToOneField(Despesa, on_delete=models.CASCADE,
                                   related_name='conta_a_pagar', verbose_name=_("Despesa Associada"))

    STATUS_PAGAMENTO_CHOICES = [
        ('PENDENTE', _('Pendente')),
        ('EM_ANALISE', _('Em Análise')),
        ('PAGO', _('Pago')),
        # Para caso o pagamento seja cancelado por algum motivo
        ('CANCELADO', _('Cancelado')),
    ]
    status_pagamento = models.CharField(
        max_length=10, choices=STATUS_PAGAMENTO_CHOICES, default='PENDENTE', verbose_name=_("Status do Pagamento")
    )

    comentario = models.TextField(
        verbose_name=_("Comentário do Pagamento"), null=True, blank=True,
        help_text=_("Adicione detalhes sobre o pagamento ou análise.")
    )
    comprovante_pagamento = models.FileField(
        upload_to='comprovantes_pagamento/', verbose_name=_("Comprovante de Pagamento (Imagem/PDF)"), null=True, blank=True
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Data de Criação"))
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name=_("Última Atualização"))

    # Quem registrou/atualizou o status de pagamento
    responsavel_pagamento = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Responsável pelo Pagamento"))

    class Meta:
        verbose_name = _("Conta a Pagar")
        verbose_name_plural = _("Contas a Pagar")
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Conta a Pagar para Despesa {self.despesa.id} (OS: {self.despesa.ordem_servico.numero_os}) - Status: {self.get_status_pagamento_display()}"

    def save(self, *args, **kwargs):
        # Quando o status do ContaPagar for 'PAGO', atualiza a despesa associada
        if self.status_pagamento == 'PAGO' and not self.despesa.paga:
            self.despesa.paga = True
            self.despesa.data_pagamento = timezone.now()
            self.despesa.save()
        # Se o status mudar de PAGO para outro, reseta a despesa
        elif self.status_pagamento != 'PAGO' and self.despesa.paga:
            self.despesa.paga = False
            self.despesa.data_pagamento = None
            self.despesa.save()
        super().save(*args, **kwargs)


class MembroEquipe(models.Model):
    """
    Representa um membro da equipe alocado para uma Ordem de Serviço específica.
    AGORA APENAS USUÁRIOS DO SISTEMA PODEM SER MEMBROS DA EQUIPE.
    """
    ordem_servico = models.ForeignKey(
        OrdemServico, on_delete=models.CASCADE, related_name="equipe")

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Membro da Equipe (Usuário)")

    # REINTRODUZINDO ESTE CAMPO COMO OPCIONAL
    funcao = models.CharField(
        max_length=100,
        verbose_name="Função na Equipe",
        help_text="Ex: Ajudante, Eletricista Auxiliar",
        blank=True,  # Torna o campo opcional no formulário
        null=True  # Permite que o campo seja NULL no banco de dados
    )

    class Meta:
        verbose_name = "Membro da Equipe"
        verbose_name_plural = "Membros da Equipe"
        unique_together = ('ordem_servico', 'usuario')

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username}"


class RegraJornadaTrabalho(models.Model):
    """
    Define as regras para cálculo de horas normais e extras.
    """
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name=_("Nome da Regra"))

    # Jornada Normal Diária
    horas_normais_diarias = models.DecimalField(
        max_digits=4, decimal_places=2, default=8.00,
        verbose_name=_("Horas Normais Diárias (Ex: 8.00)")
    )

    # Horário de Início e Fim da Jornada Normal
    # Isso é importante para diferenciar horas extras que caem antes ou depois do turno normal
    inicio_jornada_normal = models.TimeField(
        default=time(8, 0, 0), verbose_name=_("Início da Jornada Normal (HH:MM)")
    )
    fim_jornada_normal = models.TimeField(
        default=time(17, 0, 0), verbose_name=_("Fim da Jornada Normal (HH:MM)")
    )

    # Horas Extras 60%
    # Pode ser uma duração após o fim da jornada normal, ou um horário limite
    # Vamos usar um horário limite para maior flexibilidade
    inicio_extra_60 = models.TimeField(
        default=time(17, 0, 1), verbose_name=_("Início da Hora Extra 60% (HH:MM)")
    )
    fim_extra_60 = models.TimeField(
        default=time(22, 0, 0), verbose_name=_("Fim da Hora Extra 60% (HH:MM)")
    )

    # Horas Extras 100% (Geralmente após a faixa de 60% ou em horários específicos)
    inicio_extra_100 = models.TimeField(
        default=time(22, 0, 1), verbose_name=_("Início da Hora Extra 100% (HH:MM)")
    )
    # Não precisamos de um 'fim_extra_100' se for até a meia-noite ou o próximo dia

    # Regras para Fins de Semana e Feriados
    # Assumimos que o trabalho em fins de semana/feriados é 100% extra, a menos que especificado
    # Podemos ter uma flag para indicar se a regra normal se aplica em sábados/domingos
    # Ou simplesmente considerar que Sábado e Domingo são sempre 100% extra
    considerar_sabado_100_extra = models.BooleanField(
        default=True, verbose_name=_("Considerar Sábado 100% Extra")
    )
    considerar_domingo_100_extra = models.BooleanField(
        default=True, verbose_name=_("Considerar Domingo 100% Extra")
    )

    # Associação com Usuários (opcional, para regras específicas por técnico/equipe)
    # Se uma regra for default para a empresa, não precisa de associação direta aqui.
    # Podemos associar a um usuário ou deixar global.
    # Por enquanto, vamos manter como uma regra geral.

    # Campo para indicar se esta é a regra padrão (default)
    is_default = models.BooleanField(
        default=False, verbose_name=_("Regra Padrão (Default)")
    )

    class Meta:
        verbose_name = _("Regra de Jornada de Trabalho")
        verbose_name_plural = _("Regras de Jornada de Trabalho")

    def __str__(self):
        return self.nome

    # Método para calcular horas (será implementado mais tarde)
    def calcular_horas(self, hora_entrada: time, hora_saida: time, data: datetime.date) -> dict:
        # Este método será implementado na próxima etapa
        # Retornará um dicionário com 'normais', 'extra_60', 'extra_100'
        return {
            'normais': 0,
            'extra_60': 0,
            'extra_100': 0
        }

# 10. Categorias de Problema


class CategoriaProblema(models.Model):
    nome = models.CharField(max_length=100, unique=True,
                            verbose_name=_("Nome da Categoria"))
    ativo = models.BooleanField(default=True, verbose_name=_("Ativo"))

    class Meta:
        verbose_name = _("Categoria de Problema")
        verbose_name_plural = _("Categorias de Problemas")
        ordering = ['nome']

    def __str__(self):
        return self.nome

# 11. Subcategorias de Problema (relacionadas a uma Categoria)


class SubcategoriaProblema(models.Model):
    categoria = models.ForeignKey(
        CategoriaProblema, on_delete=models.CASCADE, related_name="subcategorias", verbose_name=_("Categoria Principal")
    )
    nome = models.CharField(
        max_length=100, verbose_name=_("Nome da Subcategoria"))
    ativo = models.BooleanField(default=True, verbose_name=_("Ativo"))

    class Meta:
        verbose_name = _("Subcategoria de Problema")
        verbose_name_plural = _("Subcategorias de Problemas")
        # Uma subcategoria é única dentro de uma categoria
        unique_together = ('categoria', 'nome')
        ordering = ['categoria__nome', 'nome']

    def __str__(self):
        return f"{self.categoria.nome} - {self.nome}"

# 12. Problemas Identificados (para cada relatório)


class ProblemaRelatorio(models.Model):
    """
    Representa um problema individual identificado em um Relatório de Campo.
    """
    relatorio = models.ForeignKey(
        'RelatorioCampo', on_delete=models.CASCADE, related_name="problemas_identificados_detalhes", verbose_name=_("Relatório de Campo")
    )
    categoria = models.ForeignKey(
        CategoriaProblema, on_delete=models.PROTECT, verbose_name=_(
            "Categoria do Problema")
    )
    subcategoria = models.ForeignKey(
        SubcategoriaProblema, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Subcategoria do Problema")
    )
    observacao = models.TextField(
        verbose_name=_("Comentário / Observação do Problema"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("Problema Identificado")
        verbose_name_plural = _("Problemas Identificados")
        # Pode haver múltiplos problemas do mesmo tipo em um relatório, então não unique_together
        ordering = ['categoria__nome', 'subcategoria__nome']

    def __str__(self):
        sub = f" ({self.subcategoria.nome})" if self.subcategoria else ""
        return f"{self.categoria.nome}{sub}: {self.observacao or 'Sem observação'}"
