from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/metrics/', views.api_metrics, name='api_metrics'),
    path('api/alerts/', views.api_alerts, name='api_alerts'),
]
