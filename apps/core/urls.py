from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Import recommendation view here to put it in the base namespace
from apps.encyclopedia.views import get_learning_recommendations

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    
    # Materials
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/<slug:slug>/', views.material_detail, name='material_detail'),
    
    # Learning Path (Recommendations)
    path('learning-path/', get_learning_recommendations, name='learning_path'),
    
    # Secure built-in Django auth views
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
