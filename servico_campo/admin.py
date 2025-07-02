from django.contrib import admin
from .models import Cliente, Equipamento, OrdemServico, DocumentoOS, \
    RegistroPonto, RelatorioCampo, FotoRelatorio, Despesa

admin.site.register(Cliente)
admin.site.register(Equipamento)
admin.site.register(OrdemServico)
admin.site.register(DocumentoOS)
admin.site.register(RegistroPonto)
admin.site.register(RelatorioCampo)
admin.site.register(FotoRelatorio)
admin.site.register(Despesa)
