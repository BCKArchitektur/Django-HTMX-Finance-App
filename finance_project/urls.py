from django.contrib import admin
from django.urls import path, include
from django.conf import settings


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('tracker.urls')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
