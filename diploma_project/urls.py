"""diploma_project URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('simulator/', include('simulator.urls', namespace='simulator')),
    path('encyclopedia/', include('encyclopedia.urls', namespace='encyclopedia')),
    path('materials/', include('learning_materials.urls')),
    path('testing/', include('testing.urls')),
    path('tasks/', include('tasks.urls', namespace='tasks')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)