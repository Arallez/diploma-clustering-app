from django.urls import path
from . import views

app_name = 'encyclopedia'

urlpatterns = [
    path('graph/', views.ontology_graph_view, name='graph'),
    path('concept/<int:pk>/', views.concept_detail_view, name='detail'),
    path('api/knowledge-state/', views.get_user_knowledge_state, name='api_knowledge_state'),
]