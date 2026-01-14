from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('simulator/', include(('apps.simulator.urls', 'simulator'), namespace='simulator')),
    path('', include('apps.core.urls')),
]
