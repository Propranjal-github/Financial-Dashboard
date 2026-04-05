"""
Root URL configuration for finance_dashboard project.
API endpoints under /api/v1/, frontend pages at root level.
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')
    return redirect('frontend:login')


urlpatterns = [
    # Frontend pages
    path('', root_redirect, name='root'),
    path('', include('frontend.urls')),
    # Admin
    path('admin/', admin.site.urls),
    # API
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/records/', include('records.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
]

