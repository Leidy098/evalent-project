from django.contrib import admin
from .models import Interview, Message, Score

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("user", "position", "interview_type", "language", "level", "mode", "created_at", "is_finished")
    list_filter = ("interview_type", "language", "level", "mode", "is_finished")
    search_fields = ("position", "user__username")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("interview", "role", "content", "timestamp")
    list_filter = ("role",)
    search_fields = ("content",)

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("message", "claridad", "confianza", "contenido", "creatividad", "lenguaje")
