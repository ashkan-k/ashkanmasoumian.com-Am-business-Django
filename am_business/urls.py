from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from core import views as core_views

schema_view = get_schema_view(
    openapi.Info(
        title="AM Business API",
        default_version="v1",
        description="AM Business Website Content Management API",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="admin@ambusiness.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("accounts/login/", core_views.admin_login, name="admin_login"),
    path("accounts/logout/", core_views.admin_logout, name="admin_logout"),
    path("accounts/", include("accounts.urls")),

    # Language & Theme
    path("set-language/<str:lang>/", core_views.set_language_view, name="set_language"),
    path("set-theme/<str:theme>/", core_views.set_theme_view, name="set_theme"),

    # Core (admin panel + API)
    path("", include("core.urls")),

    # Swagger / ReDoc
    re_path(r"^swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0),
         name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0),
         name="schema-redoc"),

    # Root is now the frontend (defined in core.urls)
    # path("", RedirectView.as_view(url="/admin-panel/"), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
