from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include Simulator
    path('simulator/', include('apps.simulator.urls', namespace='simulator')),
    
    # Include Encyclopedia
    path('encyclopedia/', include('apps.encyclopedia.urls', namespace='encyclopedia')),
    
    # Редиректы со старых URL авторизации на актуальные (чтобы /auth/login/ и закладки работали)
    path('auth/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('auth/logout/', RedirectView.as_view(url='/logout/', permanent=False)),
    
    # Include Core (Home, Auth, Profile, Materials)
    path('', include('apps.core.urls')),
]
