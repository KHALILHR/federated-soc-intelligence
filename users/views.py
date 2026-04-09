import functools

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrganizationForm, UserCreateForm, UserEditForm
from .models import Organization, User


# ---------------------------------------------------------------------------
# Helpers / decorators
# ---------------------------------------------------------------------------

def soc_manager_required(view_func):
    """Decorator: allow only authenticated SOC Managers."""
    @functools.wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.SOC_MANAGER:
            messages.error(request, 'Access denied. SOC Manager role required.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Authentication views
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SOC Manager admin panel
# ---------------------------------------------------------------------------

@soc_manager_required
def admin_panel(request):
    """Main SOC Manager admin panel: lists orgs and users in own org."""
    manager_org = request.user.organization
    organizations = Organization.objects.all()
    # Filter users to the manager's own organization only
    if manager_org:
        org_users = User.objects.filter(organization=manager_org).exclude(pk=request.user.pk)
    else:
        org_users = User.objects.none()
    return render(request, 'users/admin_panel.html', {
        'organizations': organizations,
        'org_users': org_users,
        'manager_org': manager_org,
    })


# --- Organization CRUD ---

@soc_manager_required
def org_create(request):
    """Create a new organization."""
    form = OrganizationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Organization created successfully.')
        return redirect('users:admin_panel')
    return render(request, 'users/org_form.html', {'form': form, 'action': 'Create'})


@soc_manager_required
def org_edit(request, org_id):
    """Edit an existing organization."""
    org = get_object_or_404(Organization, pk=org_id)
    form = OrganizationForm(request.POST or None, instance=org)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Organization "{org.name}" updated.')
        return redirect('users:admin_panel')
    return render(request, 'users/org_form.html', {'form': form, 'action': 'Edit', 'org': org})


@soc_manager_required
def org_delete(request, org_id):
    """Delete an organization (POST only)."""
    org = get_object_or_404(Organization, pk=org_id)
    if request.method == 'POST':
        org_name = org.name
        org.delete()
        messages.success(request, f'Organization "{org_name}" deleted.')
    return redirect('users:admin_panel')


# --- User CRUD (scoped to manager's org) ---

@soc_manager_required
def user_create(request):
    """Create a new user in the manager's organization."""
    manager_org = request.user.organization
    if not manager_org:
        messages.error(request, 'You must be assigned to an organization before managing users.')
        return redirect('users:admin_panel')
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_user = form.save(commit=False)
        new_user.organization = manager_org
        new_user.set_password(form.cleaned_data['password'])
        new_user.save()
        messages.success(request, f'User "{new_user.username}" created.')
        return redirect('users:admin_panel')
    return render(request, 'users/user_form.html', {
        'form': form,
        'action': 'Create',
        'manager_org': manager_org,
    })


@soc_manager_required
def user_edit(request, user_id):
    """Edit a user within the manager's organization."""
    manager_org = request.user.organization
    if not manager_org:
        messages.error(request, 'You must be assigned to an organization before managing users.')
        return redirect('users:admin_panel')
    target_user = get_object_or_404(User, pk=user_id, organization=manager_org)
    form = UserEditForm(request.POST or None, instance=target_user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'User "{target_user.username}" updated.')
        return redirect('users:admin_panel')
    return render(request, 'users/user_form.html', {
        'form': form,
        'action': 'Edit',
        'target_user': target_user,
        'manager_org': manager_org,
    })


@soc_manager_required
def user_delete(request, user_id):
    """Delete a user within the manager's organization (POST only)."""
    manager_org = request.user.organization
    if not manager_org:
        messages.error(request, 'You must be assigned to an organization before managing users.')
        return redirect('users:admin_panel')
    target_user = get_object_or_404(User, pk=user_id, organization=manager_org)
    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'User "{username}" deleted.')
    return redirect('users:admin_panel')
