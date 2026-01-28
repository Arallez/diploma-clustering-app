from django.contrib import admin
from django.urls import path, include
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('simulator/', include('apps.simulator.urls', namespace='simulator')),
    path('encyclopedia/', include('apps.encyclopedia.urls', namespace='encyclopedia')),
    path('auth/', include('django.contrib.auth.urls')),
    path('profile/', core_views.profile, name='profile'),
    path('register/', core_views.register, name='register'),
]
