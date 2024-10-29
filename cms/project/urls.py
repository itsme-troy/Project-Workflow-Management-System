from django.urls import path
from . import views

urlpatterns = [
#    path('profile_list/', views.profile_list, name='profile_list'),
#   path('profile/<int:pk>', views.profile, name='profile'),

    path("", views.home, name="home"),
    path('projects', views.all_projects, name="list-projects"),
    path('proposals', views.all_proposals, name="list-proposals"),
    path('show_project/<project_id>', views.show_project, name='show-project'),
    path('show_proposal/<project_id>', views.show_proposal, name='show-proposal'),
    path('add_project', views.add_project, name="add-project"),
    path('list-faculty', views.list_faculty, name="list-faculty"),
    path('list-student', views.list_student, name="list-student"),
    path('search_projects', views.search_projects, name="search-projects"),
    path('update_project/<project_id>', views.update_project, name='update-project'),
    path('delete_project/<project_id>', views.delete_project, name='delete-project'),
    path('update_proposal/<project_id>', views.update_proposal, name='update-proposal'),
    path('delete_proposal/<project_id>', views.delete_proposal, name='delete-proposal'),
    path('accept_proposal/<project_id>', views.accept_proposal, name='accept-proposal'),
    path('reject_project/<project_id>', views.reject_project, name='reject-project'),
    path('adviser_projects', views.adviser_projects, name='adviser-projects'),
    path('coordinator_approval', views.coordinator_approval, name='coordinator_approval'),
    
    path('submit_defense_application', views.submit_defense_application, name='submit-defense-application'),
    path('defense_applications', views.list_defense_applications, name='list-defense-applications'),
    path('submit_verdict/<int:application_id>/', views.submit_verdict, name='submit_verdict'),
    
    path('generate_report', views.generate_report, name='generate-report'),
    path('show_student/<student_id>', views.show_student, name='show-student'),
    path('add_project_group', views.add_project_group, name="add-project-group"),
    # path('my_student_profile/<profile_id>', views.my_student_profile, name="my-student-profile"), 
    path('my_profile/<profile_id>', views.my_profile, name="my-profile"), 
    path('show_faculty/<faculty_id>', views.show_faculty, name='show-faculty'),
    path('update_deficiencies/<student_id>', views.update_deficiencies, name='update_deficiencies'), 
    path('list_project_group', views.list_project_group, name='list-project-group'), 
    path('list_project_group_waitlist', views.list_project_group_waitlist, name='list-project-group-waitlist'), 
    path('approve_project_group/<group_id>', views.approve_project_group, name='approve-project-group'), 
    path('reject_project_group/<group_id>', views.reject_project_group, name='reject-project-group'),
    path('delete_project_group/<group_id>', views.delete_project_group, name='delete-project-group'),
  
]
