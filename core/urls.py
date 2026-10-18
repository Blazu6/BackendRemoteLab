from remote.views import index, machines_api, machine_detail_api, pdu_api, cameras_api
from django.contrib import admin
from django.urls import path, include
from remote import views

# --- NOWE IMPORTY DO OBSŁUGI PLIKÓW ---
from django.conf import settings
from django.conf.urls.static import static

# --- JWT tokeny ---
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- SAML2 (EduGAIN) ---
    # Rejestruje automatycznie:
    #   /saml/login/     — inicjuje AuthnRequest → redirect do IdP uczelni
    #   /saml/acs/       — Assertion Consumer Service (IdP odsyła tu asercję)
    #   /saml/ls/        — Single Logout (GET)
    #   /saml/ls/post/   — Single Logout (POST)
    #   /saml/metadata/  — Metadane SP (XML wysyłany do IT uczelni)
    path('saml/', include('djangosaml2.urls')),

    # --- JWT (opcjonalnie dla Vue jeśli nie używa sesji cookie) ---
    path('api/token/',         TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),

    # --- REST API ---
    path('api/machines/', machines_api, name='machines_api'),
    path('api/machines/<int:machine_id>/', machine_detail_api, name='machine_detail_api'),
    path('api/pdu/', pdu_api, name='pdu_api'),
    path('api/cameras/', cameras_api, name='cameras_api'),
    path('api/documents/', views.documents_api, name='documents_api'),
    path('api/documents/<int:document_id>/', views.document_detail_api, name='document_detail_api'),

    # --- Frontend (SPA fallback) ---
    path('', index, name='index'),
]

# --- OBSŁUGA SERWOWANIA PLIKÓW Z FOLDERU MEDIA ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)