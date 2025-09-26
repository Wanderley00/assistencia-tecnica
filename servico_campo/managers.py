# servico_campo/managers.py

from django.db import models
from django.core.exceptions import FieldDoesNotExist


class EmpresaScopedQuerySet(models.QuerySet):
    """
    Um QuerySet customizado que sabe como filtrar objetos
    baseado nas empresas associadas a um usuário.
    """

    def for_user(self, user):
        # Se o usuário for um superusuário, ele pode ver tudo.
        if user.is_superuser:
            return self.all()

        # Pega a lista de IDs das empresas às quais o usuário está associado.
        # Usar .values_list('pk', flat=True) é mais eficiente.
        empresas_permitidas_ids = user.empresas_associadas.values_list(
            'pk', flat=True)

        # Tenta encontrar o caminho para filtrar pelo cliente/empresa.
        # Isso torna o QuerySet reutilizável para diferentes modelos.
        # Ex: Para OrdemServico, o caminho é 'cliente__pk__in'.
        # Ex: Para Equipamento, o caminho é 'cliente__pk__in'.
        # Ex: Para Despesa, o caminho é 'ordem_servico__cliente__pk__in'.

        # O 'self.model' se refere ao modelo que está usando este QuerySet (ex: OrdemServico)
        model_meta = self.model._meta

        # Tenta os caminhos mais comuns para chegar até a empresa
        lookup_paths = [
            'cliente__pk__in',
            'ordem_servico__cliente__pk__in',
            'despesa__ordem_servico__cliente__pk__in',
            'relatorio__ordem_servico__cliente__pk__in',
        ]

        caminho_de_filtro = None
        for path in lookup_paths:
            try:
                # Verifica se o caminho é válido para o modelo atual
                model_meta.get_field(path.split('__')[0])
                caminho_de_filtro = path
                break  # Encontrou um caminho válido, para o loop
            except FieldDoesNotExist:
                continue  # Tenta o próximo caminho

        if not caminho_de_filtro:
            # Se nenhum caminho de filtro for encontrado, levanta um erro claro.
            # Isso nos força a configurar corretamente qualquer novo modelo.
            raise NotImplementedError(
                f"O modelo {self.model.__name__} usa EmpresaScopedQuerySet mas não tem um "
                f"caminho de lookup para 'cliente' definido nos lookup_paths."
            )

        # Retorna o queryset filtrado, garantindo que não haja duplicatas.
        return self.filter(**{caminho_de_filtro: empresas_permitidas_ids}).distinct()


class EmpresaScopedManager(models.Manager):
    """
    Um Manager que retorna o EmpresaScopedQuerySet,
    dando acesso ao método .for_user().
    """

    def get_queryset(self):
        return EmpresaScopedQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)
