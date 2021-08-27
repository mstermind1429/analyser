from django.urls import path

from . import views
from .api import views as api_views

urlpatterns = [
    path('scraping_tool/', views.scraping_tool, name='scraping_tool'),
    path('html/', views.html_tool, name='html_tool'),
    path('lcp/', views.lcp_page, name='lcp_page'),
    path('fid/', views.fid_page, name='fid_page'),
    path('cls_page/', views.cls_page, name='cls_page'),

    path('api/v1/checkHTML', api_views.HtmlSnippetAPI.as_view(), name='HtmlSnippetAPI'),
    path('api/v1/getHTML', api_views.HtmlToolAPI.as_view(), name='HtmlToolAPI'),
]