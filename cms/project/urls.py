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
    path('list-student-waitlist', views.list_student_waitlist, name="list-student-waitlist"),
    
    
    path('search_projects', views.search_projects, name="search-projects"),
    path('update_project/<project_id>', views.update_project, name='update-project'),
    path('delete_project/<project_id>', views.delete_project, name='delete-project'),
    path('update_proposal/<project_id>', views.update_proposal, name='update-proposal'),
    path('delete_proposal/<project_id>', views.delete_proposal, name='delete-proposal'),
    path('accept_proposal/<project_id>', views.accept_proposal, name='accept-proposal'),
    path('reject_project/<project_id>', views.reject_project, name='reject-project'),
    
    path('adviser_projects', views.adviser_projects, name='adviser-projects'),
    path('adviser_proposals', views.adviser_proposals, name='adviser-proposals'),
    

    path('coordinator_approval_faculty', views.coordinator_approval_faculty, name='coordinator-approval-faculty'),
    path('coordinator_approval_student', views.coordinator_approval_student, name='coordinator-approval-student'),
    path('select_coordinator', views.select_coordinator, name='select-coordinator'),
    
    path('my_defense_application', views.my_defense_application, name='my-defense-application'),
    path('submit_defense_application', views.submit_defense_application, name='submit-defense-application'),
    path('defense_applications', views.list_defense_applications, name='list-defense-applications'),
    path('submit_verdict/<int:application_id>/', views.submit_verdict, name='submit_verdict'),
    
    path('generate_report', views.generate_report, name='generate-report'),
    path('show_student/<student_id>', views.show_student, name='show-student'),

    path('add_project_group', views.add_project_group, name="add-project-group"),
    path('list_project_group', views.list_project_group, name='list-project-group'), 
    path('my_project_group_waitlist', views.my_project_group_waitlist, name='my-project-group-waitlist'), 
    path('approve-group-membership/<int:group_id>/', views.approve_group_membership, name='approve-group-membership'),
    path('reject-group-membership/<int:group_id>/', views.reject_group_membership, name='reject-group-membership'),
    path('finalize-group/<int:group_id>/', views.finalize_group, name='finalize-group'),
    path('invite-more-members/<int:group_id>/', views.invite_more_members, name='invite-more-members'),
    # path('replace-member/<int:group_id>/<int:member_id>/', views.replace_member, name='replace-member'),
    path('remove-member/<int:group_id>/<int:member_id>/', views.remove_member, name='remove-member'),
    path('leave-group/<int:group_id>/', views.leave_group, name='leave-group'),
    
    path('join_group', views.join_group_list, name='join-group-list'),  # Add this line
    path('request_join_group/<int:group_id>/', views.request_join_group, name='request-join-group'),  # Add this line
    path('cancel-join-request/<int:group_id>/', views.cancel_join_request, name='cancel-join-request'),
    path('accept-join-request/<int:group_id>/<int:user_id>/', views.accept_join_request, name='accept-join-request'),
    path('decline-join-request/<int:group_id>/<int:user_id>/', views.decline_join_request, name='decline-join-request'),
    path('transfer-creator/<int:group_id>/', views.transfer_creator, name='transfer-creator'),
    
    # path('my_student_profile/<profile_id>', views.my_student_profile, name="my-student-profile"), 
    path('my_profile/<profile_id>', views.my_profile, name="my-profile"), 
    path('show_faculty/<faculty_id>', views.show_faculty, name='show-faculty'),
    path('update_deficiencies/<student_id>', views.update_deficiencies, name='update_deficiencies'), 

    path('approve_project_group/<group_id>', views.approve_project_group, name='approve-project-group'), 
    path('reject_project_group/<group_id>', views.reject_project_group, name='reject-project-group'),
    path('delete_project_group/<group_id>', views.delete_project_group, name='delete-project-group'),

    path('get_notifications/', views.get_notifications, name='get_notifications'),
    path('mark_notification_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]
