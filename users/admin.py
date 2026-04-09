from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'is_active', 'joined_at')
    search_fields = ('name', 'domain')
    list_filter = ('is_active',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'organization', 'clearance_level', 'is_active')
    list_filter = ('role', 'clearance_level', 'organization', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SOC Profile', {
            'fields': ('role', 'organization', 'assigned_node', 'clearance_level', 'mfa_enabled'),
        }),
    )
