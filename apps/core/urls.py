from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Import recommendation view — function is called recommendations_view
from apps.encyclopedia.views import recommendations_view

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    
    # Materials
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/<slug:slug>/', views.material_detail, name='material_detail'),
    
    # Learning Path (Recommendations) — standalone, not inside encyclopedia
    path('learning-path/', recommendations_view, name='learning_path'),
    
    # Secure built-in Django auth views
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
