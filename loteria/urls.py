# loteria/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# loteria/urls.py

urlpatterns = [
    path('', views.home, name='home'),
    path('bolao/<int:bolao_id>/', views.detalhe_bolao, name='detalhe_bolao'),
    
    # Novas rotas de Cadastro e Perfil
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/', views.perfil, name='perfil'),
    
    # Rotas de Auth que já existiam
    path('login/', auth_views.LoginView.as_view(template_name='loteria/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('bolao/<int:bolao_id>/', views.detalhe_bolao, name='detalhe_bolao'),
    path('bolao/<int:bolao_id>/relatorio/', views.relatorio_bolao, name='relatorio_bolao'), # <-- Nova rota
    
    # loteria/urls.py (Adicione junto com as outras rotas de autenticação)

    path('recuperar-senha/', auth_views.PasswordResetView.as_view(template_name='loteria/recuperar_senha.html'), name='password_reset'),
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='loteria/recuperar_senha_enviado.html'), name='password_reset_done'),
    path('recuperar-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='loteria/recuperar_senha_confirmar.html'), name='password_reset_confirm'),
    path('recuperar-senha/concluido/', auth_views.PasswordResetCompleteView.as_view(template_name='loteria/recuperar_senha_concluido.html'), name='password_reset_complete'),
]