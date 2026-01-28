from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('simulator/', include('apps.simulator.urls', namespace='simulator')),
    path('encyclopedia/', include('apps.encyclopedia.urls', namespace='encyclopedia')),
    
    # Auth URLs with custom template for login
    path('auth/login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('auth/', include('django.contrib.auth.urls')), # Include other auth urls (logout, password reset, etc.)
    
    path('profile/', core_views.profile, name='profile'),
    path('register/', core_views.register, name='register'),
]
