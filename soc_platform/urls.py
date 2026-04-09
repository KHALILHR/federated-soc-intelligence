"""Root URL configuration for soc_platform."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('users/', include('users.urls')),
    path('logs/', include('logs.urls')),
    path('threats/', include('threat_detection.urls')),
    path('federation/', include('federated.urls')),
]
