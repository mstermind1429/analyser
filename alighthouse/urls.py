from django.urls import path

from . import views
from .api import views as api_views

urlpatterns = [
    path('lighthouse/', views.lighthouse, name='lighthouse'),
    path('domain_lighthouse/', views.domain_lighthouse, name='domain_lighthouse'),

    path('api/v1/getReport', api_views.ReportAPI.as_view(), name='ReportAPI'),
    path('api/v1/domainLighthouse', api_views.DomainLighthouseAnalysis.as_view(),
         name='domainLighthouse'),
]
