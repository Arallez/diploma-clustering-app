from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('simulator/', include('apps.simulator.urls')),
    path('', RedirectView.as_view(url='/simulator/', permanent=False)),
]
