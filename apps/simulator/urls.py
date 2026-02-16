from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'simulator'

urlpatterns = [
    # Песочница: одна страница + API для запуска алгоритмов
    path('', views.index, name='index'),
    path('run/', views.run_algorithm, name='run_algorithm'),

    # Редиректы со старых URL заданий на /tasks/
    path('tasks/', RedirectView.as_view(url='/tasks/', permanent=False)),
    path('challenge/<slug:slug>/', views._redirect_legacy_challenge),

    # Legacy/Individual API endpoints
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
