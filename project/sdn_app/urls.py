from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('block_ip', views.block_ip, name='block_ip'),
    path('unblock_ip', views.unblock_ip, name='unblock_ip'),
    path('api/topology', views.api_topology, name='api_topology'),
    path('api/traffic_stats', views.api_traffic_stats, name='api_traffic_stats'),
    path('api/port_control', views.api_port_control, name='api_port_control'),
    path('api/ping_test', views.api_ping_test, name='api_ping_test'),
]
