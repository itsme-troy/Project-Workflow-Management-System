from django.shortcuts import render, redirect
from .models import Project
from django.http import HttpResponseRedirect
from django.contrib import messages 
from django.conf import settings 
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import ProjectForm, CapstoneSubmissionForm, UpdateProjectForm, ProjectGroupForm, ProjectGroupInviteForm
from .forms import  VerdictForm
from .models import AppUserManager, Defense_Application
from .models import Student, Faculty, ApprovedProjectGroup,  Project_Group
from .models import StudentProfile, FacultyProfile, Student
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

logger = logging.getLogger(__name__)

# Import user model 
from django.contrib.auth import get_user_model 
User = get_user_model()


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
        else:
            messages.error(request, "Selected user is not an approved member of the group.")

        return redirect('my-project-group-waitlist')

    return render(request, 'project/transfer_creator.html', {
        'group': group,
        'approved_members': group.proponents.exclude(id=request.user.id)
    })

@login_required
def accept_join_request(request, group_id, user_id):
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
    else:
        messages.error(request, "This user has not requested to join the group.")

    return redirect('my-project-group-waitlist')

def join_group_list(request):
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
        # user_project = get_user_project(request)
        user_group = get_user_project_group(request)
        
        if user_group is None:
            messages.warning(request, "You are not a member of any Project Group. Please Register a Project Group First.")
            return redirect('home')
            
         # Fetch the approved project for the group
        project = ApprovedProject.objects.filter(proponents=user_group).first()

        if project is None:
            messages.error(request, "No project found for your group. Please submit a project first.")
            return redirect('home')

        if project.status=='False':  # Assuming 'approved' is a BooleanField
            messages.error(request, "Your project has not been approved yet. You cannot submit a Defense Application.")
            return redirect('home')
        
        # Fetch the last completed phase, if any
        last_phase = project.phases.order_by('-date').first()

         # Determine the next phase type
        next_phase_type = 'Proposal Defense'  # Default phase for new projects
       
        if last_phase:
            if last_phase.phase_type == 'final' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                messages.error(request, "You have already passed the Final Defense. No more defense applications are needed. Congratulations!")
                return redirect('home')
            
            if last_phase.verdict == 'redefense':
                next_phase_type = last_phase.phase_type  # Repeat the same phase type
            elif last_phase.phase_type == 'proposal':
                if last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                    next_phase_type = 'Design Defense'
            elif last_phase.phase_type == 'design':
                if last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                    next_phase_type = 'Preliminary Defense'
            elif last_phase.phase_type == 'preliminary':
                if last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                    next_phase_type = 'Final Defense'
        
        submitted = False
        if request.method == 'POST': 
            form = CapstoneSubmissionForm(request.POST, request.FILES)
            if form.is_valid(): # check if form is valid 
                application = form.save(commit=False)
                application.owner = request.user.id # Assuming a one-to-one relationship
                
                # set Set the project group and adviser from the fetched group
                application.proponents = project.proponents
                application.project = project
                application.title = next_phase_type # Set title based on phase logic

            # Assign the adviser directly as an instance
                if  project.adviser:
                    application.adviser = project.adviser  # Use the Approved_Adviser instance
                else:
                    form.add_error('adviser', 'No adviser assigned to this group.')
                    return render(request, 'project/add_project.html', {
                        'project': project,
                        'group': user_group, 
                        'form': form,
                        'submitted': submitted
                    })
                
                # Save the application object first, since you cannot set the ManyToMany field before saving
                application.save()

                # Set the panel members from the project
                panel_members = project.panel.all()  # This should be a queryset of Approved_panel instances
     
                if not panel_members:
                    messages.error(request, "No panel members found for this project.")
                    return render(request, 'project/submit_defense_application.html', {
                        'project': project,
                        'group': user_group,
                        'form': form,
                        'submitted': submitted
                    })

                # Set the panel members using their IDs
                application.panel.set(panel_members.values_list('id', flat=True))
                
                form.save_m2m()# Save the many-to-many relationships

                 # Now create the new phase for the project
                phase_type = None
                
                if not last_phase:
                    phase_type = 'proposal'
                else:
                    if last_phase.verdict == 'redefense':
                        phase_type = last_phase.phase_type  # Repeat the same phase type
                    elif last_phase.phase_type == 'proposal' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                        phase_type = 'design'
                    elif last_phase.phase_type == 'design' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                        phase_type = 'preliminary'
                    elif last_phase.phase_type == 'preliminary' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
                        phase_type = 'final'
                
                # Create the new phase if phase_type is valid
                if phase_type:
                    ProjectPhase.objects.create(
                        project=project,
                        phase_type=phase_type,
                        verdict='pending',
                        date=timezone.now()
                    )
                else:
                    logger.error("Invalid phase type determined. No phase created.")

                # messages.success(request, "Defense Application submitted Succesfully!")
                return HttpResponseRedirect('/submit_defense_application?submitted=True') # return to add_project with variable
        else: # if they did not fill out the form, then (GET)
                form = CapstoneSubmissionForm(initial={
                    'adviser' : project.adviser.id if project.adviser else None, 
                    'project_group' : user_group, 
                    'project': project, 
                    'panel': project.panel.all(), # Set the panel field with the panel members
                    'title': next_phase_type,   # Dynamically set the title based on the phase logic

            },)  # define the form
                if 'submitted' in request.GET: 
                    submitted = True

        return render(request, 'project/submit_defense_application.html',{
            'last_phase': last_phase, 
            'next_phase_type': next_phase_type, 
            'project': project, 
            'group': user_group,
            'form':form, 
            'submitted': submitted}) # pass the form 
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

def delete_project_group(request, group_id): 
    if request.user.is_authenticated: 
        project_group = Project_Group.objects.get(pk=group_id)
        if request.user == project_group.adviser: 
            project_group.delete()
            messages.success(request, "Project Group Deleted Succesfully! ")
            return redirect('list-project-group')
        else:
            messages.success(request, "You Aren't Authorized to Delete this Group!")
            return redirect('list-project-group')
    else:
        messages.success(request, "You Aren't Authorized to do this action")
        return redirect('list-project-group')
    
def reject_project_group(request, group_id): 
    project_group = Project_Group.objects.get(pk=group_id)
    if request.user == project_group.adviser: 
        project_group.approved = False
        project_group.save()
        messages.success(request, "Project Group has been rejected Succesfully! ")
        return redirect('adviser-projects')
    else:
        messages.success(request, "You Aren't Authorized to do this action")
        return redirect('adviser-projects')

def approve_project_group(request, group_id): 
     # look on projects by ID 
    project_group = Project_Group.objects.get(pk=group_id)
    if request.user == project_group.adviser: 
        project_group.approved = True
        project_group.save()
        messages.success(request, "Project Group Accepted Succesfully! ")
        return redirect('adviser-projects')
    else:
        messages.success(request, "You Aren't Authorized to Accept this Proposal!")
        return redirect('adviser-projects')

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
                    notification_type='group_decline',
                    group=other_group,
                    sender=request.user,
                    message=f"{request.user.get_full_name()} has declined the invitation to join your project group."
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
                        notification_type='group_complete',
                        group=group,
                        sender=request.user,
                        message=f"Your project group '{group.name}' has been automatically approved with 3 members."
                    )
                except Exception as e:
                    logger.error(f"Failed to create notification for {member}: {str(e)}")
            
            messages.success(request, "You have joined the group and it has been automatically approved with 3 members.")
        elif approved_students_count < 3:
            # Create notification just for the group creator about the acceptance
            try:
                Notification.objects.create(
                    recipient=group.creator,
                    notification_type='group_accept',
                    group=group,
                    sender=request.user,
                    message=f"{request.user.get_full_name()} has accepted the invitation to join your project group. ({approved_students_count}/3 members)"
                )
            except Exception as e:
                logger.error(f"Failed to create notification: {str(e)}")
            
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
                        notification_type='invitation',
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
                                notification_type='invitation',
                                group=group,
                                sender=request.user,
                                message=f"{request.user.get_full_name()} has invited you to join the project group '{group.name}'"
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

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    unread_count = notifications.filter(is_read=False).count()
     # Debugging logs
    logger.debug(f"Fetching notifications for user: {request.user}")
    logger.debug(f"Notifications count: {notifications.count()}")
    logger.debug(f"Unread notifications count: {unread_count}")
    
    notifications_data = [{
        'id': notif.id,
        'message': notif.message,
        'is_read': notif.is_read,
        'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notif in notifications]
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
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
    
def add_project_group(request): 
    if not request.user.is_authenticated or request.user.role != 'STUDENT':
        messages.error(request, "Please login as a student to perform this action")
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
                        notification_type='invitation',
                        group=project,
                        sender=student_creator,
                        message=f"{student_creator.get_full_name()} has invited you to join a project group."
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
        projects = Project.objects.all()

        student_uneligible_count = Student.objects.filter(role='STUDENT').filter(eligible=False ).count
        adviser_uneligible_count = Faculty.objects.filter(role='FACULTY').filter(adviser_eligible=False).count
        panel_uneligible_count = Faculty.objects.filter(role='FACULTY').filter(panel_eligible=False).count
        
        project_group_count = Project_Group.objects.count
        unapproved_project_group_count = Project_Group.objects.filter(approved=False).count


           # Get all projects with their phases
        projects = Project.objects.prefetch_related('phases').all()

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
        student_list = User.objects.filter(role='STUDENT').order_by('last_name')
        
        # get list of faculty 
        faculty_list = User.objects.filter(role='FACULTY').order_by('last_name')
        if request.user.is_superuser:
            if request.method == "POST":  
                id_list = request.POST.getlist('boxes')

                # Unchecked all users 
                faculty_list.update(adviser_eligible=False)
        
                # update the database
                for x in id_list: 
                    User.objects.filter(pk=int(x)).update(adviser_eligible=True)
                
                panel_id_list = request.POST.getlist('box')
                
                # Unchecked all users 
                faculty_list.update(panel_eligible=False)
                
                # update the database
                for y in panel_id_list: 
                    User.objects.filter(pk=int(y)).update(panel_eligible=True)
                

                messages.success(request, "Faculty Approval Form has been updated")
                return redirect('coordinator-approval-faculty')
            else: 
                return render(request, 
                'project/coordinator_approval_faculty.html', 
                {'faculty_list': faculty_list, 
                    "project_count": project_count,
                    "proposal_count": proposal_count,
                    "student_count": student_count, 
                    "faculty_count": faculty_count,
                    "student_list": student_list, 
                })    
        else: 
            messages.success(request, "You aren' authorized to view this Page ")
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
        if request.user.is_superuser:
            if request.method == "POST":  
            
                student_box_list = request.POST.getlist('student_box')
                student_list.update(eligible=False)
                for z in student_box_list:
                    User.objects.filter(pk=int(z)).update(eligible=True)

                messages.success(request, "Student Approval Form has been updated")
                return redirect('coordinator-approval-student')
            else: 
                return render(request, 
                'project/coordinator_approval_student.html', 
                {'faculty_list': faculty_list, 
                    "project_count": project_count,
                    "proposal_count": proposal_count,
                    "student_count": student_count, 
                    "faculty_count": faculty_count,
                    "student_list": student_list, 
                })    
        else: 
            messages.success(request, "You aren' authorized to view this Page ")
            return redirect('home')
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
        
       
def adviser_projects(request):
    if request.user.is_authenticated: 
        adviser = request.user.id
        # Grab the projects from that adviser
        approved_projects = Project.objects.filter(adviser=adviser, status='approved')
        
        # Prepare data for each project with its groups and proponents
        approved_projects_with_groups = []

        for project in approved_projects:
            project_group = Project_Group.objects.filter(project=project, approved=True).first()
            if project_group:
                proponents = list(project_group.proponents.all())
                proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
                approved_projects_with_groups.append({
                    'project': project,
                    'group': project_group,
                    'proponents': proponents, 
                    'status': project.status
                })

        not_approved_projects = Project.objects.filter(
            adviser=adviser,
            status__in=['pending', 'declined']
        )
        not_approved_projects_with_groups = []
        
        for project in not_approved_projects:
            project_group = Project_Group.objects.filter(project=project, approved=True).first()
            print("Project Group for Project:", project, "is", project_group)  # Debug statement
            if project_group:
                proponents = list(project_group.proponents.all())
                proponents += [None] * (3 - len(proponents))  # Pad to exactly 3 proponents
                not_approved_projects_with_groups.append({
                    'project': project,
                    'group': project_group,
                    'proponents': proponents,
                    'status': project.status
                })

        return render(request, 'project/adviser_projects.html', {
            "approved_projects_with_groups": approved_projects_with_groups,
            "not_approved_projects_with_groups": not_approved_projects_with_groups
        })
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    

    
def reject_project(request, project_id):
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser: 
        project.status = 'declined'
        project.save()
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
        
def update_proposal(request, project_id): 
    if request.user.is_authenticated: 
        # look on projects by ID 
        project = Project.objects.get(pk=project_id)
        # if they are gonna post, use this form otherwise, don't use anything. 
        if request.user == project.adviser: 
            form = UpdateProjectForm(request.POST or None, instance=project)
        
        # save data to the database and return somewhere 
        if form.is_valid(): 
            # Handle disabled fields by reassigning their initial values before saving
            if isinstance(form, UpdateProjectForm):  # Check if using UpdateProjectForm
                form.instance.title = project.title
                form.instance.project_type = project.project_type
                form.instance.proponents = project.proponents
                form.instance.adviser = project.adviser
                form.instance.description = project.description
            form.save()
            messages.success(request, "Proposal updated Succesfully!")
            return redirect('adviser-projects')
        else:
            # Reinitialize the panel with the pre-selected panelist to retain form state
            form.fields['panel'].initial = form.instance.panel.all()[:1]

        # pass it to the page using render 
        return render(request, 'project/update_proposal.html', 
        {'project': project, 
        'form': form})
    else: 
        messages.error(request, "You Aren't Authorized to view this page.")
        return redirect('home')


def update_project(request, project_id): 
    if request.user.is_authenticated: 
        # look on projects by ID 
        project = Project.objects.get(pk=project_id)
        # if they are gonna post, use this form otherwise, don't use anything. 
        if request.user == project.adviser: 
            form = UpdateProjectForm(request.POST or None, instance=project)
       
        # save data to the database and return somewhere 
        if form.is_valid(): 
             # Handle disabled fields by reassigning their initial values before saving
            if isinstance(form, UpdateProjectForm):  # Check if using UpdateProjectForm
                form.instance.title = project.title
                form.instance.project_type = project.project_type
                form.instance.proponents = project.proponents
                form.instance.adviser = project.adviser
                form.instance.description = project.description
                
            form.save()
            messages.success(request, "Project Updated Succesfully! ")
            return redirect('adviser-projects')
        else:
            # Add error messages from the form validation
            # for field, errors in form.errors.items():
            #     for error in errors:
            #         messages.error(request, f"{field}: {error}")
            
             # Reinitialize the panel with the pre-selected panelist to retain form state
            form.fields['panel'].initial = form.instance.panel.all()[:1]

        # pass it to the page using render 
        return render(request, 'project/update_project.html', 
        {'project': project, 'form': form})
    else: 
        messages.error(request, "You Aren't Authorized to view this page.")
        return redirect('home')
    
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
        # student_list = Student.objects.all().order_by('last_name')    
        
        p = Paginator(Student.objects.filter(role='STUDENT').filter(eligible=True).order_by('last_name'), 6) 
        page = request.GET.get('page')
        students = p.get_page(page)
        nums = "a" * students.paginator.num_pages

        return render(request, 'project/student.html', 
        # {'student_list': student_list,
        {'students': students, 
        'nums': nums})
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
        
        p = Paginator(Student.objects.filter(role='FACULTY').order_by('last_name'), 6) 
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
            return redirect('home')
            
        if request.user.role == 'STUDENT': 
            submitted = False
            if request.method == "POST":
                form = ProjectForm(request.POST, user=request.user)
                if form.is_valid():
                    project = form.save(commit=False)
                    project.owner = request.user.id
                    project.project_group = group
                    project.save()
                    form.save_m2m()
                    return HttpResponseRedirect('/add_project?submitted=True')
                else:
                    # Add a general error message
                    messages.error(request, "Please correct the errors below.")
            
            else:
                form = ProjectForm(initial={
                    'proponents': group,
                }, user=request.user)
                
                if 'submitted' in request.GET:
                    submitted = True

            return render(request, 'project/add_project.html', {
                'group': group,
                'form': form, 
                'submitted': submitted
            })
        else: 
            messages.success(request, "Only Students are allowed to propose Projects.")
            return redirect('home')
    else: 
        messages.success(request, "Please Login to view this page")
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
        
