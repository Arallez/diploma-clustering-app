from django.urls import path
from . import views

app_name = 'simulator'

urlpatterns = [
    path('', views.simulator_index, name='index'),
    path('tasks/', views.task_list, name='task_list'),
    path('challenge/<slug:slug>/', views.challenge_detail, name='challenge_detail'),
    
    # API endpoints
    path('api/run-kmeans/', views.run_kmeans, name='run_kmeans'),
    path('api/run-dbscan/', views.run_dbscan, name='run_dbscan'),
    path('api/check-solution/', views.check_solution, name='check_solution'),
]
