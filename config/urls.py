from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include Simulator
    path('simulator/', include('apps.simulator.urls', namespace='simulator')),
    
    # Include Encyclopedia
    path('encyclopedia/', include('apps.encyclopedia.urls', namespace='encyclopedia')),
    
    # Include Core (Home, Auth, Profile, Materials)
    # Put this last so it handles the root URL ''
    path('', include('apps.core.urls')),
    
    # Auth URLs (Django defaults for password reset etc, if needed beyond core.urls)
    path('auth/', include('django.contrib.auth.urls')),
]
