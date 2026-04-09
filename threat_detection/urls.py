from django.urls import path
from . import views

app_name = 'threat_detection'

urlpatterns = [
    path('', views.threat_intel_hub, name='intel_hub'),
    path('api/score/', views.api_threat_score, name='api_score'),
    path('api/iocs/', views.api_ioc_list, name='api_iocs'),
]
