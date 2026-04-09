from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('monitoring/', views.monitoring, name='monitoring'),
    path('api/topology', views.api_topology, name='api_topology'),
    path('api/traffic_stats', views.api_traffic_stats, name='api_traffic_stats'),
    path('api/port_control', views.api_port_control, name='api_port_control'),
]
