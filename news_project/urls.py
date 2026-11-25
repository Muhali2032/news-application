"""Define the main URL routes for the news project."""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("news.api_urls")),
    path("", include("news.urls")),
]
