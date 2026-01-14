from django.urls import path
from .views import simulator_view, challenge_view, tasks_view, RunKMeans, CheckSolution

app_name = 'simulator'

urlpatterns = [
    path('', simulator_view, name='simulator_index'),
    path('tasks/', tasks_view, name='task_list'),
    path('challenge/', challenge_view, name='challenge_start'),
    path('challenge/<slug:slug>/', challenge_view, name='challenge_detail'),
    
    path('api/run-kmeans/', RunKMeans.as_view(), name='run_kmeans'),
    path('api/check-solution/', CheckSolution.as_view(), name='check_solution'),
]
