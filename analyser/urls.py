from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("core.urls")),
    path('', include("alighthouse.urls")),
    path('', include("htmltool.urls")),
    path('', include("keywords.urls")),
    path('', include("ml.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.REPORT_URL, document_root=settings.REPORT_PATH)
