from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    """SOC Platform login page."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials. Access denied.')

    return render(request, 'users/login.html')


def logout_view(request):
    """Log the user out and redirect to login."""
    logout(request)
    return redirect('users:login')


@login_required
def profile_view(request):
    """User profile and settings."""
    return render(request, 'users/profile.html')
