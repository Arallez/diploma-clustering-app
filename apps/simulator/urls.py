from django.urls import path
from . import views

app_name = 'simulator'

urlpatterns = [
    # Pages
    path('', views.index, name='index'), # Renamed back to index
    path('tasks/', views.task_list, name='task_list'),
    path('challenge/<slug:slug>/', views.challenge_detail, name='challenge_detail'),
    
    # Unified API endpoint
    path('run/', views.run_algorithm, name='run_algorithm'),
    
    # Legacy/Individual API endpoints (for backward compatibility)
    path('api/run-kmeans/', views.run_kmeans, name='run_kmeans'),
    path('api/run-dbscan/', views.run_dbscan, name='run_dbscan'),
    path('api/run-forel/', views.run_forel, name='run_forel'),
    path('api/run-agglomerative/', views.run_agglomerative, name='run_agglomerative'),
    
    # Utilities
    path('dendrogram/', views.get_dendrogram, name='get_dendrogram'),
    path('preset/', views.get_preset, name='get_preset'),
    
    # Old long paths just in case
    path('api/get-dendrogram/', views.get_dendrogram, name='api_get_dendrogram'),
    path('api/generate-preset/', views.get_preset, name='api_get_preset'),
]
