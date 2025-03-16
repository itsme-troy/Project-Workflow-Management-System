from django.urls import path
from . import views 
urlpatterns = [
    # All Available Schedule 
    # in view schedule,
    #  add defense schedules 
    # create, delete function 

    path('view_schedule/', views.view_schedule, name="view-schedule"),
    path('all_sched/', views.all_sched, name='all_sched'),
    path('update_faculty_color/', views.update_faculty_color, name='update_faculty_color'),
    path('calculate_common_schedules/', views.calculate_common_schedules, name='calculate_common_schedule'),
    # path('add_sched', views.add_sched, name='add_sched'),
    # path('delete_all_defense_schedules', views.delete_all_defense_schedules, name='delete_all_defense_schedules'),
    path('create_defense_sched/', views.create_defense_schedule, name='create_defense_schedule'),
    path('update-common-schedule-color/', views.update_common_schedule_color, name='update-common-schedule-color'),

   ]
