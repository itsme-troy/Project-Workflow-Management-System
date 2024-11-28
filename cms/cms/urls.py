from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 

# from .views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("project.urls")),
    path('users/', include('django.contrib.auth.urls')), # gonna deal w/ authentication
    path('users/', include('users.urls')), 
    path('calendar_app/', include('calendar_app.urls')), 
    path('free_schedule/', include('free_schedule.urls')), 
    path('common_schedule/', include('common_schedule.urls')),

    
    # path("calendarapp", include("calendarapp.urls")),
    # path('google_calendar/', include('google_calendar.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configure Admin Titles
admin.site.site_header = "Capstone Management System Page"
admin.site.index_title = "Welcome to the Admin Area"