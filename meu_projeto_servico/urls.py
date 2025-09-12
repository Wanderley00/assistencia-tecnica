# meu_projeto_servico/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Importe seu formulário de login customizado
from servico_campo.forms import LoginFormCustom
from servico_campo.views import CustomLoginView
from servico_campo.forms import PasswordResetFormCustom
from servico_campo.views import CustomPasswordResetView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('servico/', include('servico_campo.urls')),

    # URLs do seu site original (app servico_campo)
    path('', include('servico_campo.urls')),

    # URLs da sua nova API, todas começarão com /api/
    path('api/', include('api.urls')),

    # NOVO: Incluir URLs do app de configurações
    path('configuracoes/', include('configuracoes.urls')),
    # ... (outras URLs de login/logout, etc.)
    # Use sua CustomLoginView aqui
    path('', CustomLoginView.as_view(), name='login'),  # <--- MUDANÇA AQUI
    path('logout/', auth_views.LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),

    # URLs para Autenticação (incluindo Redefinição de Senha)
    path('', CustomLoginView.as_view(), name='login'),  # Sua tela de login
    path('logout/', auth_views.LogoutView.as_view(next_page='/'),
         name='logout'),  # Redireciona para a raiz após logout

    # NOVO: URLs de Redefinição de Senha (usando sua CustomPasswordResetView)
    path('password_reset/', CustomPasswordResetView.as_view(  # Usando sua CustomPasswordResetView
        template_name='registration/password_reset_form.html',
        # Template para texto puro (pode ser o mesmo ou um .txt)
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/password_reset/done/',
        # MUDANÇA AQUI: Adicionar html_email_template_name
        # <--- ADICIONE ESTA LINHA!
        html_email_template_name='registration/password_reset_email.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
