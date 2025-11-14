from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("interviews/", include("interviews.urls")),

    # Home -> Landing Magneto usando landing_view
    path("", accounts_views.landing_view, name="landing"),
]
