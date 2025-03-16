from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("project.urls")),
    path('users/', include('django.contrib.auth.urls')), 
    path('users/', include('users.urls')), 
    path('free_schedule/', include('free_schedule.urls')), 
    path('defense_schedule/', include('defense_schedule.urls')),
    path('mutual_availability/', include('mutual_availability.urls')),
]

# Properly serve static files during development
# Add Debug Toolbar only if DEBUG is True
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# Configure Admin Titles
admin.site.site_header = "SP System Page"
admin.site.index_title = "Welcome to the Admin Area"
