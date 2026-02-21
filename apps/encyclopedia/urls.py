from django.urls import path
from . import views

app_name = 'encyclopedia'

urlpatterns = [
    path('', views.graph_view, name='graph'),
    path('concept/<int:pk>/', views.concept_detail, name='detail'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
]
