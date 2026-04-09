from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.local_node_view, name='local_node'),
    path('api/simulate/', views.api_simulate_ingestion, name='api_simulate'),
    path('api/stream/', views.api_log_stream, name='api_stream'),
]
