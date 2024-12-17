from django.urls import path
from . import views 
urlpatterns = [
    # All Available Schedule 
    path('availability', views.manage_availability, name="manage-availability"),
    path('all_sched', views.all_sched, name='all_sched'),
    # path('add_sched', views.add_sched, name='add_sched'), 
    # path('update_sched', views.update_sched, name='update_sched'),
    # path('remove_sched', views.remove_sched, name='remove_sched'),
    
    # path('delete_all_free_schedules', views.delete_all_free_schedules, name='delete_all_free_schedules'),
    # path('create_schedule', views.create_schedule, name='create_schedule'),

    # path('view_free_schedules', views.view_free_schedules, name="view-free-schedules"),
    # path('filter-by-defense-application/', views.filter_schedules_by_defense, name='filter_schedules_by_defense'),
]
