from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # SOC Manager admin panel
    path('soc-admin/', views.admin_panel, name='admin_panel'),

    # Organization management
    path('soc-admin/org/create/', views.org_create, name='org_create'),
    path('soc-admin/org/<uuid:org_id>/edit/', views.org_edit, name='org_edit'),
    path('soc-admin/org/<uuid:org_id>/delete/', views.org_delete, name='org_delete'),

    # User management
    path('soc-admin/user/create/', views.user_create, name='user_create'),
    path('soc-admin/user/<uuid:user_id>/edit/', views.user_edit, name='user_edit'),
    path('soc-admin/user/<uuid:user_id>/delete/', views.user_delete, name='user_delete'),
]
