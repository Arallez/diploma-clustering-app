from django.urls import path
from .views import simulator_view, challenge_view, RunKMeans, CheckSolution

urlpatterns = [
    path('', simulator_view, name='simulator_index'),
    path('challenge/', challenge_view, name='challenge_index'),
    path('api/run-kmeans/', RunKMeans.as_view(), name='run_kmeans'),
    path('api/check-solution/', CheckSolution.as_view(), name='check_solution'),
]
