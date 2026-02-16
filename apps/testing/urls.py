from django.urls import path
from . import views

app_name = 'testing'

urlpatterns = [
    path('', views.testing_home, name='home'),
    path('join/', views.join_group, name='join_group'),
    path('groups/create/', views.create_group, name='create_group'),
    path('tests/create/', views.create_test, name='create_test'),
    path('tests/<int:test_id>/start/', views.start_test, name='start_test'),
    path('attempt/<int:attempt_id>/', views.take_test, name='take_test'),
    path('attempt/<int:attempt_id>/submit/', views.submit_test, name='submit_test'),
    path('tests/<int:test_id>/results/', views.test_results, name='test_results'),
]
