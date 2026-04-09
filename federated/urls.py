from django.urls import path
from . import views

app_name = 'federated'

urlpatterns = [
    path('', views.federation_overview, name='overview'),
    path('api/trigger-round/', views.api_trigger_round, name='api_trigger_round'),
    path('api/nodes/', views.api_node_status, name='api_nodes'),
]
