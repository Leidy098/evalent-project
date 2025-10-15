from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),   # 👈 importante
    path("interviews/", include("interviews.urls")),
    path("", include("accounts.urls")),  # para que / redirija a login
]




