from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('coder-dashboard/', views.coder_dashboard, name='coder_dashboard'),
    path('code/<int:question_id>/', views.coding_environment, name='coding_environment'),
    path('code/<int:question_id>/decrement_points/', views.decrement_points, name='decrement_points'),
    path('execute/', views.execute_code, name='execute_code'),
    path('leaderboard/<int:question_id>/', views.get_leaderboard, name='get_leaderboard'),
    path('close-question/<int:question_id>/', views.close_question, name='close_question'),
    path('approve-coder/<int:coder_id>/', views.approve_coder, name='approve_coder'),
    path('approve-admin/<int:admin_id>/', views.approve_admin, name='approve_admin'),
]
