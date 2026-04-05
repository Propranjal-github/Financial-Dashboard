from django.urls import path

from . import views

app_name = 'frontend'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('records/', views.records_view, name='records'),
    path('records/create/', views.record_create_view, name='record_create'),
    path('users/', views.users_view, name='users'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    path('analytics/', views.analytics_view, name='analytics'),
]

