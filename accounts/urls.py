from django.urls import path
from . import views

urlpatterns = [
    path('login/admin/', views.admin_login, name='admin_login'),
    path('register/admin/', views.admin_register, name='admin_register'),
    path('login/coder/', views.coder_login, name='coder_login'),
    path('register/coder/', views.coder_register, name='coder_register'),
    path('logout/', views.custom_logout, name='logout'),
]
