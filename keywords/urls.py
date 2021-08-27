from django.urls import path

from . import views
from .api import views as api_views

urlpatterns = [
    path('csv/', views.csv, name='csv'),
    path('key_patterns/', views.key_patterns, name='key_patterns'),
    path('keyword_search/', views.keyword_search, name='keyword_search'),
    path('searchmetrics_tool/', views.searchmetrics_tool, name='searchmetrics_tool'),
    path('domain_searchmetrics/', views.domain_searchmetrics, name='domain_searchmetrics'),
    path('search_volume/', views.search_volume, name='search_volume'),
    path('keyword_domain/', views.keyword_domain, name='keyword_domain'),
    path('category_domain/', views.category_domain, name='category_domain'),

    path('api/v1/getKeyPatterns', api_views.KeyPatternExtractionAPI.as_view(),
         name='KeyPatternExtractionAPI'),
    path('api/v1/searchKeywords', api_views.KeywordSearchAPI.as_view(), name='KeywordSearchAPI'),
    path('api/v1/getWordCount', api_views.WordsCountAPI.as_view(), name='WordsCountAPI'),
    path('api/v1/getTrafficCount', api_views.TrafficCountAPI.as_view(), name='TrafficCountAPI'),
    path('api/v1/getSearchCount', api_views.SearchCountAPI.as_view(), name='SearchCountAPI'),
    path('api/v1/getSearchMetrics', api_views.SearchMetricsAPI.as_view(), name='SearchMetricsAPI'),
    path('api/v1/getExampleKeywords', api_views.ExampleKeywordsAPI.as_view(), name='ExampleKeywordsAPI'),
    path('api/v1/getSimilarKeywords', api_views.SimilarKeywordsAPI.as_view(), name='SimilarKeywordsAPI'),
    path('api/v1/getExampleURLKeywords', api_views.ExampleURLKeywordsAPI.as_view(),
         name='ExampleURLKeywordsAPI'),
    path('api/v1/searchMetricsToolAPI', api_views.SearchMetricsToolAPI.as_view(),
         name='SearchMetricsToolAPI'),
    path('api/v1/domainSearchmetrics', api_views.DomainSearchmetricsAnalysis.as_view(),
         name='DomainSearchmetricsAnalysis'),
    path('api/v1/keywordDomain', api_views.KeywordDomain.as_view(),
         name='keywordDomain'),
    path('api/v1/categoryDomain', api_views.CategoryDomainAPI.as_view(), name='categoryDomain'),
    path('api/v1/searchVolume', api_views.GetSearchVolumeAPI.as_view(),
         name='GetSearchVolumeAPI'),
]