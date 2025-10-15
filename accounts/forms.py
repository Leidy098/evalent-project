from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=(("candidate","Candidato"),("recruiter","Reclutador")), required=False)
    experience_level = forms.CharField(required=False, max_length=50)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "role", "experience_level")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            try:
                from .models import Profile
                Profile.objects.create(
                    user=user,
                    role=self.cleaned_data.get("role") or "candidate",
                    experience_level=self.cleaned_data.get("experience_level") or ""
                )
            except Exception:
                pass
        return user
