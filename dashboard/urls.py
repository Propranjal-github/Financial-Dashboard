from django.urls import path

from . import views

urlpatterns = [
    path('summary/', views.SummaryView.as_view(), name='dashboard_summary'),
    path('analytics/', views.AnalyticsView.as_view(), name='dashboard_analytics'),
    path('time-analytics/', views.TimeAnalyticsView.as_view(), name='time_analytics'),
]
