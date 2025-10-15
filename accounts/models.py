from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ("candidate", "Candidato"),
        ("recruiter", "Reclutador"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="candidate")
    experience_level = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username
