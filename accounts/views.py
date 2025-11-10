from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm


def landing_view(request):
    return render(request, "landing.html")


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"user": request.user})


# ==================== FUNCIONES DE ADMINISTRADOR ====================

def is_admin(user):
    """Verifica si el usuario es administrador o reclutador"""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'recruiter')


@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard principal del administrador"""
    from interviews.models import Interview
    from django.contrib.auth.models import User
    
    total_users = User.objects.count()
    total_interviews = Interview.objects.count()
    finished_interviews = Interview.objects.filter(is_finished=True).count()
    active_interviews = Interview.objects.filter(is_finished=False).count()
    
    recent_interviews = Interview.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_interviews': total_interviews,
        'finished_interviews': finished_interviews,
        'active_interviews': active_interviews,
        'recent_interviews': recent_interviews,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@user_passes_test(is_admin)
def admin_all_interviews(request):
    """Vista de todas las entrevistas para administrador"""
    from interviews.models import Interview
    interviews = Interview.objects.select_related('user').order_by('-created_at')
    return render(request, 'accounts/admin_interviews.html', {'interviews': interviews})


@user_passes_test(is_admin)
def admin_all_users(request):
    """Vista de todos los usuarios para administrador"""
    from django.contrib.auth.models import User
    users = User.objects.prefetch_related('interview_set', 'profile').order_by('-date_joined')
    return render(request, 'accounts/admin_users.html', {'users': users})