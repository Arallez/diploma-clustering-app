from django.urls import path
from .views import RunKMeans, simulator_view

urlpatterns = [
    path('', simulator_view, name='simulator_index'),
    path('api/run-kmeans/', RunKMeans.as_view(), name='run_kmeans'),
]
