# Generated by Django 5.2.3 on 2025-07-18 17:11

import datetime
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('configuracoes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaProblema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True, verbose_name='Nome da Categoria')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Categoria de Problema',
                'verbose_name_plural': 'Categorias de Problemas',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='ConfiguracaoEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_host', models.CharField(max_length=255, verbose_name='Servidor SMTP (Host)')),
                ('email_port', models.PositiveIntegerField(default=587, verbose_name='Porta')),
                ('email_host_user', models.EmailField(max_length=254, verbose_name='E-mail de Envio (Usuário)')),
                ('email_host_password', models.CharField(max_length=255, verbose_name='Senha do E-mail')),
                ('email_backend', models.CharField(default='django.core.mail.backends.smtp.EmailBackend', editable=False, max_length=255)),
                ('email_use_tls', models.BooleanField(default=True, editable=False, verbose_name='Usar TLS')),
                ('email_use_ssl', models.BooleanField(default=False, editable=False, verbose_name='Usar SSL')),
            ],
            options={
                'verbose_name': 'Configuração de E-mail',
                'verbose_name_plural': 'Configurações de E-mail',
            },
        ),
        migrations.CreateModel(
            name='RegraJornadaTrabalho',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True, verbose_name='Nome da Regra')),
                ('horas_normais_diarias', models.DecimalField(decimal_places=2, default=8.0, max_digits=4, verbose_name='Horas Normais Diárias (Ex: 8.00)')),
                ('inicio_jornada_normal', models.TimeField(default=datetime.time(8, 0), verbose_name='Início da Jornada Normal (HH:MM)')),
                ('fim_jornada_normal', models.TimeField(default=datetime.time(17, 0), verbose_name='Fim da Jornada Normal (HH:MM)')),
                ('inicio_extra_60', models.TimeField(default=datetime.time(17, 0, 1), verbose_name='Início da Hora Extra 60% (HH:MM)')),
                ('fim_extra_60', models.TimeField(default=datetime.time(22, 0), verbose_name='Fim da Hora Extra 60% (HH:MM)')),
                ('inicio_extra_100', models.TimeField(default=datetime.time(22, 0, 1), verbose_name='Início da Hora Extra 100% (HH:MM)')),
                ('considerar_sabado_100_extra', models.BooleanField(default=True, verbose_name='Considerar Sábado 100% Extra')),
                ('considerar_domingo_100_extra', models.BooleanField(default=True, verbose_name='Considerar Domingo 100% Extra')),
                ('is_default', models.BooleanField(default=False, verbose_name='Regra Padrão (Default)')),
            ],
            options={
                'verbose_name': 'Regra de Jornada de Trabalho',
                'verbose_name_plural': 'Regras de Jornada de Trabalho',
            },
        ),
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razao_social', models.CharField(max_length=200, verbose_name='Razão Social / Nome')),
                ('cnpj_cpf', models.CharField(help_text='Formato: XX.XXX.XXX/XXXX-XX ou XXX.XXX.XXX-XX', max_length=18, unique=True, verbose_name='CNPJ / CPF')),
                ('endereco', models.CharField(max_length=255, verbose_name='Endereço')),
                ('cidade', models.CharField(max_length=100, verbose_name='Cidade')),
                ('estado', models.CharField(help_text='Sigla do estado (ex: SP, MG)', max_length=2, verbose_name='Estado')),
                ('cep', models.CharField(help_text='Formato: XXXXX-XXX', max_length=10, verbose_name='CEP')),
                ('telefone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='E-mail')),
                ('contato_principal', models.CharField(max_length=100, verbose_name='Contato Principal')),
                ('telefone_contato', models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone do Contato')),
                ('email_contato', models.EmailField(blank=True, max_length=254, null=True, verbose_name='E-mail do Contato')),
                ('usuarios_associados', models.ManyToManyField(blank=True, related_name='empresas_associadas', to=settings.AUTH_USER_MODEL, verbose_name='Usuários com Acesso')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['razao_social'],
            },
        ),
        migrations.CreateModel(
            name='Despesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_despesa', models.DateField(verbose_name='Data da Despesa')),
                ('descricao', models.CharField(max_length=255, verbose_name='Descrição')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor')),
                ('is_adiantamento', models.BooleanField(default=False, help_text='Marque se esta despesa for um adiantamento para o serviço, exigindo pagamento antes do início.', verbose_name='É Adiantamento?')),
                ('comprovante_anexo', models.FileField(blank=True, null=True, upload_to='comprovantes_despesas/', verbose_name='Comprovante (Imagem/PDF)')),
                ('local_despesa', models.CharField(blank=True, max_length=255, null=True, verbose_name='Local da Despesa (Estabelecimento)')),
                ('status_aprovacao', models.CharField(choices=[('PENDENTE', 'Pendente'), ('APROVADA', 'Aprovada'), ('REJEITADA', 'Rejeitada')], default='PENDENTE', max_length=10, verbose_name='Status de Aprovação')),
                ('data_aprovacao', models.DateTimeField(blank=True, null=True, verbose_name='Data de Aprovação')),
                ('comentario_aprovacao', models.TextField(blank=True, null=True, verbose_name='Comentário de Aprovação/Rejeição')),
                ('paga', models.BooleanField(default=False, verbose_name='Paga?')),
                ('data_pagamento', models.DateTimeField(blank=True, null=True, verbose_name='Data do Pagamento')),
                ('aprovado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='despesas_aprovadas', to=settings.AUTH_USER_MODEL, verbose_name='Aprovado por')),
                ('categoria_despesa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='configuracoes.categoriadespesa', verbose_name='Categoria da Despesa')),
                ('tecnico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='despesas_registradas', to=settings.AUTH_USER_MODEL, verbose_name='Técnico')),
                ('tipo_pagamento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='configuracoes.formapagamento', verbose_name='Forma de Pagamento')),
            ],
            options={
                'verbose_name': 'Despesa',
                'verbose_name_plural': 'Despesas',
                'ordering': ['-data_despesa', 'descricao'],
            },
        ),
        migrations.CreateModel(
            name='ContaPagar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_pagamento', models.CharField(choices=[('PENDENTE', 'Pendente'), ('EM_ANALISE', 'Em Análise'), ('PAGO', 'Pago'), ('CANCELADO', 'Cancelado')], default='PENDENTE', max_length=10, verbose_name='Status do Pagamento')),
                ('comentario', models.TextField(blank=True, help_text='Adicione detalhes sobre o pagamento ou análise.', null=True, verbose_name='Comentário do Pagamento')),
                ('comprovante_pagamento', models.FileField(blank=True, null=True, upload_to='comprovantes_pagamento/', verbose_name='Comprovante de Pagamento (Imagem/PDF)')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Última Atualização')),
                ('responsavel_pagamento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Responsável pelo Pagamento')),
                ('despesa', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='conta_a_pagar', to='servico_campo.despesa', verbose_name='Despesa Associada')),
            ],
            options={
                'verbose_name': 'Conta a Pagar',
                'verbose_name_plural': 'Contas a Pagar',
                'ordering': ['-data_criacao'],
            },
        ),
        migrations.CreateModel(
            name='Equipamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome do Equipamento')),
                ('modelo', models.CharField(blank=True, max_length=100, null=True, verbose_name='Modelo')),
                ('numero_serie', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Número de Série')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição Detalhada do Equipamento')),
                ('localizacao', models.CharField(blank=True, max_length=255, null=True, verbose_name='Localização do Equipamento no Cliente')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servico_campo.cliente', verbose_name='Cliente')),
            ],
            options={
                'verbose_name': 'Equipamento',
                'verbose_name_plural': 'Equipamentos',
                'unique_together': {('cliente', 'nome', 'modelo')},
            },
        ),
        migrations.CreateModel(
            name='OrdemServico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_os', models.CharField(help_text='Ex: OS-YYYYMMDD-XXX', max_length=50, unique=True, verbose_name='Número da OS')),
                ('titulo_servico', models.CharField(max_length=255, verbose_name='Título do Serviço')),
                ('descricao_problema', models.TextField(verbose_name='Descrição do Problema / Motivo da OS')),
                ('data_abertura', models.DateTimeField(auto_now_add=True, verbose_name='Data de Abertura')),
                ('data_inicio_planejado', models.DateField(blank=True, help_text='Data planejada para o início das atividades da OS.', null=True, verbose_name='Início Planejado')),
                ('data_inicio_real', models.DateTimeField(blank=True, help_text='Data e hora do primeiro registro de ponto ou início efetivo.', null=True, verbose_name='Início Real')),
                ('data_previsao_conclusao', models.DateField(blank=True, null=True, verbose_name='Previsão de Conclusão')),
                ('data_fechamento', models.DateTimeField(blank=True, null=True, verbose_name='Data de Fechamento')),
                ('status', models.CharField(choices=[('PLANEJADA', 'Planejada'), ('AGUARDANDO_PLANEJAMENTO', 'Aguardando Planejamento'), ('EM_EXECUCAO', 'Em Execução'), ('CONCLUIDA', 'Concluída'), ('CANCELADA', 'Cancelada'), ('PENDENTE_APROVACAO', 'Pendente de Aprovação')], default='AGUARDANDO_PLANEJAMENTO', max_length=25, verbose_name='Status da OS')),
                ('observacoes_gerais', models.TextField(blank=True, null=True, verbose_name='Observações Gerais')),
                ('assinatura_cliente_data', models.TextField(blank=True, null=True, verbose_name='Dados da Assinatura do Cliente')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='servico_campo.cliente', verbose_name='Cliente')),
                ('equipamento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='servico_campo.equipamento', verbose_name='Equipamento')),
                ('gestor_responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ordens_servico_gerenciadas', to=settings.AUTH_USER_MODEL, verbose_name='Gestor Responsável')),
                ('tecnico_responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ordens_servico_atuais', to=settings.AUTH_USER_MODEL, verbose_name='Responsável')),
                ('tipo_manutencao', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='configuracoes.tipomanutencao', verbose_name='Tipo de Serviço')),
            ],
            options={
                'verbose_name': 'Ordem de Serviço',
                'verbose_name_plural': 'Ordens de Serviço',
                'ordering': ['-data_abertura'],
            },
        ),
        migrations.CreateModel(
            name='DocumentoOS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, verbose_name='Título do Documento')),
                ('arquivo', models.FileField(upload_to='documentos_os/', verbose_name='Arquivo')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição do Documento')),
                ('data_upload', models.DateTimeField(auto_now_add=True, verbose_name='Data de Upload')),
                ('tipo_documento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='configuracoes.tipodocumento', verbose_name='Tipo de Documento')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Enviado por')),
                ('ordem_servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='servico_campo.ordemservico', verbose_name='Ordem de Serviço')),
            ],
            options={
                'verbose_name': 'Documento da OS',
                'verbose_name_plural': 'Documentos da OS',
                'ordering': ['-data_upload'],
            },
        ),
        migrations.AddField(
            model_name='despesa',
            name='ordem_servico',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='despesas', to='servico_campo.ordemservico', verbose_name='Ordem de Serviço'),
        ),
        migrations.CreateModel(
            name='RelatorioCampo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_relatorio', models.CharField(choices=[('RDO', 'Registro Diário de Obra (RDO)'), ('FAT', 'Ficha de Assistência Técnica (FAT)')], max_length=10, verbose_name='Tipo de Relatório')),
                ('data_relatorio', models.DateField(verbose_name='Data do Relatório')),
                ('descricao_atividades', models.TextField(verbose_name='Descrição das Atividades Realizadas')),
                ('solucoes_aplicadas', models.TextField(blank=True, null=True, verbose_name='Soluções Aplicadas / Recomendações')),
                ('material_utilizado', models.TextField(blank=True, null=True, verbose_name='Materiais/Peças Utilizadas')),
                ('horas_normais', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Horas Normais')),
                ('horas_extras_60', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Horas Extras (60%)')),
                ('horas_extras_100', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Horas Extras (100%)')),
                ('km_rodado', models.DecimalField(decimal_places=2, default=0.0, max_digits=7, validators=[django.core.validators.MinValueValidator(0)], verbose_name='KM Rodado')),
                ('local_servico', models.CharField(blank=True, max_length=255, null=True, verbose_name='Local do Serviço (Endereço)')),
                ('observacoes_adicionais', models.TextField(blank=True, null=True, verbose_name='Observações Adicionais')),
                ('assinatura_executante_data', models.TextField(blank=True, null=True, verbose_name='Dados da Assinatura do Executante')),
                ('visto_cliente_imagem', models.ImageField(blank=True, null=True, upload_to='vistos_clientes_relatorios/', verbose_name='Visto do Cliente')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação do Relatório')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Última Atualização')),
                ('ordem_servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relatorios_campo', to='servico_campo.ordemservico', verbose_name='Ordem de Serviço')),
                ('tecnico', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Técnico Executante')),
            ],
            options={
                'verbose_name': 'Relatório de Campo',
                'verbose_name_plural': 'Relatórios de Campo',
                'ordering': ['-data_relatorio', '-data_criacao'],
                'unique_together': {('ordem_servico', 'tipo_relatorio', 'data_relatorio', 'tecnico')},
            },
        ),
        migrations.CreateModel(
            name='FotoRelatorio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagem', models.ImageField(upload_to='fotos_relatorios/', verbose_name='Foto')),
                ('descricao', models.CharField(blank=True, max_length=255, null=True, verbose_name='Descrição da Foto')),
                ('data_upload', models.DateTimeField(auto_now_add=True, verbose_name='Data de Upload')),
                ('relatorio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fotos', to='servico_campo.relatoriocampo', verbose_name='Relatório de Campo')),
            ],
            options={
                'verbose_name': 'Foto do Relatório',
                'verbose_name_plural': 'Fotos do Relatório',
                'ordering': ['data_upload'],
            },
        ),
        migrations.CreateModel(
            name='SubcategoriaProblema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da Subcategoria')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategorias', to='servico_campo.categoriaproblema', verbose_name='Categoria Principal')),
            ],
            options={
                'verbose_name': 'Subcategoria de Problema',
                'verbose_name_plural': 'Subcategorias de Problemas',
                'ordering': ['categoria__nome', 'nome'],
                'unique_together': {('categoria', 'nome')},
            },
        ),
        migrations.CreateModel(
            name='ProblemaRelatorio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Comentário / Observação do Problema')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='servico_campo.categoriaproblema', verbose_name='Categoria do Problema')),
                ('relatorio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problemas_identificados_detalhes', to='servico_campo.relatoriocampo', verbose_name='Relatório de Campo')),
                ('subcategoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='servico_campo.subcategoriaproblema', verbose_name='Subcategoria do Problema')),
            ],
            options={
                'verbose_name': 'Problema Identificado',
                'verbose_name_plural': 'Problemas Identificados',
                'ordering': ['categoria__nome', 'subcategoria__nome'],
            },
        ),
        migrations.CreateModel(
            name='MembroEquipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('funcao', models.CharField(blank=True, help_text='Ex: Ajudante, Eletricista Auxiliar', max_length=100, null=True, verbose_name='Função na Equipe')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Membro da Equipe (Usuário)')),
                ('ordem_servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipe', to='servico_campo.ordemservico')),
            ],
            options={
                'verbose_name': 'Membro da Equipe',
                'verbose_name_plural': 'Membros da Equipe',
                'unique_together': {('ordem_servico', 'usuario')},
            },
        ),
        migrations.CreateModel(
            name='RegistroPonto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(verbose_name='Data do Registro')),
                ('hora_entrada', models.TimeField(verbose_name='Hora de Entrada')),
                ('hora_saida', models.TimeField(blank=True, null=True, verbose_name='Hora de Saída')),
                ('localizacao', models.CharField(blank=True, max_length=255, null=True, verbose_name='Localização de Entrada (GPS ou Descrição)')),
                ('localizacao_saida', models.CharField(blank=True, max_length=255, null=True, verbose_name='Localização de Saída (GPS ou Descrição)')),
                ('observacoes_entrada', models.TextField(blank=True, null=True, verbose_name='Observações de Entrada')),
                ('observacoes', models.TextField(blank=True, null=True, verbose_name='Observações do Ponto')),
                ('ordem_servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_ponto', to='servico_campo.ordemservico', verbose_name='Ordem de Serviço')),
                ('tecnico', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Técnico')),
            ],
            options={
                'verbose_name': 'Registro de Ponto',
                'verbose_name_plural': 'Registros de Ponto',
                'ordering': ['-data', '-hora_entrada'],
                'unique_together': {('tecnico', 'ordem_servico', 'data', 'hora_entrada')},
            },
        ),
    ]
