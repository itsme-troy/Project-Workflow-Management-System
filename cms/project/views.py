from django.shortcuts import render, redirect
from .models import Project
from django.http import HttpResponseRedirect
from django.contrib import messages 
from django.conf import settings 
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import ProjectForm, CapstoneSubmissionForm, UpdateProjectForm, ProjectGroupForm
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
from django.db.models import Subquery, OuterRef, Max

logger = logging.getLogger(__name__)

# Import user model 
from django.contrib.auth import get_user_model 
User = get_user_model()

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

        if not project.approved:  # Assuming 'approved' is a BooleanField
            messages.error(request, "Your project has not been approved yet. You cannot submit a Defense Application.")
            return redirect('home')
        
        # Fetch the last completed phase, if any
        last_phase = project.phases.order_by('-date').first()

         # Determine the next phase type
        next_phase_type = 'Proposal Defense'  # Default phase for new projects
       
        if last_phase:
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
                        phase_type = 'final defense'
                
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

        return render(request, 'project/project_group_list.html', {
            'project_groups_with_proponents': project_groups_with_proponents
        })
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
def list_project_group_waitlist(request):
    if request.user.is_authenticated: 
        # Get all project groups (filtered to those not approved)
        project_groups = Project_Group.objects.filter(approved=False)

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

        return render(request, 'project/project_group_waitlist.html', {
            'project_groups_with_proponents': project_groups_with_proponents
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

def add_project_group(request): 
    if request.user.is_authenticated: 

        if request.user.role=='STUDENT': 
            # Check if the logged-in user is already in an approved project group
            approved_groups = Project_Group.objects.filter(proponents=request.user, approved=True)
            
            if approved_groups.exists():
                # If the user is already part of an approved group, show an error message
                messages.error(request, "You are already part of an approved project group and cannot create a new one.")
                return redirect('home')

            submitted = False  # variable to determine whether a user submitted a form or just viewing the page 
            
            # a student must belong to only one project group 
            
            if request.method == "POST":
                form = ProjectGroupForm(request.POST, user=request.user, approved_users=get_user_ids_with_group(request))
                if form.is_valid(): # check if form is valid 
                    # we're gonna save it but don't save it just yet
                    project = form.save(commit=False)
                    project.owner = request.user.id # logged in user
                    project.save()
                    form.save() # save it to the database
                    return HttpResponseRedirect('/add_project_group?submitted=True') # return to add_project with variable
                
            else: # if they did not fill out the form, then
                form = ProjectGroupForm(user=request.user, approved_users=get_user_ids_with_group(request)) # define the form
                if 'submitted' in request.GET:
                    submitted = True

            return render(request, 'project/add_project_group.html', {
             'form':form, 
             'submitted':submitted }) # pass the form 
        else: 
            messages.success(request, "Only Students Are allowed to perform this Action")
            return redirect('home')
    else:
        messages.success(request, "Please Login to view this page")
        return redirect('home')
    
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
        project_group = Project_Group.objects.filter(approved=True).filter(adviser=faculty)
        
        # pass it to the page using render 
        return render(request, 'project/show_faculty.html', 
        {'faculty': faculty, 
         'project_group': project_group}) 
    
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


# def get_user_project(request):
#     if not request.user.is_authenticated:
#        return None

#      # Assuming 'Student' model has a OneToOne relation with User
#     try:
#         student = Student.objects.get(id=request.user.id)

#     except Student.DoesNotExist:
#         return None
    
#     # Get the project group that the student is part of
#     group = get_user_project_group(request)
#     # Get the project that the student is part of
#     project = ApprovedProject.objects.filter(proponents=group)
    
#     if project.exists():
#         # Return the first group or handle accordingly
#         return project.first() 
    
#     else: 
#         return None


    
def coordinator_approval(request): 
    if request.user.is_authenticated: 
        # Get counts 
        project_count = Project.objects.filter(approved=True).count
        proposal_count = Project.objects.filter(approved=False).count
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
                
                student_box_list = request.POST.getlist('student_box')
                student_list.update(eligible=False)
                for z in student_box_list:
                    User.objects.filter(pk=int(z)).update(eligible=True)


                messages.success(request, "Coordinator Approval Page has been updated")
                return redirect('coordinator_approval')
            else: 
                return render(request, 
                'project/coordinator_approval.html', 
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
        
       
# Show projects handled by an adviser 
def adviser_projects(request):
    if request.user.is_authenticated: 

        project_groups = Project_Group.objects.all
    
        # Grab the adviser ID 
        adviser = request.user.id
        # Grab the projects from that adviser 
        projects = Project.objects.filter(adviser=adviser)

        if projects:  
            return render(request, 'project/adviser_projects.html', {
            "projects": projects, 
            'project_groups': project_groups
            })
        else: 
            messages.success(request, "This Adviser Has No Advisory Projects at  this time.")
            return redirect('list-projects')
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')

def reject_project(request, project_id):
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser: 
        project.approved = False
        project.save()
        messages.success(request, "Project has been moved to 'Proposals' Succesfully ! ")
        return redirect('list-projects')
    else:
        messages.success(request, "You Aren't Authorized to Accept this Proposal!")
        return redirect('list-projects')

# Accept Project
def accept_proposal(request, project_id): 
     # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser: 
        project.approved = True
        project.save()
        messages.success(request, "Proposal Accepted Succesfully ! ")
        return redirect('list-proposals')
    else:
        messages.success(request, "You Aren't Authorized to Accept this Proposal!")
        return redirect('list-proposals')


# Delete Project
def delete_proposal(request, project_id): 
    # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    if request.user == project.adviser:   
        project.delete()
        messages.success(request, "Proposal Deleted Succesfully ! ")
        return redirect('list-proposals')
    else:
        messages.error(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('list-proposals')
        
def update_proposal(request, project_id): 
     # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    # if they are gonna post, use this form otherwise, don't use anything. 
    form = UpdateProjectForm(request.POST or None, instance=project)
    
    # save data to the database and return somewhere 
    if form.is_valid(): 
        form.save()
        messages.success(request, "Proposal updated Succesfully!")
        return redirect('list-proposals')
    # pass it to the page using render 
    return render(request, 'project/update_proposal.html', 
    {'project': project, 
     'form': form})

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

def update_project(request, project_id): 
    if request.user.is_authenticated: 
        # look on projects by ID 
        project = Project.objects.get(pk=project_id)
        # if they are gonna post, use this form otherwise, don't use anything. 
        if request.user == project.adviser: 
            form = UpdateProjectForm(request.POST or None, instance=project)
        else: 
            form = ProjectForm(request.POST or None, instance=project)
        
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
            return redirect('list-projects')
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
        student_list = Student.objects.all().order_by('last_name')    
        return render(request, 'project/student.html', 
        {'student_list': student_list})
    else: 
        messages.success(request, "You Aren't Authorized to view this page.")
        return redirect('home')

def list_faculty(request): 
    if request.user.is_authenticated: 
        faculty_list = User.objects.all().order_by('last_name')
        return render(request, 'project/faculty.html', 
        {'faculty_list': faculty_list})
    
    else: 
        messages.success(request, "You Aren't Authorized to view this page.")
        return redirect('home')

def add_project(request): 
    if request.user.is_authenticated: 
        group = get_user_project_group(request)
        if group is None:
            messages.success(request, "You are not a member of any Project Group. Please Register a Project Group First.")
            return redirect('home')
            
        if request.user.role == 'STUDENT': 
            submitted = False  # Variable to determine whether a user submitted a form or just viewing the page 
            if request.method == "POST":
                form = ProjectForm(request.POST, user=request.user)
                if form.is_valid():  # Check if form is valid 
                    
                    # We're gonna save it but don't save it just yet
                    project = form.save(commit=False)
                    project.owner = request.user.id  # Set the logged-in user as the owner
                    
                    # Set the project group from the fetched group
                    project.project_group = group
                    
                    # Assign the adviser directly as an instance
                    # if group.adviser:
                    #     project.adviser = group.adviser  # Use the Approved_Adviser instance
                    # else:
                    #     form.add_error('adviser', 'No adviser assigned to this group.')
                    #     return render(request, 'project/add_project.html', {
                    #         'group': group,
                    #         'form': form,
                    #         'submitted': submitted
                    #     })
                    
                    project.save()  # Save the project to the database
                    
                    # Now save the panelists
                    form.save_m2m()  # This saves the ManyToMany relationships (panel field)

                    return HttpResponseRedirect('/add_project?submitted=True')  # Return to add_project with variable
            
            else:  # If they did not fill out the form, then
                form = ProjectForm(initial={
                    # 'adviser': group.adviser.id if group.adviser else None, 
                    'proponents': group,
                }, user=request.user)  # Define the form
                
                if 'submitted' in request.GET:
                    submitted = True

            return render(request, 'project/add_project.html', {
                'group': group,
                'form': form, 
                'submitted': submitted
            })  # Pass the form 
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
        project_list = Project.objects.all().order_by('title')

        return render(request, 'project/project_list.html', 
        {'project_list': project_list,})
    else: 
        messages.success(request, "Please Login to view this page")
        return redirect('home')
        


def all_proposals(request):
    if request.user.is_authenticated: 
        project_list = Project.objects.all().order_by('title')
        return render(request, 'project/proposal_list.html', 
        {'project_list': project_list})
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
        
