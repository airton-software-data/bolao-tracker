from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),# core/urls.py
    path('', include('loteria.urls')), # Conecta as URLs do aplicativo
]
    
# Adicione esta linha no final do arquivo:
handler403 = 'loteria.views.erro_403'
    

