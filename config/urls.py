"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import home

from core.views import superadmin_dashboard

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('core/', include('core.urls')),
    path('superadmin/', superadmin_dashboard, name='superadmin_dashboard'),
]
