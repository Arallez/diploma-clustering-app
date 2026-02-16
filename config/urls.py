from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Симулятор — только песочница (точки, алгоритмы)
    path('simulator/', include('apps.simulator.urls', namespace='simulator')),
    # Задачи — список заданий и страница задания
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    
    # Include Encyclopedia
    path('encyclopedia/', include('apps.encyclopedia.urls', namespace='encyclopedia')),
    # Testing (groups and timed tests)
    path('testing/', include('apps.testing.urls', namespace='testing')),
    
    # Редиректы со старых URL авторизации на актуальные (чтобы /auth/login/ и закладки работали)
    path('auth/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('auth/logout/', RedirectView.as_view(url='/logout/', permanent=False)),
    
    # Include Core (Home, Auth, Profile, Materials)
    path('', include('apps.core.urls')),
]
