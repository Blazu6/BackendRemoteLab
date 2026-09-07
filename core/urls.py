"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from remote.views import index, machines_api, machine_detail_api, pdu_api, cameras_api
from django.contrib import admin
from django.urls import path
from remote import views

# --- NOWE IMPORTY DO OBSŁUGI PLIKÓW ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/machines/', machines_api, name='machines_api'),
    path('api/machines/<int:machine_id>/', machine_detail_api, name='machine_detail_api'),
    path('api/pdu/', pdu_api, name='pdu_api'),
    path('api/cameras/', cameras_api, name='cameras_api'),
    path('', index, name='index'),
    path('api/documents/', views.documents_api, name='documents_api'),
    path('api/documents/<int:document_id>/', views.document_detail_api, name='document_detail_api'),
]

# --- OBSŁUGA SERWOWANIA PLIKÓW Z FOLDERU MEDIA ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)