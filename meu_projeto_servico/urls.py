# meu_projeto_servico/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Importe seu formulário de login customizado
from servico_campo.forms import LoginFormCustom


urlpatterns = [
    path('admin/', admin.site.urls),
    path('servico/', include('servico_campo.urls')),
    # NOVO: Incluir URLs do app de configurações
    path('configuracoes/', include('configuracoes.urls')),
    # ... (outras URLs de login/logout, etc.)
    path('', auth_views.LoginView.as_view(template_name='registration/login.html',
         authentication_form=LoginFormCustom), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
