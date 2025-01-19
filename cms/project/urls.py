from django.urls import path
from . import views

urlpatterns = [

    path("", views.home, name="home"),
    path('list_projects', views.all_projects, name="list-projects"),
    path('proposals', views.all_proposals, name="list-proposals"),
    path('show_project/<project_id>', views.show_project, name='show-project'),
    path('show_proposal/<project_id>', views.show_proposal, name='show-proposal'),
    path('add_project', views.add_project, name="add-project"),
    path('my_project', views.my_project, name='my-project'), 
  
    path('delete_user/<user_id>', views.delete_user, name='delete-user'), 

    path('list-faculty', views.list_faculty, name="list-faculty"),
    path('list-student', views.list_student, name="list-student"),
    path('list-student-waitlist', views.list_student_waitlist, name="list-student-waitlist"),
    
    path('archived_projects', views.list_archived_projects, name='list-archived-projects'), 
    path('archive_project/<project_id>/', views.archive_project, name='archive-project'),
    # path('project/archive/<int:project_id>/', views.archive_proposal, name='archive-proposal'),
    path('unarchive_project/<project_id>/', views.unarchive_project, name='unarchive-project'),
    # path('project/archive/<int:project_id>/', views.unarchive_proposal, name='unarchive-proposal'),
    
    path('search_projects', views.search_projects, name="search-projects"),
    path('select_panelist/<project_id>', views.select_panelist, name='select-panelist'),
    path('select_panelist_coordinator/<project_id>', views.select_panelist_coordinator, name='select-panelist-coordinator'),
    # path('select_defense_phases/<project_id>', views.select_defense_phases, name='select-defense-phases'),
    

    path('delete_project/<project_id>', views.delete_project, name='delete-project'),
    path('add_comments/<project_id>', views.add_comments, name='add-comments'),
    path('delete_proposal/<project_id>', views.delete_proposal, name='delete-proposal'),
    path('student_delete_proposal/<project_id>', views.student_delete_proposal, name='student-delete-proposal'),
    
    path('accept_proposal/<project_id>', views.accept_proposal, name='accept-proposal'),
    path('reject_project/<project_id>', views.reject_project, name='reject-project'),
    path('reject_proposal/<project_id>', views.reject_proposal, name='reject-proposal'),

    path('coordinator_projects', views.coordinator_projects, name='coordinator-projects'),
    path('adviser_projects', views.adviser_projects, name='adviser-projects'),
    path('adviser_proposals', views.adviser_proposals, name='adviser-proposals'),
    path('panel_projects', views.panel_projects, name='panel-projects'),
    
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
    path('remove-member/<int:group_id>/<int:member_id>/', views.remove_member, name='remove-member'),
    path('leave-group/<int:group_id>/', views.leave_group, name='leave-group'),
    
    path('join_group', views.join_group_list, name='join-group-list'),  # Add this line
    path('request_join_group/<int:group_id>/', views.request_join_group, name='request-join-group'),  # Add this line
    path('cancel-join-request/<int:group_id>/', views.cancel_join_request, name='cancel-join-request'),
    path('accept-join-request/<int:group_id>/<int:user_id>/', views.accept_join_request, name='accept-join-request'),
    path('decline-join-request/<int:group_id>/<int:user_id>/', views.decline_join_request, name='decline-join-request'),
    path('transfer-creator/<int:group_id>/', views.transfer_creator, name='transfer-creator'),
    
    path('my_profile/<profile_id>', views.my_profile, name="my-profile"), 
    path('show_faculty/<faculty_id>', views.show_faculty, name='show-faculty'),
    path('update_deficiencies/<user_id>', views.update_deficiencies, name='update-deficiencies'), 
    
    path('delete_project_group/<group_id>', views.delete_project_group, name='delete-project-group'),

    path('reject-panel-invitation/<int:project_id>/', views.reject_panel_invitation, name='reject-panel-invitation'),

    path('submit_project_idea', views.submit_project_idea, name='submit-project-idea'), 
    path('all_project_ideas', views.all_project_ideas, name='all-project-ideas'), 
    path('show_project_idea/<project_idea_id>', views.show_project_idea, name='show-project-idea'), 
    path('delete_project_idea/<project_id>', views.delete_project_idea, name='delete-project-idea'),
    path('update_project_idea/<project_id>', views.update_project_idea, name='update-project-idea'),
  
    # path('create_custom_phase/<project_id>', views.create_custom_phase, name='create-custom-phase'),  
    # path('create_custom_phases', views.create_custom_phases, name='create-custom-phases'),  
 
    path('notifications/', views.notifications_view, name='notifications'), 
    path('notifications_api/', views.notifications_api, name='notifications_api'),    
    path('mark_read_unread/<int:notification_id>/', views.mark_read_unread, name='mark_read_unread'),
    path('delete_notification/<int:notification_id>/', views.delete_notification, name='delete_notification'),
     path('delete_all_notifications/', views.delete_all_notifications, name='delete_all_notifications'),
     
    path('mark_all_read/', views.mark_all_read, name='mark_all_read'),
 
    path('dashboard', views.coordinator_dashboard, name='coordinator-dashboard'), 
    path('save_project_group_settings/', views.save_project_group_settings, name='save_project_group_settings'),
    path('project-group-settings/', views.get_project_group_settings, name='project_group_settings'),

    path('delete-account/<user_id>', views.delete_account, name='delete-account'),
]   


