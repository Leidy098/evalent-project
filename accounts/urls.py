from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Rutas públicas
    path("", views.landing_view, name="landing"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    
    # Rutas de administrador (ESTAS FALTAN)
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-interviews/", views.admin_all_interviews, name="admin_interviews"),
    path("admin-users/", views.admin_all_users, name="admin_users"),
]