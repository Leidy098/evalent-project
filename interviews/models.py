from django.db import models
from django.contrib.auth.models import User


class Interview(models.Model):
    MODE_CHOICES = [
        ("questions", "Por número de preguntas"),
        ("time", "Por tiempo"),
    ]

    INTERVIEW_TYPES = [
        ("job", "Trabajo"),
        ("academic", "Académica"),
        ("scholarship", "Beca"),
        ("informal", "Informal"),
    ]

    LANGUAGES = [
        ("es", "Español"),
        ("en", "Inglés"),
    ]

    LEVELS = [
        ("junior", "Junior"),
        ("semi", "Semi-Senior"),
        ("senior", "Senior"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    language = models.CharField(max_length=10, choices=LANGUAGES, default="es")
    level = models.CharField(max_length=20, choices=LEVELS, default="junior")
    position = models.CharField(max_length=100)

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="questions")
    max_questions = models.IntegerField(null=True, blank=True)
    time_limit = models.IntegerField(null=True, blank=True)  # en minutos

    created_at = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default=False)
    asked_questions = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.get_interview_type_display()} ({self.position})"


class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "Usuario"),
        ("ai", "Entrevistador IA"),
        ("feedback", "Consejo IA"),
    ]

    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"


class Score(models.Model):
    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="score")
    claridad = models.IntegerField(default=0)
    confianza = models.IntegerField(default=0)
    contenido = models.IntegerField(default=0)
    creatividad = models.IntegerField(default=0)
    lenguaje = models.IntegerField(default=0)

    def average(self):
        return (self.claridad + self.confianza + self.contenido + self.creatividad + self.lenguaje) / 5
