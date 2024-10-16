from django.urls import path 
from . import views 

urlpatterns = [
#    path('', views.index, name='index'), 
    path('login_user', views.login_user, name="login"), 
    path('logout_user', views.logout_user, name='logout'),
    #path('register_user', views.register_user, name='register_user'),
    path('register_student', views.register_student, name='register_student'),
    path('register_faculty', views.register_faculty, name='register_faculty'),
    #path('register_user', views.register_user, name='register_user'),
    path('update_user', views.update_user, name='update-user'),
 ]
