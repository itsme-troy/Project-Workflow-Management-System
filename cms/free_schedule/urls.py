from django.urls import path

from . import views 
urlpatterns = [
    # All Available Schedule 
    path('free_schedule', views.free_sched, name="free-schedule"),
    path('all_sched', views.all_sched, name='all_sched'),
    path('add_sched', views.add_sched, name='add_sched'), 
    path('update_sched', views.update_sched, name='update_sched'),
    path('remove_sched', views.remove_sched, name='remove_sched'),

]
