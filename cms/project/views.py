from django.shortcuts import render, redirect
from .models import Project
from django.http import HttpResponseRedirect
from django.contrib import messages 
from django.conf import settings 
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import ProjectForm, CapstoneSubmissionForm, AddCommentsForm, ProjectGroupForm, ProjectGroupInviteForm
from .forms import  VerdictForm, CoordinatorForm, SelectPanelistForm, CoordinatorSelectPanelistForm
from .models import AppUserManager, Defense_Application
from .models import Student, Faculty, ApprovedProjectGroup,  Project_Group
from .models import StudentProfile, FacultyProfile, CoordinatorProfile, Coordinator
from .models import Project_Idea
from .forms import ProjectIdeaForm

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
logger = logging.getLogger(__name__)

# Import user model 
from django.contrib.auth import get_user_model 
User = get_user_model()

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
    if request.user.is_authenticated: 
        # Create a Paginator object with the project_ideas list and specify the number of items per page
        p = Paginator(Project_Idea.objects.order_by('title'), 10) 
        page = request.GET.get('page')
        project_ideas = p.get_page(page)
        nums = "a" * project_ideas.paginator.num_pages

        return render(request, 'project/all_project_ideas.html', {
         'project_ideas': project_ideas, 
        'nums': nums})
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')

def submit_project_idea(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page" )
        return redirect('home')
    
    if request.user.role != 'FACULTY': 
        messages.error(request, "Only Faculty are able to submit Project Ideas." )    
        return redirect('home')
        
    if request.method == 'POST':
        form = ProjectIdeaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('all-project-ideas')  # Redirect to the same page after submission
    else:
        form = ProjectIdeaForm(initial={'faculty': request.user, }, user=request.user)

    ideas = Project_Idea.objects.all()  # Retrieve all submitted ideas
    return render(request, 'project/submit_project_idea.html', {
        'form': form, 'ideas': ideas})

@login_required
def reject_panel_invitation(request, project_id):
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

@login_required
def notifications_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view your notifications.")
        return redirect('login')

    # Fetch all notifications for the logged-in user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
    
    # Mark all notifications as read
    notifications.update(is_read=True)

    return render(request, 'project/notifications.html', {
        'notifications': notifications,
        'unread_notifications': unread_notifications, 

    })

from django.views.decorators.http import require_POST

@require_POST
@login_required 
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
    
from django.views.decorators.http import require_http_methods

@require_http_methods(["DELETE"])
@login_required
def delete_notification(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)

@login_required
def select_coordinator(request):
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


@login_required
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

@login_required # Notification: Current members, 
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

@login_required
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
                message=f"Your join request to {group.creator.get_full_name()}'s group has been declined."
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
                    message=f"{user.get_full_name()} join request has been declined."
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
                    message=f"{request.user.get_full_name()} has requested to join your Project Group."
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
                    message=f"{request.user.get_full_name()}'s join request has been cancelled."
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
            # Save the verdict for the latest phase
            phase = form.save(commit=False)

            # Ensure you are setting the phase type here if it's blank
            if not phase.phase_type:
                phase.phase_type = latest_phase.phase_type  # or set to a default value if needed
            phase.save()
            
             # Create notifications for all proponents
            for proponent in application.project.proponents.proponents.all():
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='VERDICT',
                    group=application.project.proponents,
                    sender=request.user,
                                       message=f"The verdict for the {phase.get_phase_type_display()} phase of the project '{application.project.title}' is {phase.get_verdict_display()}.",
                )
            
            messages.success(request, "Verdict submitted successfully!")
            return redirect('list-defense-applications')
        else:
            messages.error(request, "There was an error with the form submission.")
            return render(request, 'project/submit_verdict.html', {'form': form, 'application': application})

    else:
        messages.error(request, "Invalid request method or you are not logged in.")
        return redirect('home')

def submit_defense_application(request):
    if request.user.is_authenticated: 
        user_group = get_user_project_group(request)
        
        if user_group is None:
            messages.warning(request, "You are not a member of any Project Group. Please Register a Project Group First.")
            return redirect('home')
            
        project = Project.objects.filter(proponents=user_group, status='approved').first()

        if project is None:
            messages.error(request, "No project found for your group. Please submit a project first and wait for approval from an Adviser.")
            return redirect('home')

        elif project.status == 'pending':
            messages.error(request, "Your project has not been approved yet. You cannot submit a Defense Application.")
            return redirect('home')
        
        # Check for any two pending project phase
        pending_phases_count = project.phases.filter(verdict='pending').count()
        if pending_phases_count >= 2:
            messages.error(request, "There is already a pending Defense Application for your project group. Please wait for a Verdict to be given.")
            return redirect('home')

        # Fetch the last completed phase, if any
        last_completed_phase = project.phases.exclude(verdict='pending').order_by('-date').first()

        # Check if the last completed phase has a verdict of "Not Accepted"
        if last_completed_phase and last_completed_phase.verdict == 'not_accepted':
            messages.error(request, "The Verdict of the recent Defense was Not-Accepted. Please Contact the Coordinator if you think this is a mistake.")
            return redirect('home')

        # Determine the next phase type
        next_phase_type = 'proposal'  # Default phase for new projects
        if last_completed_phase:
            if last_completed_phase.phase_type == 'final' and last_completed_phase.verdict in ['accepted', 'accepted_with_revisions']:
                messages.error(request, "You have already passed the Final Defense. No more defense applications are needed. Congratulations!")
                return redirect('home')
            
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

                # Create the new phase only if there is no pending phase 
                # if not pending_phase:
                ProjectPhase.objects.create(
                    project=project,
                    phase_type=next_phase_type,
                    verdict='pending',
                    date=timezone.now()
                )

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
                    message=f"A new defense application for the project '{project.title}' has been submitted by {request.user.get_full_name()}."
                )
            except User.DoesNotExist:
                logger.error("No current coordinator found to notify.")


                return HttpResponseRedirect('/submit_defense_application?submitted=True')
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
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
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
            "verdict_forms": verdict_forms
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
    
    return render(request, 'project/my_defense_application.html', {
        'application_data': application_data
    })
# def delete_project_group(request, group_id): 
#     if request.user.is_authenticated: 
#         project_group = Project_Group.objects.get(pk=group_id)
#         if request.user == project_group.adviser: 
#             project_group.delete()
#             messages.success(request, "Project Group Deleted Succesfully! ")
#             return redirect('list-project-group')
#         else:
#             messages.success(request, "You Aren't Authorized to Delete this Group!")
#             return redirect('list-project-group')
#     else:
#         messages.success(request, "You Aren't Authorized to do this action")
#         return redirect('list-project-group')
    
# def reject_project_group(request, group_id): 
#     project_group = Project_Group.objects.get(pk=group_id)
#     if request.user == project_group.adviser: 
#         project_group.approved = False
#         project_group.save()
#         messages.success(request, "Project Group has been rejected Succesfully! ")
#         return redirect('adviser-projects')
#     else:
#         messages.success(request, "You Aren't Authorized to do this action")
#         return redirect('adviser-projects')

# def approve_project_group(request, group_id): 
#      # look on projects by ID 
#     project_group = Project_Group.objects.get(pk=group_id)
#     if request.user == project_group.adviser: 
#         project_group.approved = True
#         project_group.save()
#         messages.success(request, "Project Group Accepted Succesfully! ")
#         return redirect('adviser-projects')
#     else:
#         messages.success(request, "You Aren't Authorized to Accept this Proposal!")
#         return redirect('adviser-projects')

def list_project_group(request): 
    if request.user.is_authenticated: 
        # Get all project groups (filtered to those not approved)
        project_groups = Project_Group.objects.filter(approved=True)

        # Prepare project groups with proponents padded to at least 3
        project_groups_with_proponents = []

        for group in project_groups:
            # Convert queryset to a list and pad with None if there are fewer than 3 proponents
            proponents = list(group.proponents.all())
            proponents += [None] * (3 - len(proponents))  # Pad the list to have exactly 3 proponents
            project_groups_with_proponents.append({
                'group': group,
                'proponents': proponents
            })

        # Paginate the project groups
        p = Paginator(project_groups_with_proponents, 6)  # Show 6 project groups per page
        page = request.GET.get('page')
        paginated_groups = p.get_page(page)
        nums = "a" * paginated_groups.paginator.num_pages

        return render(request, 'project/project_group_list.html', {
            'project_groups_with_proponents': paginated_groups,
            'nums': nums
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

            } for group in all_groups
        ]

        return render(request, 'project/my_project_group_waitlist.html', {
            'groups_with_all_members': groups_with_all_members,
           
        })
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
    
def update_deficiencies(request, student_id): 
    if request.user.is_authenticated: 
        return render(request, 'project/update_deficiencies.html', {})
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
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

@login_required
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

@login_required
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



@login_required
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

@login_required
def invite_more_members(request, group_id):
    group = get_object_or_404(Project_Group, id=group_id)
    
    if request.user != group.creator:
        messages.error(request, "Only the group creator can invite more members.")
        return redirect('my-project-group-waitlist')
    
    # Calculate the total number of current, pending, and declined members
    total_members = group.proponents.count() + group.pending_proponents.count() + group.declined_proponents.count()
    
    if total_members > 2:
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
        return redirect('home')

    if request.user.is_authenticated and request.user.eligible == False: 
        messages.error(request, "Only Eligible Students are able to register a Project Group. Please Contact Coordinator to for assistance with Eligibility Concerns")
        return redirect('home')
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
    
    if request.method == "POST":
        form = ProjectGroupForm(request.POST, user=request.user, approved_users=get_user_ids_with_group(request))
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
        'submitted':submitted
    })
    
def my_profile(request, profile_id): 
    if request.user.is_authenticated: 
        
        # look on user objects by ID 
        user = User.objects.get(pk=profile_id)
        
        if user.role == "STUDENT": 
            #profile = Student.objects.get(user_id= profile_id)
            project_group = Project_Group.objects.filter(approved=True).filter(proponents=user)
            # project = ApprovedProject.objects.filter(proponents=project_group)
            return render(request, 'project/my_student_profile.html', 
            {'user': user, 
            'project_group': project_group,
            # 'project': project, 
            #'profile': profile, 
            })
        
        elif user.role =='FACULTY':

            #profile = Faculty.objects.get(user_id=profile_id)     
            projects = ApprovedProject.objects.filter(adviser=user)
            return render(request, 'project/my_faculty_profile.html', 
            {'user': user, 
            'projects': projects,
            # "profile": profile,
            })
        
    else: 
        messages.success(request, "Please Login to view this page")
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
        messages.success(request, "Please Login to view this page")
        return redirect('home')

def show_faculty(request, faculty_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        faculty = Faculty.objects.get(pk=faculty_id)
        # project_group = Project_Group.objects.filter(approved=True).filter(adviser=faculty)
        
        # pass it to the page using render 
        return render(request, 'project/show_faculty.html', 
        {'faculty': faculty}) 
        #  'project_group': project_group}) 
    
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
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


        return render(request, 'project/generate_report.html', 
        { "adviser_count": adviser_count, 
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
        messages.success(request, "Please Login to view this page")
        return redirect('home')


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
            messages.success(request, "You aren't authorized to view this Page ")
            return redirect('home')
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
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
            messages.success(request, "You aren' authorized to view this Page ")
            return redirect('home')
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
       
def coordinator_projects(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
    if request.user.role !='COORDINATOR': 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

   
    # Grab the projects from that adviser
    approved_projects = Project.objects.filter(status='approved').order_by('title')
    
    approved_paginator = Paginator(approved_projects, 5)  # Show 10 projects per page
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
        return redirect('home')
    
    if request.user.role !='FACULTY': 
        messages.error(request, "You are not authorized to view this page")
        return redirect('home')

    adviser = request.user.id
    # Grab the projects from that adviser
    approved_projects = Project.objects.filter(adviser=adviser, status='approved').order_by('title')
    
    approved_paginator = Paginator(approved_projects, 5)  # Show 10 projects per page
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


    return render(request, 'project/adviser_projects.html', {
        "approved_projects_with_groups": approved_projects_with_groups,
        "approved_page_obj": approved_page_obj,
        "approved_nums": approved_nums,
    })


def adviser_proposals(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
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
        return redirect('home')
    
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

        messages.success(request, "Project has been moved to 'Proposals' Succesfully ! ")
        return redirect('adviser-projects')
    else:
        messages.success(request, "You Aren't Authorized to Accept this Proposal!")
        return redirect('adviser-projects')

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
        messages.success(request, "You Aren't Authorized to Accept this Proposal!")
    
    return redirect('adviser-projects')

# Delete Project
def delete_proposal(request, project_id): 
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser:   
        project.delete()
        messages.success(request, "Proposal Deleted Succesfully ! ")
        return redirect('adviser-projects')
    else:
        messages.error(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('adviser-projects')
        
def student_delete_proposal(request, project_id): 
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user in project.proponents.proponents.all:   
        project.delete()
        messages.success(request, "Proposal Deleted Succesfully ! ")
        return redirect('list-proposals')
    else:
        messages.error(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('home')
        
def select_panelist(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
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

def select_panelist_coordinator(request, project_id): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please Login to view this page")
        return redirect('home')
    
    if request.user.role != 'COORDINATOR':
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

def add_comments(request, project_id): 
    if request.user.is_authenticated: 
        # look on projects by ID 
        project = Project.objects.get(pk=project_id)
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
    else: 
        messages.error(request, "You Aren't Authorized to view this page.")
        return redirect('home')

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

    if request.method == 'POST':
        # look on projects by ID 
        project = Project.objects.get(pk=project_id)
        if request.user == project.adviser: 
            project.delete()
            messages.success(request, "Project Deleted Succesfully ! ")
            return JsonResponse({'success': True})
            # return redirect('list-projects')
        else:
            messages.error(request, "You Aren't Authorized to Delete this Project!")
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


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
        messages.success(request, "You Aren't Authorized to view this page.")
        return redirect('home')
    

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
        messages.success(request, "You Aren't Authorized to view this page.")
        return redirect('home')

    
def list_faculty(request): 
    if request.user.is_authenticated: 
        # student_list = Student.objects.all().order_by('last_name')    
        
        p = Paginator(Student.objects.filter(role='FACULTY').order_by('last_name'), 8) 
        page = request.GET.get('page')
        facultys = p.get_page(page)
        nums = "a" * facultys.paginator.num_pages

        return render(request, 'project/faculty.html', 
        {'facultys': facultys, 
        'nums': nums})
    else: 
        messages.success(request, "Please Login to view this page.")
        return redirect('home')

def add_project(request): 
    if request.user.is_authenticated: 
        
        group = get_user_project_group(request)
        if group is None:
            messages.success(request, "You are not a member of any Project Group. Please Register a Project Group First.")
            return redirect('home')
        
        if not group.approved:
            messages.success(request, "Your Project Group is not approved. Please Ensure all Students have approved before proceeding.")
            return redirect('my-project-group-waitlist')
            
        # Check if the group already has an approved project
        approved_project_exists = Project.objects.filter(
            proponents=group,
            status='approved'
        ).exists()

        if approved_project_exists:
            messages.error(request, "Your group already has an approved project. You cannot submit another project.")
            return redirect('list-projects')
        
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
                            message=f"A new project '{project.title}' has been submitted by {request.user.get_full_name()}.", 
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
                                    message=f"A new project '{project.title}' has been submitted by {request.user.get_full_name()}.",
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
        return redirect('home')

def home(request):
    return render(request, "project/home.html", {})

def all_projects(request):
    if request.user.is_authenticated: 
        # Create a Paginator object with the project list and specify the number of items per page
        p = Paginator(Project.objects.filter(status='approved').order_by('title'), 5) 
        page = request.GET.get('page')
        projects = p.get_page(page)
        nums = "a" * projects.paginator.num_pages

        return render(request, 'project/project_list.html', 
        {'projects': projects, 
        'nums': nums})
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
        
def all_proposals(request):
    if request.user.is_authenticated:

        group = get_user_project_group(request)
        # Filter projects where the logged-in user is a proponent
        project_list = Project.objects.filter(
            (Q(status='pending') | Q(status='declined')) & 
            Q(proponents=group)  # Assuming 'proponents' is the field name
        ).order_by('title')

        
        # Create a Paginator object with the project list and specify the number of items per page
        p = Paginator(project_list, 5)  # Show 5 proposals per page
        page = request.GET.get('page')
        projects = p.get_page(page)
        nums = "a" * projects.paginator.num_pages

        return render(request, 'project/proposal_list.html', {
            'projects': projects,
            'nums': nums
        })
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')

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
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
def show_project_idea(request, project_idea_id): 
    if request.user.is_authenticated: 
        # look on faculty by ID 
        project_idea = Project_Idea.objects.get(pk=project_idea_id)
        # project_owner = User.objects.get(pk=project.owner)
        
        # pass it to the page using render
        return render(request, 'project/show_project_idea.html', 
        {'project_idea': project_idea})
    
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
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
        messages.success(request, "Please Login to view this page")
        return redirect('home')
        
