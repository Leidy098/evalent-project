from django.urls import path
from . import views

app_name = "interviews"

urlpatterns = [
    path("", views.interview_list, name="interview_list"),
    path("create/", views.interview_create, name="interview_create"),
    path("<int:pk>/", views.interview_detail, name="interview_detail"),
    path("<int:pk>/finish/", views.interview_finish, name="interview_finish"),
    path("<int:pk>/delete/", views.interview_delete, name="interview_delete"),
    path("<int:pk>/results/", views.interview_results, name="interview_results"),

    # 👇 AGREGA ESTA LÍNEA NUEVA
    path("<int:pk>/export-pdf/", views.interview_export_pdf, name="interview_export_pdf"),
]
