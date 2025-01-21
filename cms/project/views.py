from django.shortcuts import render, redirect
from .models import Project
from django.http import HttpResponseRedirect
from django.contrib import messages 
from django.conf import settings 
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import ProjectForm, CapstoneSubmissionForm, AddCommentsForm, ProjectGroupForm, ProjectGroupInviteForm
from .forms import  VerdictForm, CoordinatorForm, SelectPanelistForm, CoordinatorSelectPanelistForm
from .models import AppUserManager, Defense_Application, ProjectGroupSettings
from .models import Student, Faculty, Coordinator, ApprovedProjectGroup,  Project_Group
from .models import StudentProfile, FacultyProfile, CoordinatorProfile, Coordinator
from .models import Project_Idea
from .forms import ProjectIdeaForm, UpdateDeficienciesForm, UpdateDeficienciesFacultyForm
from defense_schedule.models import Defense_schedule 
# from .forms import CustomProjectPhaseForm

# from .models import Event
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse 
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from .models import Approved_Adviser, ApprovedProject
from django.db import IntegrityError
from .models import ProjectPhase
import logging
from django.db.models import Subquery, OuterRef, Max, Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Notification
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

logger = logging.getLogger(__name__)
# from .forms import PhaseForm
# from .models import CustomPhase
# from .forms import CustomPhaseForm

# Import user model 
from django.contrib.auth import get_user_model 
User = get_user_model()

@csrf_exempt

def get_project_group_settings(request):
    settings = ProjectGroupSettings.objects.first()
    max_proponents = settings.max_proponents if settings else 3
    allow_defense_applications = settings.allow_defense_applications if settings else True
    return JsonResponse({
        'maxProponents': max_proponents,
        'allowDefenseApplications': allow_defense_applications,
    })

def save_project_group_settings(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            max_proponents = int(data.get('numProponents', 3))  # Default to 3 if not provided
            allow_defense_applications = data.get('allowDefenseApplications', True)  # Default to True if not provided

            # Fetch or create the settings record
            settings, created = ProjectGroupSettings.objects.get_or_create(id=1)
            settings.max_proponents = max_proponents
            settings.allow_defense_applications = allow_defense_applications
            settings.save()

            # Return success response
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

# def add_custom_phase(request, project_id):
#     project = Project.objects.get(id=project_id)

#     # Ensure the logged-in user has permission to modify the project
#     if project.proponents.filter(id=request.user.id).exists():  # Check if the user is part of the project
#         if request.method == 'POST':
#             form = CustomPhaseForm(request.POST)
#             if form.is_valid():
#                 custom_phase = form.save(commit=False)
#                 custom_phase.project = project  # Associate phase with project
#                 custom_phase.save()
#                 messages.success(request, "Custom phase added successfully!")
#                 return redirect('project-detail', project_id=project.id)
#         else:
#             form = CustomPhaseForm()

#         return render(request, 'project/add_custom_phase.html', {'form': form, 'project': project})
#     else:
#         messages.error(request, "You don't have permission to add phases to this project.")
#         return redirect('project-list')  # Redirect to a different page if the user doesn't have permission

def notifications_api(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        # print(notifications)
        data = {
            "notifications": [
                {
                    "id": n.id, 
                    "type": n.get_notification_type_display(),
                    "message": n.message,
                    "created_at": n.created_at.strftime("%b %d, %Y %I:%M %p"),
                    "redirect_url": n.redirect_url,
                    "is_read": n.is_read,
                    "verdict": n.verdict,
                }
                for n in notifications
            ],
            "unread_count": notifications.filter(is_read=False).count(),
        }
        return JsonResponse(data)
    return JsonResponse({"error": "Not authenticated"}, status=401)

# def create_phases(request): 

#     project = Project.objects.get(id=project_id)

#     if not request.user.is_authenticated: 
#         messages.error(request, "Please login to view this page")
#         return redirect('home')
    
#     if not request.user.is_current_coordinator: 
#         messages.error(request, "You are not authorized to view this page")
#         return redirect('home')
    
#     return render(request, 'project/create_phases.html', {})

# def create_custom_phases(request):
#     # project = Project.objects.get(id=project_id)
#     if not request.user.is_authenticated: 
#         messages.error(request, "Please login to view this page")
#         return redirect('home')
    
#     if not request.user.is_current_coordinator: 
#         messages.error(request, "You are not authorized to view this page")
#         return redirect('home')
    
#     # if  request.method == 'POST':
#     #     form = CustomProjectPhaseForm(request.POST)
#     #     if form.is_valid():
#     #         custom_phase = form.save(commit=False)
#     #         # custom_phase.project = project
#     #         custom_phase.save()
#     #         form.save_m2m()  # Save the ManyToMany relation
#     #         messages.success(request, 'Custom phases have been saved successfully!')
#     #         return redirect('project_detail', project_id=project.id)
#     # else:
#     #     form = CustomProjectPhaseForm(initial={'project': project})

#     return render(request, 'project/create_custom_phases.html', {})

def coordinator_dashboard(request): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please login to view this page")
        return redirect('login')    

    if not request.user.is_current_coordinator:
        messages.error(request, "You're not authorized to view this page")
        return redirect('home')    


    adviser_count = Faculty.objects.filter(role='FACULTY').filter(adviser_eligible=True).count
    student_count = Student.objects.filter(role='STUDENT').filter(eligible=True ).count 
    project_group_count = Project_Group.objects.count 
    panelist_count = Faculty.objects.filter(role='FACULTY').filter(panel_eligible=True).count
    faculty_count = Faculty.objects.filter(role='FACULTY').count

    student_uneligible_count = Student.objects.filter(role='STUDENT').filter(eligible=False ).count
    adviser_uneligible_count = Faculty.objects.filter(role='FACULTY').filter(adviser_eligible=False).count
    panel_uneligible_count = Faculty.objects.filter(role='FACULTY').filter(panel_eligible=False).count
    
    project_group_count = Project_Group.objects.count
    unapproved_project_group_count = Project_Group.objects.filter(approved=False).count

    latest_projects = Project.objects.all().order_by('-created_at')[:15]
    project_count = Project.objects.filter(status='approved').count
    recent_users = User.objects.all().order_by('-created_at')[:10]

# Subquery to fetch the latest submission date per project
    latest_application_date_subquery = Defense_Application.objects.filter(
        project=OuterRef('project')
    ).order_by('-submission_date').values('submission_date')[:1]

    # Filter for the latest defense application per project with date comparison
    defense_applications = Defense_Application.objects.annotate(
        latest_application_date=Subquery(latest_application_date_subquery)
    ).filter(submission_date=F('latest_application_date'))

    # Check for 'pending' verdict in the latest phase
    latest_phase_subquery = ProjectPhase.objects.filter(
        project=OuterRef('project')
    ).order_by('-date').values('verdict')[:1]

    defense_applications = defense_applications.annotate(
        latest_verdict=Subquery(latest_phase_subquery)
    ).filter(latest_verdict='pending')

    defense_applications_count = defense_applications.count 

    # Prepare forms and data for each application
    verdict_forms = {}
    application_data = []

    for application in defense_applications:
        latest_phase = application.project.phases.order_by('-date').first()
        verdict_form = VerdictForm(instance=latest_phase)
        verdict_forms[application.id] = verdict_form

        application_data.append({
            'application': application,
            'latest_phase': latest_phase.phase_type,
            'latest_verdict': latest_phase.get_verdict_display(),
            'form': verdict_form,
        })

    defense_schedule_count = Defense_schedule.objects.all().count


    return render(request, 'project/coordinator_dashboard.html', {
        "faculty_count": faculty_count,
        "adviser_count": adviser_count, 
        "student_count": student_count,
        "project_group_count": project_group_count,
        "student_uneligible_count": student_uneligible_count, 
        "adviser_uneligible_count": adviser_uneligible_count, 
        "panelist_count": panelist_count,
        "panel_uneligible_count": panel_uneligible_count,
        "project_group_count": project_group_count, 
        "unapproved_project_group_count": unapproved_project_group_count,
        "project_count":  project_count,
        "defense_applications_count": defense_applications_count, 
        "defense_schedule_count": defense_schedule_count, 
        "latest_projects": latest_projects,
        "recent_users": recent_users,
    })


def show_proposal(request, project_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        project = Project.objects.get(pk=project_id)
        project_owner = User.objects.get(pk=project.owner)
        
        # pass it to the page using render
        return render(request, 'project/show_proposal.html', 
        {'project': project, 
        'project_owner': project_owner})
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')


def delete_user(request, user_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "You're not authorized to perform this Action")
        return redirect('home')
    
    if request.user.role != 'COORDINATOR': 
        messages.error(request, "You're not authorized to perform this Action")
        return redirect('home')
    
    try:
        user_to_delete = User.objects.get(pk=user_id)
        role = user_to_delete.role 

        if request.user == user_to_delete:  # Prevent users from deleting themselves
            messages.error(request, "You cannot delete your own account.")
            return redirect('home')
        
        user_to_delete.delete()

        # Redirect based on the role of the user
        if role == 'STUDENT':
            messages.success(request, "Student account deleted successfully!")
            return redirect('coordinator-approval-student')  # Redirect to the student list
        elif role == 'FACULTY':
            messages.success(request, "Faculty account deleted successfully!")
            return redirect('coordinator-approval-faculty')  # Redirect to the faculty list
        elif role == 'COORDINATOR': 
            messages.success(request, "Coordinator account deleted successfully!")
            return redirect('coordinator-approval-faculty') 
        else: 
            messages.success(request, "User account deleted successfully!")
            return redirect('coordinator-approval-faculty')
        
    except User.DoesNotExist:
        messages.error(request, "User does not exist.")
        return redirect('user-list')  # Redirect to a user list or appropriate page


def my_project(request): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
    if request.user.role != 'STUDENT': 
        messages.error(request, "Only Students can view this page")
        return redirect('home')
   
    user_group = get_user_project_group(request)
    if user_group is None:
            messages.success(request, "You are not a member of any Project Group. Please Register a Project Group First.")
            return redirect('home')
    
    project = Project.objects.filter(proponents=user_group, status='approved').first()

    return render(request, 'project/my_project.html', {'project': project })

def all_project_ideas(request): 
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view your notifications.")
        return redirect('login')
    
    # Create a Paginator object with the project_ideas list and specify the number of items per page
    p = Paginator(Project_Idea.objects.order_by('title'), 10) 
    page = request.GET.get('page')
    project_ideas = p.get_page(page)
    nums = "a" * project_ideas.paginator.num_pages

    # Calculate the start index for the current page
    start_index = (project_ideas.number - 1) * project_ideas.paginator.per_page


    return render(request, 'project/all_project_ideas.html', {
        'project_ideas': project_ideas, 
        'nums': nums, 
        'start_index': start_index  # Add start_index to context
    })


def submit_project_idea(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page" )
        return redirect('home')
    
    if request.method == 'POST':
        form = ProjectIdeaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Project Idea succesfully submitted")
            return redirect('all-project-ideas')  # Redirect to the same page after submission
    else:
        form = ProjectIdeaForm(initial={'faculty': request.user, }, user=request.user)

    ideas = Project_Idea.objects.all()  # Retrieve all submitted ideas
    return render(request, 'project/submit_project_idea.html', {
        'form': form, 'ideas': ideas})

def reject_panel_invitation(request, project_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view your notifications.")
        return redirect('login')
    
    project = get_object_or_404(Project, id=project_id)

    # Check if the user is a panelist for the project
    if request.user in project.panel.all():
        project.panel.remove(request.user.id)  # Remove the user from the panelists
        messages.success(request, f"You have successfully declined to serve as a panelist for the Project '{project.title}'.")
        
        # notify other users about the rejection
        for proponent in project.proponents.proponents.all():
            Notification.objects.create(
                recipient=proponent,
                notification_type='PANELIST_DECLINE',
                group=project.proponents,
                sender=request.user,
                message=f"{request.user.get_full_name()} has declined to serve as a Panelist for the project '{project.title}'.",
                redirect_url = reverse('my-project') 
            )
        # Notify the project adviser about the rejection
        if project.adviser:  # Check if there is an adviser assigned
            Notification.objects.create(
                recipient=project.adviser,
                notification_type='PANELIST_DECLINE',
                group=project.proponents,
                sender=request.user,
                message=f"{request.user.get_full_name()} has declined to serve as a Panelist for the project '{project.title}'. Please Select Another Panelist",
                redirect_url = reverse('adviser-projects') 
            )
    else:
        messages.error(request, "You are not a panelist for this project.")

    return redirect('panel-projects')  # Redirect to the appropriate page

def notifications_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view your notifications.")
        return redirect('login')

    # Fetch all notifications for the logged-in user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    return render(request, 'project/notifications.html', {
        'notifications': notifications,
    })

from django.views.decorators.http import require_POST

# @require_POST
# @login_required 
# def mark_notification_read(request, notification_id):
#     try:
#         notification = Notification.objects.get(id=notification_id, recipient=request.user)
#         notification.is_read = True
#         notification.save()
#         return JsonResponse({'success': True})
#     except Notification.DoesNotExist:
#         return JsonResponse({'error': 'Notification not found'}, status=404)
    
# Mark notification as read/unread
def mark_read_unread(request, notification_id):
    if request.user.is_authenticated:
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = not notification.is_read  # Toggle the read status
            notification.save()
            
            return JsonResponse({'status': 'success', 'is_read': notification.is_read})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
    return JsonResponse({'error': 'Not authenticated'}, status=401)

@login_required
def mark_all_read(request):
    if request.method == 'POST':
        # Mark all unread notifications for the current user as read
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        notifications.update(is_read=True)

        # Return success response
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


from django.views.decorators.http import require_http_methods
@require_http_methods(["DELETE"])
def delete_notification(request, notification_id):
    if request.user.is_authenticated:
        try:
            # Get the notification for the logged-in user
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.delete()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            # Notification not found
            return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
        except Exception as e:
            # Log unexpected errors
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'error': 'Not authenticated'}, status=401)

def delete_all_notifications(request):
    if request.method == 'DELETE':
        # Optionally, check if the user is authenticated or has permission
        notifications = Notification.objects.filter(recipient=request.user)  # Get all notifications
        notifications.delete()  # Delete all notifications
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# def delete_notification_dropdown(request, notification_id):
#     if request.user.is_authenticated:
#         try:
#             notification = Notification.objects.get(id=notification_id, recipient=request.user)
#             notification.delete()
#             return JsonResponse({'status': 'success'})
#         except Notification.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
#     return JsonResponse({'error': 'Not authenticated'}, status=401)

def select_coordinator(request):
    if not request.user.is_authenticated: 
        messages.error(request, "You are not authorized to view this page ")
        return redirect('home')
    
    # Allow access if the user is a superuser or the current coordinator
    if not request.user.is_superuser and not User.objects.filter(id=request.user.id, is_current_coordinator=True, role='COORDINATOR').exists():
        messages.error(request, "You are not authorized to view this page ")
        return redirect('home')  # Redirect if not admin or current coordinator

    # Check if there is a current coordinator
    try:
        current_coordinator = Coordinator.objects.filter(is_current_coordinator=True).first()
    except Coordinator.DoesNotExist:
        current_coordinator = None  # No current coordinator

    submitted = False 

    if request.method == 'POST':
        form = CoordinatorForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']

            # Ensure user is a Faculty instance or retrieve the Faculty instance
            try:
                faculty = Faculty.objects.get(id=user.id)
            except Faculty.DoesNotExist:
                messages.error(request, "Selected user is not a faculty member.")
                return redirect('select_coordinator')
            
            # Change the role of the selected Faculty to Coordinator
            faculty = Faculty.objects.get(id=user.id)
            faculty.role = 'COORDINATOR'
            faculty.is_current_coordinator = True
            faculty.save()
       
             # Set the current logged-in user's is_current_coordinator to False
            request.user.is_current_coordinator = False
            request.user.save()
            
            # Create a notification for the new coordinator
            try:
                Notification.objects.create(
                    recipient=faculty,
                    notification_type='ROLE_CHANGE',
                    group=None,  # Assuming no group is associated with this notification
                    sender=request.user,
                    message=f"You have been appointed as the new Coordinator.",
                    redirect_url = reverse('coordinator-projects') 
                )
            except Exception as e:
                logger.error(f"Failed to create notification for new coordinator: {str(e)}")


            messages.success(request, f"{user.get_full_name()} is now a Coordinator.")
            return HttpResponseRedirect('/select_coordinator?submitted=True')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        if current_coordinator: 
            form = CoordinatorForm(initial={'user': current_coordinator})
        else:
            form = CoordinatorForm()

        if 'submitted' in request.GET:
            submitted = True
            


    return render(request, 'project/select_coordinator.html', {
        'form': form,
        'current_coordinator': current_coordinator, 
        'submitted': submitted,
        })


def transfer_creator(request, group_id):
    group = get_object_or_404(Project_Group, id=group_id)

    if request.user != group.creator:
        messages.error(request, "Only the group creator can transfer the creator role.")
        return redirect('my-project-group-waitlist')

    if request.method == "POST":
        new_creator_id = request.POST.get('new_creator')
        new_creator = get_object_or_404(User, id=new_creator_id)

        if new_creator in group.proponents.all():
            group.creator = new_creator
            group.save()
            messages.success(request, f"Creator role has been transferred to {new_creator.get_full_name()}.")
        
            # Notify all proponents about the change
            for member in group.proponents.all():
                try:
                    Notification.objects.create(
                        recipient=member,
                        notification_type='ROLE_TRANSFER',
                        group=group,
                        sender=request.user,
                        message=f"The Leader Role has been transferred to {new_creator.get_full_name()}.",
                        redirect_url = reverse('my-project-group-waitlist') 
                    )
                except Exception as e:
                    logger.error(f"Failed to create notification for {member}: {str(e)}")
        
        
        else:
            messages.error(request, "Selected user is not an approved member of the group.")

        return redirect('my-project-group-waitlist')

    return render(request, 'project/transfer_creator.html', {
        'group': group,
        'approved_members': group.proponents.exclude(id=request.user.id)
    })

def accept_join_request(request, group_id, user_id): # Accept Join Request from a Student
    group = get_object_or_404(Project_Group, id=group_id)
    user = get_object_or_404(User, id=user_id)

    if request.user != group.creator:
        messages.error(request, "Only the group creator can accept join requests.")
        return redirect('my-project-group-waitlist')

    # Check if the total number of proponents and pending proponents is <= 2
    total_members = group.proponents.count() + group.pending_proponents.count() + group.declined_proponents.count()
    if total_members >= 3:
        messages.error(request, "The group already has the maximum number of members.")
        return redirect('my-project-group-waitlist')

    if user in group.requests.all():
        group.join_requests.remove(user.id)  # Ensure user object is used, not user.id
        group.pending_proponents.add(user.id)  # Ensure user object is used, not user.id

        messages.success(request, f"{user.get_full_name()} has been added to the group.")

        # Notify the user that they have been added to the group
        try:
            Notification.objects.create(
                recipient=user,
                notification_type='ADDED_TO_GROUP',
                group=group,
                sender=request.user,
                message=f"You have been added to {group.creator.get_full_name()}'s group.",
                redirect_url = reverse('my-project-group-waitlist')
            )

        except Exception as e:
            logger.error(f"Failed to create notification for {user}: {str(e)}")

        # Notify all proponents about the change
        for member in group.proponents.all():
            try:
                Notification.objects.create(
                    recipient=member,
                    notification_type='NEW_MEMBER',
                    group=group,
                    sender=request.user,
                    message=f"A new member has been added to the group, {user.get_full_name()}.",
                    redirect_url = reverse('my-project-group-waitlist')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {member}: {str(e)}")

    else:
        messages.error(request, "This user has not requested to join the group.")

    group.requests.remove(user.id)  # Ensure user object is used, not user.id
    return redirect('my-project-group-waitlist')

def decline_join_request(request, group_id, user_id):
    group = get_object_or_404(Project_Group, id=group_id)
    user = get_object_or_404(User, id=user_id)

    if request.user != group.creator:
        messages.error(request, "Only the group creator can decline join requests.")
        return redirect('my-project-group-waitlist')

    if user in group.requests.all():
        group.join_requests.remove(user.id)
        group.declined_requests.add(user.id)
        messages.success(request, f"{user.get_full_name()}'s join request has been declined.")
    
        # Notify the user that they have been declined to join the group
        try:
            Notification.objects.create(
                recipient=user,
                notification_type='DECLINED_JOIN_REQUEST',
                group=None,
                sender=request.user,
                message=f"You have declined to join {group.creator.get_full_name()}'s group.",
                redirect_url = reverse('my-project-group-waitlist')
            )   
        except Exception as e:
            logger.error(f"Failed to create notification for {user}: {str(e)}")
    
        # Notify all proponents about the change
        for member in group.proponents.all():
            try:
                Notification.objects.create(
                    recipient=member,
                    notification_type='DECLINED_JOIN_REQUEST',
                    group=group,
                    sender=request.user,
                    message=f"{user.get_full_name()} has declined to join the group.",
                    redirect_url = reverse('my-project-group-waitlist')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {member}: {str(e)}")
    
    else:
        messages.error(request, "This user has not requested to join the group.")

    return redirect('my-project-group-waitlist')

def join_group_list(request):
    if request.user.is_authenticated and request.user.eligible == False: 
        messages.error(request, "Only Eligible Students are able to request to join a Project Group. Please Contact Coordinator to for assistance with Eligibility Concerns")
        return redirect('home')
    
    # Get max_proponents value
    max_proponents = ProjectGroupSettings.get_max_proponents()


    # Get all unapproved groups that aren't full
    available_groups = Project_Group.objects.filter(approved=False)

    # Create enhanced data structure with both proponents and pending proponents
    groups_with_all_members = [
        {
            'group': group,
            'current_proponents': group.proponents.all(),      # Current members
            'pending_proponents': group.pending_proponents.all(), # Invited members
            'declined_proponents': group.declined_proponents.all(), # Declined members
            'join_requests': group.join_requests.all(), # Join requests
            'declined_requests': group.declined_requests.all(), # Declined requests.
            'requests': group.requests.all(), # Requests sent to this group
            'max_proponents': max_proponents,  # Pass max_proponents value
        
        } for group in available_groups
    ]

    # Check if user already belongs to a group
    user_has_group = Project_Group.objects.filter(
        Q(proponents=request.user) |
        Q(pending_proponents=request.user) | 
        Q(approved_by_students=request.user)
    ).exists()

    # Check if user has a pending join request  
    has_pending_request = Project_Group.objects.filter(
        approved=False,
        join_requests=request.user
    ).exists()
    
    context = {
        'groups_with_all_members': groups_with_all_members,
        'user_has_group': user_has_group,
        'has_pending_request': has_pending_request,
    }
    return render(request, 'project/join_group.html', context)

def request_join_group(request, group_id):
    
    if request.user.is_authenticated and request.user.eligible == False: 
        messages.error(request, "Only Eligible Students are able to request to join a Project Group. Please Contact Coordinator to for assistance with Eligibility Concerns")
        return redirect('home')

    if request.method == 'POST':
        group = get_object_or_404(Project_Group, id=group_id, approved=False)
        
        # Check if user already belongs to a group
        if Project_Group.objects.filter(
            Q(proponents=request.user) |
            Q(pending_proponents=request.user)

        ).exists():
            messages.error(request, 'You already belong to a group.')
            return redirect('join-group-list')
        
        # Check if group is full
        if group.proponents.count() >= 3:
            messages.error(request, 'This group is already full.')
            return redirect('join-group-list')
        
 # Check if the user is in declined_requests and remove them
        if request.user in group.declined_requests.all():
            group.declined_requests.remove(request.user.id) 
        # Add user to pending proponents
        group.join_requests.add(request.user.id)
        group.requests.add(request.user.id)

         # Notify all current proponents about the join request
        for proponent in group.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='JOIN_REQUEST',
                    group=group,
                    sender=request.user,
                    message=f"{request.user.get_full_name()} has requested to join your Project Group.",
                    redirect_url = reverse('my-project-group-waitlist')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")

        messages.success(request, 'Join request sent successfully.')
        
        return redirect('join-group-list')
    
    return redirect('join-group-list')

def cancel_join_request(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Project_Group, id=group_id, approved=False)
        
        # Check if user has a pending join request
        if request.user not in group.join_requests.all():
            messages.error(request, 'No pending join request found.')
            return redirect('join-group-list')
        
        # Remove user from join requests
        group.join_requests.remove(request.user.id)
        group.requests.remove(request.user.id)

        for member in group.proponents.all():
            # Notify the project proponents that their a join request has been cancelled        
            try:
                Notification.objects.create(
                    recipient=member,
                    notification_type='JOIN_REQUEST_CANCELLED',
                    group=group,
                    sender=request.user,
                    message=f"{request.user.get_full_name()}'s join request has been cancelled.",
                    redirect_url = reverse('my-project-group-waitlist')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {request.user}: {str(e)}")

        messages.success(request, 'Join request cancelled successfully.')
        
        return redirect('join-group-list')
    
    return redirect('join-group-list')

def submit_verdict(request, application_id):
    if request.method == 'POST' and request.user.is_authenticated:
        # Fetch the defense application based on the ID
        application = get_object_or_404(Defense_Application, id=application_id)

        # Fetch the latest project phase
        latest_phase = application.project.phases.order_by('-date').first()

        # If no phase exists, create the first phase as "Proposal Defense"
        if not latest_phase:
            latest_phase = ProjectPhase.objects.create(
                project=application.project,
                phase_type='proposal',  # First phase is 'Proposal Defense'
                verdict='pending',  # Initial verdict is 'pending'
                date=timezone.now()
            )

        form = VerdictForm(request.POST, instance=latest_phase)

        if form.is_valid():
            # Check if the selected verdict is 'pending'
            if form.cleaned_data['verdict'] == 'pending':
                messages.error(request, "Verdict cannot be pending.")
                return redirect('list-defense-applications')  # Redirect to avoid showing success message
            
            # Save the verdict for the latest phase
            phase = form.save(commit=False)

            # Ensure you are setting the phase type here if it's blank
            if not phase.phase_type:
                phase.phase_type = latest_phase.phase_type  # or set to a default value if needed
            phase.save()
            
             # Create notifications for all proponents
            for proponent in application.project.proponents.proponents.all():
                verdict = phase.get_verdict_display()  # Get the verdict description
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='VERDICT',
                    group=application.project.proponents,
                    sender=request.user,
                    message=f"The verdict for the {phase.get_phase_type_display()} of the project '{application.project.title}' is",
                    verdict=verdict, # Store the verdict for later use in template
                    redirect_url = reverse('my-defense-application')
                )
            if application.project.adviser:  # Check if there is an adviser assigned
                Notification.objects.create(
                    recipient=application.project.adviser,
                    notification_type='VERDICT',
                    group=application.project.proponents,
                    sender=request.user,
                    message=f"The verdict for the {phase.get_phase_type_display()} of the project '{application.project.title}' is.",
                    redirect_url=reverse('generate-report')  
                )

            messages.success(request, "Verdict submitted successfully!")
            return redirect('list-defense-applications')
        else:
            messages.error(request, "There was an error with the form submission.")
            return render(request, 'project/home')

    else:
        messages.error(request, "Invalid request method or you are not logged in.")
        return redirect('home')

def submit_defense_application(request):

    settings = ProjectGroupSettings.objects.first()
    if settings and not settings.allow_defense_applications:
        messages.info(request, "Currently not accepting Defense Applications.")
        return redirect('my-defense-application')
        
    
    if not request.user.is_authenticated: 
        messages.error(request, "You are not authorized to view this page. Please login")
        return redirect('home')
    
    user_group = get_user_project_group(request)
    
    if user_group is None:
        messages.error(request, "You are not a member of any Project Group. Please Register a Project Group First.")
        return redirect('my-defense-application')
        
    project = Project.objects.filter(proponents=user_group, status='approved', is_archived=False).first()

    if project is None:
        messages.error(request, "No project found for your group. Please submit a project first and wait for approval from an Adviser.")
        return redirect('my-defense-application')

    elif project.status == 'pending':
        messages.error(request, "Your project has not been approved yet. You cannot submit a Defense Application.")
        return redirect('my-defense-application')
    
    # Check for pending phases
    # pending_phases = project.phases.filter(verdict='pending').exclude(first_phase=True)
    # if pending_phases.exists():
    #     messages.error(request, "There is already a pending Defense Application for your project group. Please wait for a Verdict to be given.")
    #     return redirect('my-defense-application')
        
    
    # Check for any two pending project phase
    pending_phases_count = project.phases.filter(verdict='pending').count()
    if pending_phases_count >= 2:
        messages.success(request, "There is already a pending Defense Application for your project group. Please wait for a Verdict to be given.")
        return redirect('my-defense-application')

    # Fetch custom phases if they exist
    # custom_phases = project.custom_phases.all()
    # if custom_phases.exists():
    #     # Allow the user to select from the custom phases instead of fixed ones
    #     # You can render a dropdown of custom phases or the available phases for the defense
    #     next_phase_type = custom_phases.first().phase_type  # Get the first custom phase
    # else:
    
    # Fetch the last completed phase, if any
    last_completed_phase = project.phases.exclude(verdict='pending').order_by('-date').first()

    # Check if the last completed phase has a verdict of "Not Accepted"
    if last_completed_phase and last_completed_phase.verdict == 'not_accepted':
        messages.error(request, "The Verdict of the recent Defense was Not-Accepted. Please Contact the Coordinator if you think this is a mistake.")
        return redirect('my-defense-application')

    next_phase_type = 'proposal'  # Default phase if no custom phases exist

    if last_completed_phase:
        if last_completed_phase.phase_type == 'final' and last_completed_phase.verdict in ['accepted', 'accepted_with_revisions']:
            messages.error(request, "You have already passed the Final Defense. No more defense applications are needed. Congratulations!")
            return redirect('my-defense-application')
        
        if last_completed_phase.verdict == 'redefense':
            next_phase_type = last_completed_phase.phase_type
        elif last_completed_phase.phase_type == 'proposal' and last_completed_phase.verdict in ['accepted', 'accepted_with_revisions']:
            next_phase_type = 'design'
        elif last_completed_phase.phase_type == 'design' and last_completed_phase.verdict in ['accepted', 'accepted_with_revisions']:
            next_phase_type = 'preliminary'
        elif last_completed_phase.phase_type == 'preliminary' and last_completed_phase.verdict in ['accepted', 'accepted_with_revisions']:
            next_phase_type = 'final'

    submitted = False

    if request.method == 'POST': 
        # Ensure no pending phase exists before proceeding
        pending_phases = project.phases.filter(verdict='pending').exclude(first_phase=True)
        if pending_phases.exists():
            messages.success(request, "There is already a pending Defense Application for your project group. Please wait for a verdict.")
            return redirect('my-defense-application')  # Redirect if a pending phase exists

        form = CapstoneSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.owner = request.user.id
            application.proponents = project.proponents
            application.project = project
            application.title = next_phase_type

            if project.adviser:
                application.adviser = project.adviser
            else:
                form.add_error('adviser', 'No adviser assigned to this group.')
                return render(request, 'project/add_project.html', {
                    'project': project,
                    'group': user_group, 
                    'form': form,
                    'submitted': submitted
                })
            
            application.save()
            # Set submitted to True after saving the application
            submitted = True

            panel_members = project.panel.all()

            if not panel_members:
                messages.error(request, "No panel members found for this project.")
                return render(request, 'project/submit_defense_application.html', {
                    'project': project,
                    'group': user_group,
                    'form': form,
                    'submitted': submitted
                })

            application.panel.set(panel_members.values_list('id', flat=True))
            form.save_m2m()

            # Send notifications to all proponents except the logged-in user
            for proponent in project.proponents.proponents.all().exclude(id=request.user.id):
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='SUBMITTED_DEFENSE_APPLICATION',
                    group=project.proponents,
                    sender=request.user,
                    message=f"A new defense application for the '{application.get_title_display()}' has been submitted for the project '{project.title}' by {request.user.get_full_name()}."
                    
                )
                # Send notification to the Coordinator
            try:
                coordinator = User.objects.get(is_current_coordinator=True)  # Adjust this query based on your model
                Notification.objects.create(
                    recipient=coordinator,
                    notification_type='SUBMITTED_DEFENSE_APPLICATION',
                    group=project.proponents,
                    sender=request.user,
                    message=f"A new defense application for the project '{project.title}' has been submitted by {request.user.get_full_name()}.",
                    redirect_url = reverse('list-defense-applications')
                )
            except User.DoesNotExist:
                logger.error("No current coordinator found to notify.")

            # Check if there is already a pending phase
            pending_phases = project.phases.filter(verdict='pending')   

                # Create the new phase only if there is no pending phase
                # Only create a new phase if no pending phases exist
            if not pending_phases.exists():
                # Create the new phase
                ProjectPhase.objects.create(
                    project=project,
                    phase_type=next_phase_type,
                    verdict='pending',
                    date=timezone.now(),
                    first_phase=True if not project.phases.exists() else False
                )
                return HttpResponseRedirect('/submit_defense_application?submitted=True')
            else:
                messages.success(request, "There is already a pending Defense Application for your project group. Please wait for a verdict.")
                return redirect('my-defense-application')   
    else:
        form = CapstoneSubmissionForm(initial={
            'adviser': project.adviser.id if project.adviser else None, 
            'project_group': user_group, 
            'project': project, 
            'panel': project.panel.all(),
            'title': next_phase_type,
        })
        if 'submitted' in request.GET: 
            submitted = True

    return render(request, 'project/submit_defense_application.html', {
        'last_phase': last_completed_phase, 
        'next_phase_type': next_phase_type, 
        'project': project, 
        'group': user_group,
        'form': form, 
        'submitted': submitted
    })

    
from django.db.models import Subquery, OuterRef, F
from django.utils import timezone
    
def list_defense_applications(request):
    if request.user.is_authenticated:
        # Subquery to fetch the latest submission date per project
        latest_application_date_subquery = Defense_Application.objects.filter(
            project=OuterRef('project')
        ).order_by('-submission_date').values('submission_date')[:1]

        # Filter for the latest defense application per project with date comparison
        defense_applications = Defense_Application.objects.annotate(
            latest_application_date=Subquery(latest_application_date_subquery)
        ).filter(submission_date=F('latest_application_date'))

        # Check for 'pending' verdict in the latest phase
        latest_phase_subquery = ProjectPhase.objects.filter(
            project=OuterRef('project')
        ).order_by('-date').values('verdict')[:1]

        defense_applications = defense_applications.annotate(
            latest_verdict=Subquery(latest_phase_subquery)
        ).filter(latest_verdict='pending')

        defense_applications_count = defense_applications.count 

        # Prepare forms and data for each application
        verdict_forms = {}
        application_data = []

        for application in defense_applications:
            latest_phase = application.project.phases.order_by('-date').first()
            verdict_form = VerdictForm(instance=latest_phase)
            verdict_forms[application.id] = verdict_form

            application_data.append({
                'application': application,
                'latest_phase': latest_phase.phase_type,
                'latest_verdict': latest_phase.get_verdict_display(),
                'form': verdict_form,
            })

        return render(request, 'project/defense_application_list.html', {
            "defense_applications": defense_applications,
            "verdict_forms": verdict_forms,
            "defense_applications_count": defense_applications_count,
        })
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('login')
    
def my_defense_application(request):
    if request.user.is_authenticated and request.user.role != 'STUDENT':
        messages.error(request, "You are not a Student. You cannot view this page.")
        return redirect('home')
    
    # Get the project group of the logged-in user
    project_group = get_user_project_group(request)
    
    if not project_group:
        messages.error(request, "You are not part of any project group.")
        return redirect('home')
    
    # Subquery to fetch the latest submission date per project
    latest_application_date_subquery = Defense_Application.objects.filter(
        project=OuterRef('project')
    ).order_by('-submission_date').values('submission_date')[:1]

    # Fetch only the latest defense application for the user's project group
    defense_applications = Defense_Application.objects.annotate(
        latest_application_date=Subquery(latest_application_date_subquery)
    ).filter(
        submission_date=F('latest_application_date'),
        project__proponents=project_group
    )

    # Prepare data for each application
    application_data = []
    for application in defense_applications:
        latest_phase = application.project.phases.order_by('-date').first()
        application_data.append({
            'application': application,
            'latest_phase': latest_phase,
        })

    # Define the list of verdicts
    verdicts = ['redefense', 'accepted', 'accepted_with_revisions']
    
    return render(request, 'project/my_defense_application.html', {
        'application_data': application_data,
         'verdicts': verdicts,  # Pass the verdicts list to the template
    })

def delete_project_group(request, group_id): 
    if not request.user.is_authenticated or not request.user.is_current_coordinator: 
        messages.error(request, "You Aren't Authorized to perform this action")
        return redirect('home')
    
    try:
        project_group = Project_Group.objects.get(pk=group_id)
        project_group.delete()
        messages.success(request, "Project Group Deleted Successfully!")
    except Project_Group.DoesNotExist:
        messages.error(request, "Project Group not found!")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('list-project-group')
    

def list_project_group(request): 
     # Fetch max proponents setting
    # max_proponents = ProjectGroupSettings.get_max_proponents()
    
    if request.user.is_authenticated: 
        # Get all project groups (filtered to those not approved)
        project_groups = Project_Group.objects.filter(approved=True)
        max_members_in_any_group = 0  # Track the max number of proponents in any group


        # Prepare project groups with proponents padded to at least 3
        project_groups_with_proponents = []


        # First pass: determine the maximum number of members in any group
        for group in project_groups:
            proponents = list(group.proponents.all())  # Get actual proponents list
            group_proponents_count = len(proponents)
            
            # Update max_members_in_any_group if this group has more proponents
            max_members_in_any_group = max(max_members_in_any_group, group_proponents_count)
            
        # Second pass: calculate extra cells for each group and prepare data
        for group in project_groups:
            proponents = list(group.proponents.all())  # Get the list of proponents
            group_proponents_count = len(proponents)

             # Calculate the number of extra cells needed for this group
            extra_cells = max_members_in_any_group - group_proponents_count

            project_groups_with_proponents.append({
                'group': group,
                'proponents': proponents,
                'proponents_count': group_proponents_count,  # Store count of proponents
                'extra_cells': extra_cells,  # Include empty cells for padding
        })

          # Set max_proponents to the maximum number found
        # max_members_in_any_group = max(max_proponents, max_members_in_any_group)


        # Paginate the project groups
        p = Paginator(project_groups_with_proponents, 8)  # Show 6 project groups per page
        page = request.GET.get('page')
        paginated_groups = p.get_page(page)
        nums = "a" * paginated_groups.paginator.num_pages

        # Calculate the start index for the current page
        start_index = (paginated_groups.number - 1) * paginated_groups.paginator.per_page


        return render(request, 'project/project_group_list.html', {
            'project_groups_with_proponents': paginated_groups,
            'nums': nums, 
            'start_index': start_index, 
            'max_members_in_any_group': max_members_in_any_group,
            'start_index': start_index,
        })
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
    
def my_project_group_waitlist(request):
    if request.user.is_authenticated:
        
        # Get all project groups where the current user is a pending proponent
        pending_groups = Project_Group.objects.filter(pending_proponents=request.user)

        # Get groups where user is creator
        groups_where_user_is_creator = Project_Group.objects.filter(creator=request.user)
        
        # Get groups where user has approved
        groups_where_user_approved = Project_Group.objects.filter(approved_by_students=request.user)
    
        # Get max_proponents value
        max_proponents = ProjectGroupSettings.get_max_proponents()

        # Consolidate groups and avoid duplicates
        all_groups = list(set(pending_groups) | set(groups_where_user_is_creator) | set(groups_where_user_approved))

        # Create enhanced data structure with both proponents and pending proponents
        groups_with_all_members = [
            {
                'group': group,
                'current_proponents': group.proponents.all(),      # Current members
                'pending_proponents': group.pending_proponents.all(), # Invited members
                'declined_proponents': group.declined_proponents.all(), # Declined members
                'declined_requests': group.declined_requests.all(), # Declined requests
                'join_requests': group.join_requests.all(), # Join requests
                'total_members': group.proponents.count() + group.pending_proponents.count() + group.declined_proponents.count(),  # Calculate total members
                'max_proponents': max_proponents,  # Pass max_proponents value
            } for group in all_groups
        ]

        return render(request, 'project/my_project_group_waitlist.html', {
            'groups_with_all_members': groups_with_all_members,
           
        })
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')

    
def update_deficiencies(request, user_id ): 
    # Authentication and permissions check
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
    if not request.user.is_current_coordinator:
        messages.error(request, "You are not authorized to perform this action")
        return redirect('home')
    
    try: 
        selected_user = User.objects.get(pk=user_id)
            
    except User.DoesNotExist: 
        messages.error(request, "User does not exist.")
        return redirect('home')  # Redirect to a user list or appropriate page

    # Determine form based on user role
    if selected_user.role == 'STUDENT':
        form = UpdateDeficienciesForm(request.POST or None, instance=selected_user)
    # Initialize the form
    elif selected_user.role == 'FACULTY':
        form = UpdateDeficienciesFacultyForm(request.POST or None, instance=selected_user)
    
    if request.method == 'POST':
            if form.is_valid():
                  # Manually set disabled fields' values from the instance
                form.cleaned_data['first_name'] = selected_user.first_name
                form.cleaned_data['last_name'] = selected_user.last_name
                form.cleaned_data['email'] = selected_user.email
                
                if selected_user.role == 'STUDENT':
                    form.cleaned_data['student_id'] = selected_user.student_id
                    form.cleaned_data['course'] = selected_user.course
                
                form.save()

                try: 
                     # Determine the redirect URL based on the user's role
                    if selected_user.role == 'STUDENT':
                        redirect_url = reverse('list-student')
                    else:
                        redirect_url = reverse('list-faculty')

                    Notification.objects.create(
                    recipient=selected_user,
                    notification_type='DEFICIENCIES',
                    sender=request.user,
                    message=f"Your Eligibility Deficiencies has been updated.",
                    redirect_url=redirect_url  

                    )
                except Exception as e: 
                    logger.error(f"Failed to create notification for {selected_user}: {str(e)}")

                messages.success(request, "User's deficiencies updated successfully!")

                if selected_user.role == 'STUDENT':
                    return redirect('coordinator-approval-student')
                else: 
                    return redirect('coordinator-approval-faculty')
            else:
                # Add error feedback for invalid forms
                messages.error(request, "Please correct the errors below.")

     # Compute deficiencies_list for template display
    deficiencies_list = [d.strip() for d in selected_user.deficiencies.split(',')] if selected_user.deficiencies else []

    return render(request, 'project/update_deficiencies.html', {
        'user': selected_user,
        'form': form, 
        'deficiencies_list': deficiencies_list,
    })
  
    
def get_user_ids_with_group(request): 
    # Get all approved project groups
    approved_groups = Project_Group.objects.filter(approved=True)

    # Create a set to store unique student IDs
    approved_student_ids = set()
    
        # Iterate through each approved project group
    for group in approved_groups:
        # Add the IDs of the proponents (students) to the set
        approved_student_ids.update(group.proponents.values_list('id', flat=True))

    
    return list(approved_student_ids)
def approve_group_membership(request, group_id):
    if not request.user.is_authenticated or request.user.role != 'STUDENT':
        messages.error(request, "Unauthorized access")
        return redirect('home')
        
    group = get_object_or_404(Project_Group, id=group_id)
    
    # Get the Student instance associated with the user
    try:
        student = Student.objects.get(id=request.user.id)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found")
        return redirect('home')
    
    # Check if student is already in an approved group
    existing_approved_group = Project_Group.objects.filter(
        proponents=student,
        approved=True
    ).first()
    
    if existing_approved_group:
        messages.error(request, "You are already in an approved group. You cannot join another group.")
        return redirect('my-project-group-waitlist')

    # Check if student is already in an approved group
    existing_approved_pending_group = Project_Group.objects.filter(
        approved_by_students=student,
        approved=False
    ).first()

    if existing_approved_pending_group:
        messages.error(request, "You have given an approval in another group. You cannot join this group.")
        return redirect('my-project-group-waitlist')

    if student not in group.pending_proponents.all():
        messages.error(request, "You are not invited to this group")
        return redirect('home')
    
    # Start a transaction to ensure all operations are atomic
    from django.db import transaction

    with transaction.atomic():
        # Accept the current group invitation
        group.approved_by_students.add(student)
        group.pending_proponents.remove(student)
        group.proponents.add(student)
        
        # Automatically decline all other pending invitations
        other_pending_groups = Project_Group.objects.filter(
            pending_proponents=student,
            approved=False
        ).exclude(id=group_id)

        for other_group in other_pending_groups:
            other_group.pending_proponents.remove(student)
            other_group.declined_proponents.add(student)
            # Optionally, create a notification for the decline
            try:
                Notification.objects.create(
                    recipient=other_group.creator,
                    notification_type='rejected',
                    group=other_group,
                    sender=request.user,
                    message=f"{request.user.get_full_name()} has declined the invitation to join your project group.",
                    redirect_url = reverse('my-project-group-waitlist')
                )
            except Exception as e:
                logger.error(f"Failed to create decline notification: {str(e)}")
        
        # Check if there are exactly 3 approved students
        approved_students_count = group.approved_by_students.count()
        
        if approved_students_count == 3:
            # Automatically approve the group
            group.approved = True
            group.save()
            
            # Clear any remaining pending invitations
            group.pending_proponents.clear()
            
            # Create notification for all group members
            for member in group.proponents.all():
                try:
                    Notification.objects.create(
                        recipient=member,
                        notification_type='GROUP_COMPLETE',
                        group=group,
                        sender=request.user,
                        message=f"Your Project Group, led by {group.creator.get_full_name()}, has been automatically approved with 3 members.",
                        redirect_url = reverse('my-project-group-waitlist')
                    )
                except Exception as e:
                    logger.error(f"Failed to create notification for {member}: {str(e)}")
            
            messages.success(request, "You have joined the group and it has been automatically approved with 3 members.")
        elif approved_students_count < 3:
             # Notify all proponents about the acceptance
            for proponent in group.proponents.all():
                try:
                    Notification.objects.create(
                        recipient=proponent,
                        notification_type='ACCEPTED',
                        group=group,
                        sender=request.user,
                        message=f"{request.user.get_full_name()} has accepted the invitation to join your project group. ({approved_students_count}/3 members)",
                        redirect_url=reverse('my-project-group-waitlist')
                    )
                except Exception as e:
                    logger.error(f"Failed to create notification for {proponent}: {str(e)}")
            
            messages.success(request, f"You have successfully joined the group. {3 - approved_students_count} more member(s) needed for automatic approval.")
        else:
            logger.warning(f"Group {group.id} has more than 3 approved members: {approved_students_count}")
            messages.warning(request, "Unexpected number of group members.")

    return redirect('my-project-group-waitlist')

def reject_group_membership(request, group_id):
    if not request.user.is_authenticated or request.user.role != 'STUDENT':
        messages.error(request, "Unauthorized access")
        return redirect('home')
        
    group = get_object_or_404(Project_Group, id=group_id)
    
    if request.user not in group.pending_proponents.all():
        messages.error(request, "You are not invited to this group")
        return redirect('home')
        
    # Move user from pending to declined instead of removing
    group.pending_proponents.remove(request.user.id)
    group.declined_proponents.add(request.user.id)
    
    # Notify all proponents about the decline
    for proponent in group.proponents.all():
        try:
            Notification.objects.create(
                recipient=proponent,
                notification_type='REJECTED',
                group=group,
                sender=request.user,
                message=f"{request.user.get_full_name()} has declined the invitation to join your project group.",
                redirect_url=reverse('my-project-group-waitlist')
            )
        except Exception as e:
            logger.error(f"Failed to create decline notification for {proponent}: {str(e)}")


    messages.success(request, "Group invitation declined.")
    return redirect('my-project-group-waitlist')

# Add new view for replacing declined member
def replace_member(request, group_id, member_id):
    group = get_object_or_404(Project_Group, id=group_id)
    member = get_object_or_404(Student, id=member_id)
    
    if request.user != group.creator:
        messages.error(request, "Only the group creator can replace members")
        return redirect('my-project-group-waitlist')
    
    if request.method == "POST":
        form = ProjectGroupInviteForm(request.POST, group=group)
        if form.is_valid():
            new_members = form.cleaned_data.get('proponents', [])
            if len(new_members) > 1:
                messages.error(request, "You can only select one replacement member")
                return redirect('my-project-group-waitlist')
                
            if new_members:
                group.declined_proponents.remove(member)
                group.pending_proponents.add(new_members[0])
                
                # Create notification for new invite
                try:
                    Notification.objects.create(
                        recipient=new_members[0],
                        notification_type='INVITATION',
                        group=group,
                        sender=request.user,
                        message=f"{request.user.get_full_name()} has invited you to join the project group."
                    )
                except Exception as e:
                    logger.error(f"Failed to create notification: {str(e)}")
                
                messages.success(request, "Replacement invitation sent successfully")
                return redirect('my-project-group-waitlist')
    else:
        form = ProjectGroupInviteForm(group=group)
    
    return render(request, 'project/replace_member.html', {
        'form': form,
        'group': group,
        'member': member
    })

def leave_group(request, group_id):
    group = get_object_or_404(Project_Group, id=group_id)
    
    if request.user == group.creator:
        # Get all approved members excluding the creator
        other_members = group.proponents.exclude(id=request.user.id)
        
        if other_members.exists():
            # Transfer creator role to another member
            new_creator = other_members.first()
            group.creator = new_creator
            messages.success(request, f"You have left the group. Creator role transferred to {new_creator.get_full_name()}")
        else:
            # Delete the group if no other members
            group.delete()
            messages.success(request, "Group has been deleted as you were the only member.")
            return redirect('my-project-group-waitlist')
    else:
        # Non-creator members can leave the group
        group.proponents.remove(request.user.id)
        group.approved_by_students.remove(request.user.id)
        messages.success(request, "You have left the group.")
    
    # Create notifications for remaining proponents
    for member in group.proponents.all():
        try:
            Notification.objects.create(
                recipient=member,
                notification_type='LEAVE_GROUP',
                group=group,
                sender=request.user,
                message=f"{request.user.get_full_name()} has left the project group.",
                redirect_url=reverse('my-project-group-waitlist')
            )
        except Exception as e:
            logger.error(f"Failed to create notification for {member}: {str(e)}")

    group.save()
    return redirect('my-project-group-waitlist')

def remove_member(request, group_id, member_id):
    group = get_object_or_404(Project_Group, id=group_id)
    member = get_object_or_404(Student, id=member_id)
    
    if request.user != group.creator:
        messages.error(request, "Only the group creator can remove members.")
        return redirect('my-project-group-waitlist')
    
    # Check both pending and declined proponents
    if member in group.declined_proponents.all():
        group.declined_proponents.remove(member)
        messages.success(request, f"{member.get_full_name()} has been removed from the list.")
    elif member in group.pending_proponents.all():
        group.pending_proponents.remove(member)
        messages.success(request, f"{member.get_full_name()} has been removed from the list.")
    else:
        messages.error(request, "This member is not in the pending or declined list.")
    
        return redirect('my-project-group-waitlist')

    # Notify all proponents about the removal
    for proponent in group.proponents.all():
        try:
            Notification.objects.create(
                recipient=proponent,
                notification_type='MEMBER_REMOVAL',
                group=group,
                sender=request.user,
                message=f"{member.get_full_name()} has been removed from the project group.", 
                redirect_url=reverse('my-project-group-waitlist')
            )
        except Exception as e:
            logger.error(f"Failed to create notification for {proponent}: {str(e)}")
    
    return redirect('my-project-group-waitlist')



def finalize_group(request, group_id):
    group = get_object_or_404(Project_Group, id=group_id)
    
    if request.user != group.creator:
        messages.error(request, "Only the group creator can finalize the group.")
        return redirect('my-project-group-waitlist')
    
    # if group.approved_by_students.count() < 2:
    #     messages.error(request, "You need at least 2 members to finalize the group.")
    #     return redirect('my-project-group-waitlist')
    
    # Clear any pending invitations
    group.pending_proponents.clear()
    
    # Mark the group as approved
    group.approved = True
    group.save()
    
    # Notify all current proponents about the group finalization
    for member in group.proponents.all():
        try:
            Notification.objects.create(
                recipient=member,
                notification_type='GROUP_FINALIZED',
                group=group,
                sender=request.user,
                message=f"The project group, led by {group.creator.get_full_name()}, has been finalized.",
                redirect_url=reverse('my-project-group-waitlist')
            )
        except Exception as e:
            logger.error(f"Failed to create notification for {member}: {str(e)}")

    messages.success(request, "Group has been finalized successfully!")
    return redirect('my-project-group-waitlist')

def invite_more_members(request, group_id):
    # Retrieve the max_proponents value
    max_proponents = ProjectGroupSettings.get_max_proponents()

    group = get_object_or_404(Project_Group, id=group_id)
    
    if request.user != group.creator:
        messages.error(request, "Only the group creator can invite more members.")
        return redirect('my-project-group-waitlist')
    
    # Calculate the total number of current, pending, and declined members
    total_members = group.proponents.count() + group.pending_proponents.count() + group.declined_proponents.count()
    
    if total_members >= max_proponents:
        messages.error(request, "Cannot invite more members. The group already has the maximum number of members.")
        return redirect('my-project-group-waitlist')
    
    if request.method == "POST":
        form = ProjectGroupInviteForm(request.POST, group=group)
        if form.is_valid():
            new_members = form.cleaned_data.get('proponents', [])
            
            # Get existing members and pending members
            existing_members = set(group.proponents.all())
            pending_members = set(group.pending_proponents.all())
            
            # Track successful invites
            successful_invites = []
            failed_invites = []
            
            for member in new_members:
                # Only add if they're not already a member or pending
                if member not in existing_members and member not in pending_members:
                    try:
                        # Add to pending_proponents
                        group.pending_proponents.add(member)
                        
                        # Create notification with separate try-except block
                        try:
                            notification = Notification.objects.create(
                                recipient=member,
                                notification_type='INVITATION',
                                group=group,
                                sender=request.user,
                                message=f"{request.user.get_full_name()} has invited you to join the project group led by'{group.creator}'",
                                redirect_url = reverse('my-project-group-waitlist')
                            )
                            logger.info(f"Successfully created notification {notification.id} for {member.get_full_name()}")
                        except Exception as notif_error:
                            logger.error(f"Failed to create notification for {member.get_full_name()}: {str(notif_error)}")
                            # Continue with the invitation even if notification fails
                        
                        successful_invites.append(member.get_full_name())
                        logger.info(f"Successfully added {member.get_full_name()} to pending proponents of group {group.id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to add {member.get_full_name()} to group {group.id}: {str(e)}")
                        failed_invites.append(f"{member.get_full_name()} (error: {str(e)})")
                else:
                    failed_invites.append(f"{member.get_full_name()} (already invited or member)")
            
            # Show summary messages
            if successful_invites:
                messages.success(request, f"Successfully invited: {', '.join(successful_invites)}")
            if failed_invites:
                messages.warning(request, f"Some invitations could not be processed: {', '.join(failed_invites)}")
                
            return redirect('my-project-group-waitlist')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ProjectGroupInviteForm(group=group)
    
    return render(request, 'project/invite_more_members.html', {
        'form': form,
        'group': group,
        'current_members': group.proponents.all(),
        'pending_members': group.pending_proponents.all(),
        'max_proponents': max_proponents,
    })

from django.contrib.auth.decorators import login_required

# @login_required
# def get_notifications(request):
#     notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
#     unread_count = notifications.filter(is_read=False).count()
#      # Debugging logs
#     logger.debug(f"Fetching notifications for user: {request.user}")
#     logger.debug(f"Notifications count: {notifications.count()}")
#     logger.debug(f"Unread notifications count: {unread_count}")
    
#     notifications_data = [{
#         'id': notif.id,
#         'message': notif.message,
#         'is_read': notif.is_read,
#         'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
#     } for notif in notifications]
    
#     return JsonResponse({
#         'notifications': notifications_data,
#         'unread_count': unread_count
#     })

def add_project_group(request): 
    if not request.user.is_authenticated or request.user.role != 'STUDENT':
        messages.error(request, "Please login as a student to perform this action")
        return redirect('login')

    if request.user.is_authenticated and request.user.eligible == False: 
        messages.error(request, "Only Eligible Students are able to register a Project Group.") #Please Contact Coordinator to for assistance with Eligibility Concerns
        return redirect('home')
    
    # Fetch max proponents setting
    max_proponents = ProjectGroupSettings.get_max_proponents()

    # Check for existing approved groups 
    approved_groups = Project_Group.objects.filter(proponents=request.user, approved=True)
    
    if approved_groups.exists():
        messages.error(request, "You are already part of an approved project group and cannot create a new one.")
        return redirect('my-project-group-waitlist')

    # Check for pending project groups
    pending_groups = Project_Group.objects.filter(proponents=request.user, approved=False)
    
    if pending_groups.exists():
        messages.error(request, "You have a pending project group. Please leave the group before creating a new one.")
        return redirect('my-project-group-waitlist')
    
    pending_groups_for_approval =  Project_Group.objects.filter(pending_proponents=request.user, approved=False)

    if pending_groups_for_approval.exists():
        messages.error(request, "You have a pending project group. Please decline the pending group before creating a new one.")
        return redirect('my-project-group-waitlist')
    
    submitted = False
    
    # Handle form Submission
    if request.method == "POST":
        form = ProjectGroupForm(
            request.POST, 
            user=request.user, 
            max_proponents=max_proponents, 
            approved_users=get_user_ids_with_group(request)
        )

        if form.is_valid():
            project = form.save(commit=False)
            
            try:
                student_creator = Student.objects.get(id=request.user.id)
            except Student.DoesNotExist:
                messages.error(request, "Student profile not found.")
                return redirect('home')

            selected_proponents = form.cleaned_data['proponents']
            other_proponents = [p for p in selected_proponents if p.id != request.user.id]
            
            # Validate minimum group size
            if len(other_proponents) == 0:
                messages.error(request, "You must select at least one other student for the group.")
                return render(request, 'project/add_project_group.html', {
                    'form': form,
                    'submitted': False
                })
            
            project.creator = student_creator
            project.save()
            
            # Add relationships
            project.approved_by_students.add(student_creator)
            project.proponents.add(student_creator)
            
            # Add relationships and create notifications
            for proponent in other_proponents:
                project.pending_proponents.add(proponent)
                
                try:
                    # Create notification with error handling
                    notification = Notification.objects.create(
                        recipient=proponent,
                        notification_type='INVITATION',
                        group=project,
                        sender=student_creator,
                        message=f"{student_creator.get_full_name()} has invited you to join a project group.",
                        redirect_url=reverse('my-project-group-waitlist')
                    
                    )
                    logger.debug(f"Created notification {notification.id} for {proponent}")
                except Exception as e:
                    logger.error(f"Failed to create notification for {proponent}: {str(e)}")
            
            messages.success(request, "Group created and invitations sent to selected students.")
            return HttpResponseRedirect('/add_project_group?submitted=True') 
    else:
        form = ProjectGroupForm(user=request.user, approved_users=get_user_ids_with_group(request))
        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'project/add_project_group.html', {
        'form':form, 
        'submitted':submitted,
        'max_proponents': max_proponents,
    })

    
def my_profile(request, profile_id): 
    if request.user.is_authenticated: 
        # look on user objects by ID 
        user = User.objects.get(pk=profile_id)
        
        if user.role == "STUDENT": 
            student_id = user.id    

            # # Get the project groups associated with this student
            # project_group = Project_Group.objects.filter(approved=True).filter(proponents=user)
            
             # Redirect to show_student view, passing the student_id in the URL
            return redirect('show-student', student_id=student_id)
        
        elif user.role =='FACULTY':
            faculty_id = user.id
             # Handle faculty profile
            return redirect('show-faculty', faculty_id=faculty_id)
        
        elif user.is_current_coordinator: 
            id = user.id
            return redirect('show-faculty', faculty_id=id)
              # Handle Coordinator profile
            # return redirect('show-faculty', faculty_id=faculty_id)
        
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
def show_student(request, student_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        student = Student.objects.get(pk=student_id)
        project_group = Project_Group.objects.filter(approved=True).filter(proponents=student)
        
        # pass it to the page using render 
        return render(request, 'project/show_student.html', 
        {'student': student, 
         'project_group': project_group}) 
    
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')

def show_faculty(request, faculty_id): 
    if request.user.is_authenticated: 
        
        user = User.objects.get(pk=faculty_id)

        # Check if the user is a current coordinator
        if user.is_current_coordinator:
            # Pass it to the page using render
            return render(request, 'project/show_coordinator.html', {
                'faculty': user, 
            })
        
        elif user.role=='FACULTY': # Look up faculty by ID
            faculty = Faculty.objects.get(pk=faculty_id)
            projects = Project.objects.filter(status='approved', adviser=faculty)
            
            # Pass it to the page using render
            return render(request, 'project/show_faculty.html', {
                'faculty': faculty, 
                'projects': projects,
            })
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
def generate_report(request):
    if request.user.is_authenticated: 
        # total advisers
        # total students enrolled 
        # total groups 
        # topic of each group 
        # Defense success/fail record, current progress 

        adviser_count = Faculty.objects.filter(role='FACULTY').filter(adviser_eligible=True).count
        student_count = Student.objects.filter(role='STUDENT').filter(eligible=True ).count 
        project_group_count = Project_Group.objects.count 
        panelist_count = Faculty.objects.filter(role='FACULTY').filter(panel_eligible=True).count
        # projects = Project.objects.all()

        student_uneligible_count = Student.objects.filter(role='STUDENT').filter(eligible=False ).count
        adviser_uneligible_count = Faculty.objects.filter(role='FACULTY').filter(adviser_eligible=False).count
        panel_uneligible_count = Faculty.objects.filter(role='FACULTY').filter(panel_eligible=False).count
        
        project_group_count = Project_Group.objects.count
        unapproved_project_group_count = Project_Group.objects.filter(approved=False).count

        # Get all projects with their phases
        projects = ApprovedProject.objects.prefetch_related('phases').all()

        # Create a dictionary to store defense results for each project
        projects_with_phases = []
        for project in projects:
            defense_results = {
                'proposal': 'Not Started',
                'design': 'Not Started',
                'preliminary': 'Not Started',
                'final': 'Not Started'
            }
            
            # Get the latest verdict for each phase type
            for phase_type in ['proposal', 'design', 'preliminary', 'final']:
                latest_phase = project.phases.filter(
                    phase_type=phase_type
                ).order_by('-date').first()
                
                if latest_phase:
                    defense_results[phase_type] = latest_phase.get_verdict_display()

            projects_with_phases.append({
                'project': project,
                'defense_results': defense_results
            })

        return render(request, 'project/generate_report.html', {
        "adviser_count": adviser_count, 
        "student_count": student_count,
        "project_group_count": project_group_count,
        "projects": projects, 
        "student_uneligible_count": student_uneligible_count, 
        "adviser_uneligible_count": adviser_uneligible_count, 
        "panelist_count": panelist_count,
        "panel_uneligible_count": panel_uneligible_count,
        "project_group_count": project_group_count, 
        "unapproved_project_group_count": unapproved_project_group_count,
        'projects_with_phases': projects_with_phases,
        })
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')


def get_user_project_group(request):
    if not request.user.is_authenticated:
       return None

     # Assuming 'Student' model has a OneToOne relation with User
    try:
        student = Student.objects.get(id=request.user.id)

    except Student.DoesNotExist:
        return None
    # Get the project that the student is part of
    project_group =  Project_Group.objects.filter(proponents=student)
    
    if project_group.exists():
        # Return the first group or handle accordingly
        return project_group.first() 
    
    else: 
        return None
    
def coordinator_approval_faculty(request): 
    if request.user.is_authenticated: 
        # Get counts 
        project_count = Project.objects.filter(status='approved').count
        proposal_count = Project.objects.filter(status='pending').count
        student_count = User.objects.filter(role='STUDENT').count
        faculty_count = User.objects.filter(role='FACULTY').count
        
        # get list of faculty 
        faculty_list = User.objects.filter(role='FACULTY').order_by('last_name')
        
        if request.user.role == 'COORDINATOR':
            if request.method == "POST":  
                id_list = request.POST.getlist('boxes')

                # Unchecked all users 
                faculty_list.update(adviser_eligible=False)
        
                # update the database
                for x in id_list: 
                    User.objects.filter(pk=int(x)).update(adviser_eligible=True)
                
                    # try:
                    #     Notification.objects.create(
                    #         recipient=User.objects.get(pk=int(x)),
                    #         notification_type='ADVISER_ELIGIBILITY',
                    #         message="You have been marked as eligible to be an adviser."
                    #     )
                    # except Exception as e:
                    #     logger.error(f"Failed to create notification for adviser eligibility: {str(e)}")

                panel_id_list = request.POST.getlist('box')
                
                # Unchecked all users 
                faculty_list.update(panel_eligible=False)
                
                # update the database
                for y in panel_id_list: 
                    User.objects.filter(pk=int(y)).update(panel_eligible=True)
                
                messages.success(request, "Faculty Approval Form has been updated")
                return redirect('coordinator-approval-faculty')
            else: 
                # # Paginate the faculty list
                # paginator = Paginator(faculty_list, 5)  # Show 10 faculty members per page
                # page_number = request.GET.get('page')
                # paginated_faculty = paginator.get_page(page_number)
                # nums = "a" * paginated_faculty.paginator.num_pages

                return render(request, 
                'project/coordinator_approval_faculty.html', 
                {
                    'faculty_list': faculty_list, 
                    "project_count": project_count,
                    "proposal_count": proposal_count,
                    "student_count": student_count, 
                    "faculty_count": faculty_count,
                  
                })    
        else: 
            messages.error(request, "You aren't authorized to view this Page ")
            return redirect('home')
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
def coordinator_approval_student(request): 
    if request.user.is_authenticated: 
        # Get counts 
        project_count = Project.objects.filter(status='approved').count
        proposal_count = Project.objects.filter(status='pending').count
        student_count = User.objects.filter(role='STUDENT').count
        faculty_count = User.objects.filter(role='FACULTY').count
        student_list = User.objects.filter(role='STUDENT').order_by('last_name')
        
        # get list of faculty 
        faculty_list = User.objects.filter(role='FACULTY').order_by('last_name')
        
        if request.user.role == 'COORDINATOR':
            if request.method == "POST":  
                student_box_list = request.POST.getlist('student_box')
                student_list.update(eligible=False)
                for z in student_box_list:
                    User.objects.filter(pk=int(z)).update(eligible=True)

                messages.success(request, "Student Approval Form has been updated")
                # Create a notification for the student
                # Update notifications
                return redirect('coordinator-approval-student')
            else: 
    
                return render(request, 
                'project/coordinator_approval_student.html', 
                {
                    'faculty_list': faculty_list, 
                    "project_count": project_count,
                    "proposal_count": proposal_count,
                    "student_count": student_count, 
                    "faculty_count": faculty_count,
                    "student_list": student_list,  # Use paginated students
                    
                })    
        else: 
            messages.error(request, "You aren' authorized to view this Page ")
            return redirect('home')
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
       
def coordinator_projects(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
    if request.user.role not in ['COORDINATOR', 'FACULTY']:
        messages.error(request, "You are not authorized to view this page")
        return redirect('login')
    
    # Grab the projects from that adviser
    approved_projects = Project.objects.filter(status='approved', is_archived=False).order_by('title')
    
    approved_paginator = Paginator(approved_projects, 10)  # Show 10 projects per page
    approved_page_number = request.GET.get('approved_page')
    approved_page_obj = approved_paginator.get_page(approved_page_number)  
    approved_nums = "a" * approved_page_obj.paginator.num_pages

    # Prepare data for each project with its groups and proponents
    approved_projects_with_groups = []
    for project in approved_page_obj:
        project_group = Project_Group.objects.filter(project=project, approved=True).first()
        
        # Fetch the project where the current group are the proponents
        project = Project.objects.filter(proponents=project_group, status='approved').first()
        
        if project_group and project: 
            proponents = list(project_group.proponents.all())
            proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
            
            # Fetch panel members directly from the project_group
            panel_members = list(project.panel.all())  # Fetch panel members
            panel_members += [None] * (3 - len(panel_members))  # Pad to exactly 3 panel members
            
            approved_projects_with_groups.append({
                'project': project,
                'group': project_group,
                'proponents': proponents, 
                'panel': panel_members,
                # 'status': project.status,
            })

    return render(request, 'project/coordinator_projects.html', {
        "approved_projects_with_groups": approved_projects_with_groups,
        "approved_page_obj": approved_page_obj,
        "approved_nums": approved_nums,
    })


def adviser_projects(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
    if request.user.role !='FACULTY': 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

    adviser = request.user.id
    # Grab the projects from that adviser
    approved_projects = Project.objects.filter(adviser=adviser, status='approved').order_by('title')
    
    approved_paginator = Paginator(approved_projects, 2)  # Show 10 projects per page
    approved_page_number = request.GET.get('approved_page')
    approved_page_obj = approved_paginator.get_page(approved_page_number)  
    approved_nums = "a" * approved_page_obj.paginator.num_pages

    # Calculate the start index for the current page
    start_index = (approved_page_obj.number - 1) * approved_page_obj.paginator.per_page

    # Prepare data for each project with its groups and proponents
    approved_projects_with_groups = []
    for project in approved_page_obj:
        project_group = Project_Group.objects.filter(project=project, approved=True).first()
        
        # Fetch the project where the current group are the proponents
        project = Project.objects.filter(proponents=project_group, status='approved').first()
        
        if project_group and project: 
            proponents = list(project_group.proponents.all())
            proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
            
            # Fetch panel members directly from the project_group
            panel_members = list(project.panel.all())  # Fetch panel members
            panel_members += [None] * (3 - len(panel_members))  # Pad to exactly 3 panel members
            
            approved_projects_with_groups.append({
                'project': project,
                'group': project_group,
                'proponents': proponents, 
                'panel': panel_members,
                # 'status': project.status,
            })


    return render(request, 'project/adviser_projects.html', {
        "approved_projects_with_groups": approved_projects_with_groups,
        "approved_page_obj": approved_page_obj,
        "approved_nums": approved_nums,
        'start_index': start_index, 
    })


def adviser_proposals(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
    if request.user.role != 'FACULTY': 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

    adviser = request.user.id
    # Fetch projects where the adviser is the logged-in user and the status is either pending or declined
    not_approved_projects = Project.objects.filter(adviser=adviser, status__in=['pending', 'declined']).order_by('title')
    
    not_approved_paginator = Paginator(not_approved_projects, 10)  # Show 5 projects per page
    not_approved_page_number = request.GET.get('not_approved_page')
    not_approved_page_obj = not_approved_paginator.get_page(not_approved_page_number)
    not_approved_nums = "a" * not_approved_page_obj.paginator.num_pages

    not_approved_projects_with_groups = []
    for project in not_approved_page_obj:
        project_group = project.proponents  # Directly use the project's proponents
        
        if project_group: 
            proponents = list(project_group.proponents.all())
            proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
            
            # Fetch panel members directly from the project
            panel_members = list(project.panel.all())  # Fetch panel members
            panel_members += [None] * (3 - len(panel_members))  # Pad to exactly 3 panel members
        
            not_approved_projects_with_groups.append({
                'project': project,
                'group': project_group,
                'proponents': proponents,
                'panel': panel_members,
            })

    return render(request, 'project/adviser_proposals.html', {
        "not_approved_projects_with_groups": not_approved_projects_with_groups,
        "not_approved_page_obj": not_approved_page_obj,
        "not_approved_nums": not_approved_nums,
    })
def panel_projects(request): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
    if request.user.role != 'FACULTY': 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

    # Instead of filtering by adviser, filter by panel members
    approved_projects = Project.objects.filter(panel=request.user, status='approved').order_by('title')
    
    approved_paginator = Paginator(approved_projects, 5)  # Show 10 projects per page
    approved_page_number = request.GET.get('approved_page')
    approved_page_obj = approved_paginator.get_page(approved_page_number)  
    approved_nums = "a" * approved_page_obj.paginator.num_pages

    # Prepare data for each project with its groups and proponents
    approved_projects_with_groups = []
    for project in approved_page_obj:
        project_group = Project_Group.objects.filter(project=project, approved=True).first()
        
        # Fetch the project where the current group are the proponents
        # This line is no longer necessary since we already have the project
        # project = Project.objects.filter(proponents=project_group, status='approved').first()
        
        if project_group: 
            proponents = list(project_group.proponents.all())
            proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
            
            # Fetch panel members directly from the project_group
            panel_members = list(project.panel.all())  # Fetch panel members
            panel_members += [None] * (3 - len(panel_members))  # Pad to exactly 3 panel members
            
            approved_projects_with_groups.append({
                'project': project,
                'group': project_group,
                'proponents': proponents, 
                'panel': panel_members,
                # 'status': project.status,
            })

    return render(request, 'project/panel_projects.html', {
        "approved_projects_with_groups": approved_projects_with_groups,
        "approved_page_obj": approved_page_obj,
        "approved_nums": approved_nums,
    })

def reject_project(request, project_id):
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser: 
        project.status = 'declined'
        project.save()

        # Notify all proponents about the project rejection
        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PROJECT_REJECTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"Your project '{project.title}' has been rejected by the adviser: {request.user.get_full_name()}.",
                    redirect_url=reverse('list-proposals')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")

        messages.success(request, f"Project '{project.title}' has been moved to 'Proposal list' Succesfully ! ")
        return redirect('adviser-projects')
    else:
        messages.error(request, "You Aren't Authorized to Accept this Proposal!")
        return redirect('adviser-projects')
    
def reject_proposal(request, project_id):
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser: 
        project.status = 'declined'
        project.save()

        # Notify all proponents about the project rejection
        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PROJECT_REJECTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"Your project '{project.title}' has been rejected by the adviser: {request.user.get_full_name()}.",
                    redirect_url=reverse('list-proposals')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")

        messages.success(request, f"Project '{project.title}' has been Rejected Succesfully ! ")
        return redirect('adviser-proposals')
    else:
        messages.error(request, "You Aren't Authorized to Accept this Proposal!")
        return redirect('adviser-proposals')

def archive_project(request, project_id):
    if not request.user.is_authenticated: 
        messages.error(request, "You Aren't Authorized to archive this Project.")
        return redirect('login')

    # look on projects by ID 
    if request.user.is_current_coordinator: 
        project = Project.objects.get(pk=project_id)
        project.is_archived = True
        project.save()

        messages.success(request, f"Project '{project.title}' has been Archived Succesfully! ")
        return redirect('coordinator-projects')
    else:
        messages.error(request, "You Aren't Authorized to Archive this Project!")
        return redirect('home')

def unarchive_project(request, project_id):
    if not request.user.is_authenticated: 
        messages.error(request, "You Aren't Authorized to Unarchive this Project.")
        return redirect('home')
    
    # look on projects by ID 
    if request.user.is_current_coordinator:  
        project = Project.objects.get(pk=project_id)
        project.is_archived = False
        project.save()

        messages.success(request, f"Project '{project.title}' has been Unarchived Succesfully! ")
        return redirect('list-archived-projects')
    
    else:
        messages.error(request, "You Aren't Authorized to Archive this Project!")
        return redirect('home')

def list_archived_projects(request): 

    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
    if request.user.role !='COORDINATOR' or not request.user.is_current_coordinator: 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

   
    # Grab the projects from that adviser
    archived_projects = Project.objects.filter(status='approved', is_archived=True).order_by('title')
    
    approved_paginator = Paginator(archived_projects, 5)  # Show 10 projects per page
    approved_page_number = request.GET.get('approved_page')
    approved_page_obj = approved_paginator.get_page(approved_page_number)  
    approved_nums = "a" * approved_page_obj.paginator.num_pages

    # Prepare data for each project with its groups and proponents
    archived_projects_with_groups = []
    for project in approved_page_obj:
        project_group = Project_Group.objects.filter(project=project, approved=True).first()
        
        # Fetch the project where the current group are the proponents
        project = Project.objects.filter(proponents=project_group, status='approved').first()
        
        if project_group and project: 
            proponents = list(project_group.proponents.all())
            proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
            
            # Fetch panel members directly from the project_group
            panel_members = list(project.panel.all())  # Fetch panel members
            panel_members += [None] * (3 - len(panel_members))  # Pad to exactly 3 panel members
            
            archived_projects_with_groups.append({
                'project': project,
                'group': project_group,
                'proponents': proponents, 
                'panel': panel_members,
                # 'status': project.status,
            })


    return render(request, 'project/archived_projects.html', {
        "archived_projects_with_groups": archived_projects_with_groups,
        "approved_page_obj": approved_page_obj,
        "approved_nums": approved_nums,
    })

# def archive_proposal(request, project_id):
#     # look on projects by ID 
#     project = Project.objects.get(pk=project_id)
#     if request.user == project.adviser: 
#         project.is_archived = 'True'
#         project.save()

#         messages.success(request, f"Project '{project.title}' has been Archived Succesfully! ")
#         return redirect('adviser-proposals')
#     else:
#         messages.success(request, "You Aren't Authorized to Archive this Project!")
#         return redirect('adviser-proposals')
    
    
# def unarchive_proposal(request, project_id):
#     # look on projects by ID 
#     project = Project.objects.get(pk=project_id)
#     if request.user == project.adviser: 
#         project.is_archived = False
#         project.save()

#         messages.success(request, f"Project '{project.title}' has been Archived Succesfully! ")
#         return redirect('adviser-proposals')
#     else:
#         messages.success(request, "You Aren't Authorized to Archive this Project!")
#         return redirect('adviser-proposals')


# def archive_project(request, project_id):
#     # look on projects by ID 
#     project = Project.objects.get(pk=project_id)
#     if request.user == project.adviser: 
#         project.archive = 'True'
#         project.save()

#         messages.success(request, f"Project '{project.title}' has been Archived Succesfully! ")
#         return redirect('adviser-projects')
#     else:
#         messages.success(request, "You Aren't Authorized to Archive this Project!")
#         return redirect('adviser-projects')
    
# Accept Project
def accept_proposal(request, project_id): 
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser: 
        # Decline other proposals for the same project group
        Project.objects.filter(
            proponents=project.proponents,  # Filter by the same project group
            adviser=project.adviser
        ).exclude(id=project_id).update(status='declined')
        
        # Approve the current proposal
        project.status = 'approved'
        project.save()

        # Notify all proponents about the project acceptance
        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PROJECT_ACCEPTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"Your project '{project.title}' has been accepted by the adviser: {request.user.get_full_name()}.",
                    redirect_url=reverse('list-projects'),
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")
        
        messages.success(request, "Proposal Accepted Successfully!")
    else:
        messages.error(request, "You Aren't Authorized to Accept this Proposal!")
    
    return redirect('adviser-projects')

# Delete Project
def delete_proposal(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('login')

    # look on projects by ID 
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        messages.error(request, "The project does not exist.")
        return redirect('adviser-proposals')

    if request.user == project.adviser:   
        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PROPOSAL_DELETED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"The proposal entitled '{project.title}' has been deleted by the adviser: {request.user.get_full_name()}.",
                    redirect_url=reverse('list-proposals')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")
        project.delete()
        messages.success(request, "Proposal Deleted Succesfully ! ")
        return redirect('adviser-proposals')
    else:
        messages.error(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('home')

        
def student_delete_proposal(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('home')
    # look on projects by ID 
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        messages.error(request, "The project does not exist.")
        return redirect('list-proposals')

    if request.user in project.proponents.proponents.all():   
        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PROPOSAL_DELETED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"The project '{project.title}' has been deleted by a student, {request.user.get_full_name()}.",
                    redirect_url=reverse('list-proposals')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")
        
        # Notify the adviser about the project deletion
        try:
            Notification.objects.create(
                recipient=project.adviser,  # Assuming adviser is a User instance
                notification_type='PROPOSAL_DELETED',
                group=project.proponents,
                sender=request.user,
                message=f"The project proposal '{project.title}' has been deleted by a student, {request.user.get_full_name()}.",
                redirect_url=reverse('adviser-proposals')
            )
        except Exception as e:
            logger.error(f"Failed to create notification for adviser {project.adviser}: {str(e)}")
        project.delete()
        messages.success(request, "Proposal Deleted Succesfully ! ")
        return redirect('list-proposals')
  
        
def select_panelist(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
    if request.user.role  != 'FACULTY':
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    # if they are gonna post, use this form otherwise, don't use anything. 
    if request.user == project.adviser: 
        form = SelectPanelistForm(request.POST or None, instance=project)
        form.user = request.user # pass the user to the form

        # Capture the initial panelists
        # initial_panelists = set(project.panel.all())

    # save data to the database and return somewhere 
    if form.is_valid():
        # Handle disabled fields by reassigning their initial values before saving
        form.instance.title = project.title
        form.instance.project_type = project.project_type
        form.instance.proponents = project.proponents
        form.instance.adviser = project.adviser
        form.instance.description = project.description
        form.save()

        # Get the newly selected panelists
        selected_panelists = set(form.cleaned_data['panel'])
        # new_panelists = selected_panelists - initial_panelists

        for panelist in selected_panelists:
            try:
                Notification.objects.create(
                    recipient=panelist,
                    notification_type='PANELIST_SELECTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"You have been selected as a panelist for the project '{project.title}' with the Adviser: {request.user.get_full_name()}.",
                    redirect_url=reverse('panel-projects'),
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {panelist}: {str(e)}")

         # Notify all proponents about the panelist selection
        for proponent in project.proponents.proponents.all():  # Changed from selected_panelists to project.proponents.proponents.all()
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PANELIST_SELECTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"The Panel for the project '{project.title}' has been updated. Panelists: {', '.join([panelist.get_full_name() for panelist in selected_panelists])}.",
                    redirect_url=reverse('my-project'),
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")

        try:
            coordinator = User.objects.get(is_current_coordinator=True)  # Adjust this query based on your model
            Notification.objects.create(
                recipient=coordinator,
                notification_type='PANELIST_SELECTED',
                group=project.proponents,
                sender=request.user,
                message=f"The Panel for the project '{project.title}' has been updated. New panelists: {', '.join([panelist.get_full_name() for panelist in selected_panelists])}.",
                redirect_url=reverse('coordinator-projects'),
            )
        except User.DoesNotExist:
            logger.error("No current coordinator found to notify.")


        messages.success(request, "Project Panel Updated Successfully!")
        return redirect('adviser-projects')
      
    else:
        form.fields['panel'].initial = form.instance.panel.all()[:1]

    return render(request, 'project/select_panelist.html', {
        'project': project,
        'form': form
    })

def update_project_idea(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
    if request.user.role == 'STUDENT' :
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('home')

     # Attempt to look up the project by ID
    try:
        project = Project_Idea.objects.get(pk=project_id)
    except Project_Idea.DoesNotExist:
        messages.error(request, "The project idea does not exist.")
        return redirect('all-project-ideas')
    
    # if they are gonna post, use this form otherwise, don't use anything. 
    if request.user == project.faculty or request.user.is_current_coordinator: 
        form = ProjectIdeaForm(request.POST or None, instance=project)

    if form.is_valid(): 
        # Handle disabled fields by reassigning their initial values before saving
        if isinstance(form, ProjectIdeaForm):  # Check if using UpdateProjectForm
            form.instance.title = project.title
            form.instance.description = project.description
            form.instance.faculty = project.faculty
        
        form.save()

        messages.success(request, "Project Idea Updated Successfully!")
        return redirect('all-project-ideas')
    

    return render(request, 'project/update_project_idea.html', {
        'project': project,
        'form': form
    })

def select_panelist_coordinator(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
    if not request.user.is_current_coordinator: 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    # if they are gonna post, use this form otherwise, don't use anything. 

     # Check if the project already has two panelists selected
    if project.panel.count() < 2:
        messages.error(request, "Please wait until the Project adviser and students have selected their panelists.")
        return redirect('coordinator-projects')

    form = CoordinatorSelectPanelistForm(request.POST or None, instance=project)
    form.user = request.user # pass the user to the form
    # save data to the database and return somewhere 
    
    # Capture the initial panelists
    initial_panelists = set(project.panel.all())
    
    if form.is_valid():
        # Handle disabled fields by reassigning their initial values before saving
        form.instance.title = project.title
        form.instance.project_type = project.project_type
        form.instance.proponents = project.proponents
        form.instance.adviser = project.adviser
        form.instance.description = project.description
        form.save()

        # Get the newly selected panelists
        selected_panelists = set(form.cleaned_data['panel'])
        new_panelists = selected_panelists - initial_panelists

        for panelist in new_panelists:
            try: # inform panelist 
                Notification.objects.create(
                    recipient=panelist,
                    notification_type='PANELIST_SELECTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"You have been selected as a panelist for the project '{project.title}' by coordinator {request.user.get_full_name()}.",
                    redirect_url=reverse('panel-projects'),
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {panelist}: {str(e)}")

        # Notify the project adviser about the panelist selection
        try:
            Notification.objects.create(
                recipient=project.adviser,
                notification_type='PANELIST_SELECTED',
                group=project.proponents,
                sender=request.user,
                message=f"The Panel for the project '{project.title}' has been updated. New panelists: {', '.join([panelist.get_full_name() for panelist in selected_panelists])}.",
                redirect_url=reverse('adviser-projects'),
            )
        except Exception as e:
            logger.error(f"Failed to create notification for adviser {project.adviser}: {str(e)}")


        # Notify all proponents about the panelist selection
        for proponent in project.proponents.proponents.all():  # Changed from selected_panelists to project.proponents.proponents.all()
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PANELIST_SELECTED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"The Panel for the project '{project.title}' has been updated. Panelists: {', '.join([panelist.get_full_name() for panelist in selected_panelists])}.",
                    redirect_url=reverse('my-project'),
                
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")


        messages.success(request, "Project Panel Updated Successfully!")
        return redirect('coordinator-projects')
    else:
        form.fields['panel'].initial = form.instance.panel.all()[:2]

    return render(request, 'project/select_panelist_coordinator.html', {
        'project': project,
        'form': form
    })


# def select_defense_phases(request, project_id): 
#     if not request.user.is_authenticated: 
#         messages.error(request, "Please Login to view this page")
#         return redirect('home')
    
#     if request.user.role != 'COORDINATOR' or not request.user.is_current_coordinator:
#         messages.error(request, "You are not authorized to view this page")
#         return redirect('home')

#     # look on projects by ID 
#     project = Project.objects.get(pk=project_id)
#     # if they are gonna post, use this form otherwise, don't use anything. 

#     form = CoordinatorSelectPanelistForm(request.POST or None, instance=project)
#     form.user = request.user # pass the user to the form
#     # save data to the database and return somewhere 

#     if form.is_valid():
#         # Handle disabled fields by reassigning their initial values before saving
#         form.instance.title = project.title
#         form.instance.project_type = project.project_type
#         form.instance.proponents = project.proponents
#         form.instance.adviser = project.adviser
#         form.instance.description = project.description
#         form.save()

#         messages.success(request, "Project Phases Updated Successfully!")
#         return redirect('coordinator-projects')


#     return render(request, 'project/select_defense_phases.html', {
#         'project': project,
#         'form': form
#     })

def add_comments(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
        
     # Attempt to look up the project by ID
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        messages.error(request, "The project does not exist.")
        return redirect('home')
    
    # if they are gonna post, use this form otherwise, don't use anything. 
    if request.user == project.adviser: 
        form = AddCommentsForm(request.POST or None, instance=project)
    
    # save data to the database and return somewhere 
    if form.is_valid(): 
        # Handle disabled fields by reassigning their initial values before saving
        if isinstance(form, AddCommentsForm):  # Check if using UpdateProjectForm
            form.instance.title = project.title
            form.instance.project_type = project.project_type
            form.instance.proponents = project.proponents
            form.instance.adviser = project.adviser
            form.instance.description = project.description
            form.instance.comments = project.comments
        form.save()

        # Send notifications to all proponents
        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='COMMENTS_UPDATED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"Comments have been updated for the project '{project.title}'.",
                    redirect_url=reverse('list-proposals'),
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")

        messages.success(request, "Project Comments Updated Succesfully!")
        return redirect('adviser-proposals')
    else:
        # Reinitialize the panel with the pre-selected panelist to retain form state
        form.fields['panel'].initial = form.instance.panel.all()[:1]

    # pass it to the page using render 
    return render(request, 'project/add_comments.html', 
    {'project': project, 
    'form': form})
   

# def update_project(request, project_id): 
#     if request.user.is_authenticated: 
#         # look on projects by ID 
#         project = Project.objects.get(pk=project_id)
#         # if they are gonna post, use this form otherwise, don't use anything. 
#         if request.user == project.adviser: 
#             form = UpdateProjectForm(request.POST or None, instance=project)
       
#         # save data to the database and return somewhere 
#         if form.is_valid(): 
#              # Handle disabled fields by reassigning their initial values before saving
#             if isinstance(form, UpdateProjectForm):  # Check if using UpdateProjectForm
#                 form.instance.title = project.title
#                 form.instance.project_type = project.project_type
#                 form.instance.proponents = project.proponents
#                 form.instance.adviser = project.adviser
#                 form.instance.description = project.description
                
#             form.save()
#             messages.success(request, "Project Updated Succesfully! ")
#             return redirect('adviser-projects')
#         else:
#             # Add error messages from the form validation
#             # for field, errors in form.errors.items():
#             #     for error in errors:
#             #         messages.error(request, f"{field}: {error}")
            
#              # Reinitialize the panel with the pre-selected panelist to retain form state
#             form.fields['panel'].initial = form.instance.panel.all()[:1]

#         # pass it to the page using render 
#         return render(request, 'project/update_project.html', 
#         {'project': project, 'form': form})
#     else: 
#         messages.error(request, "You Aren't Authorized to view this page.")
#         return redirect('home')
    
    # Delete Project
def delete_project(request, project_id):
    if not request.user.is_authenticated: 
        messages.error(request, "You Aren't Authorized to Delete this Project!")
        return redirect('home')

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        messages.error(request, "The project does not exist.")
        return redirect('home')
    
    if request.user == project.adviser or request.user.is_current_coordinator:    

        for proponent in project.proponents.proponents.all():
            try:
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='PROJECT_DELETED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"The Project entitled '{project.title}' has been deleted by {request.user.get_full_name()}.",
                    redirect_url=reverse('my-project')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {proponent}: {str(e)}")

        if request.user.is_current_coordinator: 
            try:
                Notification.objects.create(
                    recipient=project.adviser,
                    notification_type='PROJECT_DELETED',
                    group=project.proponents,
                    sender=request.user,
                    message=f"The Project entitled '{project.title}' has been deleted by {request.user.get_full_name()}.",
                    redirect_url=reverse('adviser-projects')
                )

            except Exception as e:
                logger.error(f"Failed to create notification for {project.adviser}: {str(e)}")

        project.delete()
        messages.success(request, "Project Deleted Succesfully ! ")
        
        role = request.user.role
        if role == 'FACULTY': 
            return redirect('adviser-projects')
        else:
            return redirect('coordinator-projects')

    else: 
        messages.error(request, "You Aren't Authorized to Delete this Project!")
        return redirect('home')


# def delete_project_coordinator(request, project_id):

#     #  if not request.user.is_authenticated: 
#     #     messages.error(request, "You Aren't Authorized to Delete this Project Idea!")
#     #     return redirect('home')

#     # # Look for the project idea by ID
#     # try:
#     #     project = Project_Idea.objects.get(pk=project_id)
#     # except Project_Idea.DoesNotExist:
#     #     messages.error(request, "The project idea does not exist.")
#     #     return redirect('all-project-ideas')

#     # if request.user == project.faculty or request.user.is_current_coordinator: 
#     #     project.delete()
#     #     messages.success(request, "Project Idea Deleted Successfully!")
#     #     return redirect('all-project-ideas')
#     # else:
#     #     messages.error(request, "You Aren't Authorized to Delete this Project Idea!")
#     #     return redirect('home')

#     if not request.user.is_current_coordinator: 
#         messages.error(request, "You Aren't Authorized to Delete this Project!")
#         return redirect('home')

#         # look on projects by ID 
#     try:     
#         project = Project.objects.get(pk=project_id)
#     except Project.DoesNotExist:
#         messages.error(request, "The project does not exist.")
#         return redirect('home')
    
     
#     for proponent in project.proponents.proponents.all():
#         try:
#             Notification.objects.create(
#                 recipient=proponent,
#                 notification_type='PROJECT_DELETED',
#                 group=project.proponents,
#                 sender=request.user,
#                 message=f"The Project entitled '{project.title}' has been deleted by {request.user.get_full_name()}.",
#                 redirect_url=reverse('my-project')
#             )
#         except Exception as e:
#             logger.error(f"Failed to create notification for {proponent}: {str(e)}")

#     project.delete()
#     messages.success(request, "Project Deleted Succesfully ! ")


def delete_project_idea(request, project_id):
    if not request.user.is_authenticated: 
        messages.error(request, "You Aren't Authorized to Delete this Project Idea!")
        return redirect('home')


    # Look for the project idea by ID
    try:
        project = Project_Idea.objects.get(pk=project_id)
    except Project_Idea.DoesNotExist:
        messages.error(request, "The project idea does not exist.")
        return redirect('all-project-ideas')
    
    if request.user == project.faculty or request.user.is_current_coordinator: 
    
        project.delete()
        if request.user.is_current_coordinator: 
            try:
                Notification.objects.create(
                    recipient=project.faculty,
                    notification_type='PROJECT_DELETED',
                    sender=request.user,
                    message=f"The Project entitled '{project.title}' has been deleted by {request.user.get_full_name()}.",
                    redirect_url=reverse('all-project-ideas')
                )
            except Exception as e:
                logger.error(f"Failed to create notification for {project.faculty}: {str(e)}")

        
        messages.success(request, "Project Idea Deleted Successfully!")
        return redirect('all-project-ideas')
    else:
        messages.error(request, "You Aren't Authorized to Delete this Project Idea!")
        return redirect('home')
        
def search_projects(request): 
    # determine whether some has gone to the page 
    # or has fillout and posted to the page. 
    if request.method == 'POST': 
        searched = request.POST['searched']
        
        # query the database using searched 
        projects = Project.objects.filter(title__icontains=searched)
        return render(request, 'project/search_projects.html',
        {'searched':searched, 'projects': projects})
    else:
        return render(request, 'project/search_projects.html',
        {'searched':searched})

def list_student(request): 
    if request.user.is_authenticated: 
        student_list = Student.objects.filter(role='STUDENT').order_by('last_name')    
        
        # p = Paginator(Student.objects.filter(role='STUDENT').order_by('last_name'), 10) 
        # page = request.GET.get('page')
        # students = p.get_page(page)
        # nums = "a" * students.paginator.num_pages

        return render(request, 'project/student.html', 
        {'student_list': student_list })
        # {'students': students, 
        # 'nums': nums})
    else: 
        messages.error(request, "You Aren't Authorized to view this page.")
        return redirect('login')
    

def list_student_waitlist(request): 
    if request.user.is_authenticated: 
        # student_list = Student.objects.all().order_by('last_name')    
        
        p = Paginator(Student.objects.filter(role='STUDENT').filter(eligible=False).order_by('last_name'), 6) 
        page = request.GET.get('page')
        students = p.get_page(page)
        nums = "a" * students.paginator.num_pages

        return render(request, 'project/student_waitlist.html', 
        # {'student_list': student_list,
        {'students': students, 
        'nums': nums})
    else: 
        messages.error(request, "You Aren't Authorized to view this page.")
        return redirect('login')

    
def list_faculty(request): 
    if request.user.is_authenticated: 
        # student_list = Student.objects.all().order_by('last_name')    
        
        p = Paginator(Student.objects.filter(role='FACULTY').order_by('last_name'), 10) 
        page = request.GET.get('page')
        facultys = p.get_page(page)
        nums = "a" * facultys.paginator.num_pages

        return render(request, 'project/faculty.html', 
        {'facultys': facultys, 
        'nums': nums})
    else: 
        messages.error(request, "Please Login to view this page.")
        return redirect('login')

def add_project(request): 
    if request.user.is_authenticated: 
        
        group = get_user_project_group(request)
        if group is None:
            messages.error(request, "You are not a member of any Project Group. Please Register a Project Group First.")
            return redirect('home')
        
        if not group.approved:
            messages.error(request, "Your Project Group is not approved. Please Ensure all Students have approved before proceeding.")
            return redirect('my-project-group-waitlist')
            
        # Check if the group already has an approved project
        approved_project_exists = Project.objects.filter(
            proponents=group,
            status='approved'
        ).exists()

        if approved_project_exists:
            messages.error(request, "Your group already has an approved project. You cannot submit another project.")
            return redirect('my-project')
        
        if request.user.role == 'STUDENT': 
            submitted = False

            # Check for pending projects with an adviser
            pending_projects = Project.objects.filter(
                proponents=group,
                status='pending'
            )

            current_adviser = None
            if pending_projects.exists():
                current_adviser = pending_projects.first().adviser

            if request.method == "POST":
                form = ProjectForm(request.POST, user=request.user)
                if form.is_valid():
                    project = form.save(commit=False)
                    project.owner = request.user.id
                    project.project_group = group
                    project.save()
                
                    # Save the many-to-many relationships (e.g., panel members, proponents)
                    form.save_m2m()
                    # Send notifications to the adviser selected in the form and proponents excluding the logged-in user
                    selected_adviser = form.cleaned_data['adviser']  # Get the adviser from the form

                    
                    # Fetch the adviser instance
                    try:
                        adviser_instance = User.objects.get(id=selected_adviser.id)  # Assuming User is the model for advisers
                    except User.DoesNotExist:
                        logger.error(f"Adviser with ID {selected_adviser.id} does not exist.")
                        messages.error(request, "The selected adviser does not exist.")
                        return redirect('add_project')

                    # Send notifications to the adviser and proponents excluding the logged-in user
                    try:
                        # Notify the adviser
                        Notification.objects.create(
                            recipient=adviser_instance, 
                            notification_type='NEW_PROJECT_PROPOSAL',
                            group=project.proponents,
                            sender=request.user,
                            message=f"A new Project Proposal entitled '{project.title}' has been submitted by {request.user.get_full_name()}.", 
                            redirect_url = reverse('adviser-proposals') 
                        )
                    except Exception as e:
                        logger.error(f"Failed to create notification for adviser: {str(e)}")

                    # Notify all proponents excluding the logged-in user
                    for proponent in project.proponents.proponents.all():
                        if proponent != request.user:  # Exclude the logged-in user
                            try:
                                Notification.objects.create(
                                    recipient=proponent,
                                    notification_type='NEW_PROJECT_PROPOSAL',
                                    group=project.proponents,
                                    sender=request.user,
                                    message=f"A new Project Proposal '{project.title}' has been submitted by {request.user.get_full_name()}.",
                                    redirect_url = reverse('list-proposals') 
                                )
                            except Exception as e:
                                logger.error(f"Failed to create notification for proponent {proponent}: {str(e)}")
                    
                    
                    return HttpResponseRedirect('/add_project?submitted=True')
                else:
                    # Add a general error message
                    messages.error(request, "Please correct the errors below.")
            
            else:
                form = ProjectForm(initial={
                    'proponents': group,
                }, user=request.user)

                # Restrict adviser selection if there's a pending project
                if current_adviser:
                    form.fields['adviser'].queryset = User.objects.filter(id=current_adviser.id)
                
                if 'submitted' in request.GET:
                    submitted = True

            return render(request, 'project/add_project.html', {
                'group': group,
                'form': form, 
                'submitted': submitted
            })
        else: 
            messages.error(request, "Only Students are allowed to propose Projects.")
            return redirect('home')
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')

def home(request):
    return render(request, "project/home.html", {})

def home_faculty(request):
    return render(request, "project/home_faculty.html", {})

def home_student(request):
    return render(request, "project/home_student.html", {})


def all_projects(request):
    if request.user.is_authenticated: 
        # Create a Paginator object with the project list and specify the number of items per page
        p = Paginator(Project.objects.filter(status='approved', is_archived=False).order_by('title'), 8) 
        page = request.GET.get('page')
        projects = p.get_page(page)
        nums = "a" * projects.paginator.num_pages

        # Calculate the start index for the current page
        start_index = (projects.number - 1) * projects.paginator.per_page

        return render(request, 'project/project_list.html', {
            'projects': projects, 
            'nums': nums, 
            'start_index':  start_index,
        })
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
        
def all_proposals(request):
    if request.user.is_authenticated:

        group = get_user_project_group(request)
        # Filter projects where the logged-in user is a proponent
        project_list = Project.objects.filter(
            (Q(status='pending') | Q(status='declined')) & 
            Q(proponents=group)  # Assuming 'proponents' is the field name
        ).order_by('title')

        
        # Create a Paginator object with the project list and specify the number of items per page
        p = Paginator(project_list, 8)  # Show 8 proposals per page
        page = request.GET.get('page')
        projects = p.get_page(page)
        nums = "a" * projects.paginator.num_pages

        # Calculate the start index for the current page
        start_index = (projects.number - 1) * projects.paginator.per_page


        return render(request, 'project/proposal_list.html', {
            'projects': projects,
            'nums': nums,
            'start_index': start_index,
        })
    else:
        messages.error(request, "Please Login to view this page")
        return redirect('login')

def show_project(request, project_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        project = Project.objects.get(pk=project_id)
        project_owner = User.objects.get(pk=project.owner)
        
        # pass it to the page using render
        return render(request, 'project/show_project.html', 
        {'project': project, 
        'project_owner': project_owner})
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
def show_application(request, application_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        application = Defense_Application.objects.get(pk=application_id)        
          # Get the user object using the owner field
        try:
            owner_user = User.objects.get(pk=application.owner)
        except User.DoesNotExist:
            owner_user = None
       
       
        # pass it to the page using render
        return render(request, 'project/show_application.html', {
            'application': application, 
            'owner_user':  owner_user,
        })
    
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
def show_project_idea(request, project_idea_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        project_idea = Project_Idea.objects.get(pk=project_idea_id)
        # project_owner = User.objects.get(pk=project.owner)
        
        # pass it to the page using render
        return render(request, 'project/show_project_idea.html', 
        {'project_idea': project_idea})
    
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')
    
def show_proposal(request, project_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        project = Project.objects.get(pk=project_id)
        project_owner = User.objects.get(pk=project.owner)
        
        # pass it to the page using render
        return render(request, 'project/show_proposal.html', 
        {'project': project, 
        'project_owner': project_owner})
    else: 
        messages.error(request, "Please Login to view this page")
        return redirect('login')

@login_required
def delete_account(request, user_id):
    if not request.user.is_authenticated: 
        messages.error(request, "You're not authorized to perform this Action")
        return redirect('home')
    
    try:
        user_to_delete = User.objects.get(pk=user_id)
        user_to_delete.delete()
        messages.success(request, "Your account has been deleted successfully.")

    except User.DoesNotExist:
        messages.error(request, "User does not exist.")

        
    return redirect('home')  # In case of GET request, you can redirect to home (if needed)