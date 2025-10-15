from django import forms
from .models import Interview


class InterviewForm(forms.ModelForm):
    """
    Formulario para crear una entrevista.
    Valida que según el modo seleccionado (por preguntas o por tiempo),
    se exija el campo correcto.
    """

    class Meta:
        model = Interview
        fields = [
            "interview_type",
            "language",
            "level",
            "position",
            "mode",
            "max_questions",
            "time_limit",
        ]

        widgets = {
            "interview_type": forms.Select(attrs={"class": "form-control"}),
            "language": forms.Select(attrs={"class": "form-control"}),
            "level": forms.Select(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "mode": forms.Select(attrs={"class": "form-control"}),
            "max_questions": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "placeholder": "Ej: 5"}
            ),
            "time_limit": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "placeholder": "Ej: 10"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("mode")
        max_q = cleaned_data.get("max_questions")
        time_limit = cleaned_data.get("time_limit")

        # Si es por número de preguntas y no se ingresó max_questions
        if mode == "questions" and not max_q:
            self.add_error("max_questions", "Debes ingresar el número de preguntas.")

        # Si es por tiempo y no se ingresó time_limit
        elif mode == "time" and not time_limit:
            self.add_error("time_limit", "Debes ingresar el límite de tiempo en minutos.")

        return cleaned_data
