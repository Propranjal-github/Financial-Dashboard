from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('', views.FinancialRecordViewSet, basename='financial-record')

urlpatterns = [
    path('', include(router.urls)),
]
