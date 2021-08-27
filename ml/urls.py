from django.urls import path

from . import views
from .api import views as api_views

urlpatterns = [
    path('casual_impact/', views.casual_impact, name='casual_impact'),
    path('api/v1/casualImpact', api_views.CasualImpactAPI.as_view(), name='casual_impact'),
]
