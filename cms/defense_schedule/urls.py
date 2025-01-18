from django.urls import path
from . import views 
from mutual_availability.views import view_schedule, calculate_common_schedules
from django.urls import include

urlpatterns = [
    # Defenses  
    path('defense_schedule', views.defense_sched, name="defense-schedule"),
    path('view_defense_schedule', views.view_defense_schedule, name="view-defense-schedule"),
    
    
    path('all_sched', views.all_sched, name='all_sched'),
    path('add_sched', views.add_sched, name='add_sched'), 
    path('update_sched', views.update_sched, name='update_sched'),
    path('remove_sched', views.remove_sched, name='remove_sched'),
    
    path('delete_all_defense_schedules', views.delete_all_defense_schedules, name='delete_all_defense_schedules'),
    path('create_defense_schedule', views.create_defense_schedule, name='create_defense_schedule'),
    
    # DEFENSE SCHEDULE 
    
    # path('view_schedule', view_schedule, name='view-schedule'),
    # path('mutual_availability/', include('mutual_Availability.urls')),
    
]
