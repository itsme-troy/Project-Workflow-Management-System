from django.shortcuts import render, redirect
from .models import Project
from django.http import HttpResponseRedirect
from django.contrib import messages 
from django.conf import settings 
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import ProjectForm, CapstoneSubmissionForm, UpdateProjectForm, ProjectGroupForm
from .models import AppUserManager, Defense_Application
from .models import Student, Faculty, Project_Group
from .models import StudentProfile, FacultyProfile
# from .models import Event
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse 

# Import user model 
from django.contrib.auth import get_user_model 
User = get_user_model()

def list_defense_applications(request): 
    defense_applications = Defense_Application.objects.all
    return render(request, 'project/defense_application_list.html', {
    "defense_applications": defense_applications 
    })
def delete_project_group(request, group_id): 
    project_group = Project_Group.objects.get(pk=group_id)
    if request.user == project_group.adviser: 
        project_group.delete()
        messages.success(request, "Project Group Deleted Succesfully! ")
        return redirect('list-project-group')
    else:
        messages.success(request, "You Aren't Authorized to Delete this Group!")
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
        # look on faculty by ID 
    project_groups = Project_Group.objects.all

    return render(request, 'project/project_group_list.html', {
        'project_groups':project_groups
    })

def update_deficiencies(request, student_id): 
    return render(request, 'project/update_deficiencies.html', {})

def add_project_group(request): 
    submitted = False  # variable to determine whether a user submitted a form or just viewing the page 
    
    # a student must belong to only one project group 
    
    if request.method == "POST":
        form = ProjectGroupForm(request.POST)
        if form.is_valid(): # check if form is valid 
            # we're gonna save it but don't save it just yet
            project = form.save(commit=False)
            project.owner = request.user.id # logged in user
            project.save()
            form.save() # save it to the database
            return HttpResponseRedirect('/add_project_group?submitted=True') # return to add_project with variable
    
    else: # if they did not fill out the form, then
        form = ProjectGroupForm # define the form
        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'project/add_project_group.html', 
    {'form':form, 'submitted':submitted}) # pass the form 
  

def my_profile(request, profile_id): 
    if request.user.is_authenticated: 
        
        # look on user objects by ID 
        user = User.objects.get(pk=profile_id)
        
        if user.role == "STUDENT": 
            profile = StudentProfile.objects.get(user_id= profile_id)
            project_group = Project_Group.objects.filter(approved=True).filter(proponents=user)
            return render(request, 'project/my_student_profile.html', 
            {'user': user, 
            'project_group': project_group,
            'profile': profile, 
            })
        
        elif user.role =='FACULTY':

            #profile = Faculty.objects.get(user_id=profile_id)     
            project_group = Project_Group.objects.filter(approved=True).filter(adviser=user)
            return render(request, 'project/my_faculty_profile.html', 
            {'user': user, 
            'project_group': project_group,
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
    
# def profile_list(request): 
#     if request.user.is_authenticated: 
#         profiles = User.objects.exclude(user=request.user)
#         return render(request, 'projects/profile_list.html', {"profiles":profiles})
#     else: 
#         messages.success(request, ("You must be Logged In to view this page"))
#         return redirect('home')

# def profile(request, pk): 
#     if request.user.is_authenticated: 
#         profile = Profile.objects.get(user_id=pk)
#         return render(request, "projects/profile.html", {"profile":profile})
#     else: 
#         messages.success(request, ("You must be Logged In to view this page"))
#         return redirect('home')


@login_required
def generate_report(request):
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


def submit_defense_application(request): 
    submitted = False
    if request.method == 'POST': 
        form = CapstoneSubmissionForm(request.POST, request.FILES)
        if form.is_valid(): # check if form is valid 
            application = form.save(commit=False)
            application.owner = request.user.id # Assuming a one-to-one relationship
            application.save()

            form.save()
            # messages.success(request, "Defense Application submitted Succesfully!")
            return HttpResponseRedirect('/submit_defense_application?submitted=True') # return to add_project with variable
    else: # if they did not fill out the form, then
        form = CapstoneSubmissionForm()  # define the form
        if 'submitted' in request.GET: 
            submitted = True

    return render(request, 'project/submit_defense_application.html', 
    {'form':form, 'submitted': submitted}) # pass the form 


def coordinator_approval(request): 
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
       
# Show projects handled by an adviser 
def adviser_projects(request):

    project_groups = Project_Group.objects.all

    if request.user.is_authenticated: 
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
        messages.success(request, "You Aren't Authorized to view this page.")
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
        messages.success(request, "You Aren't Authorized to Delete this Proposal!")
        return redirect('list-proposals')
    
def update_proposal(request, project_id): 
     # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    # if they are gonna post, use this form otherwise, don't use anything. 
    form = ProjectForm(request.POST or None, instance=project)
    
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
     # look on projects by ID 
    project = Project.objects.get(pk=project_id)
    # if they are gonna post, use this form otherwise, don't use anything. 
    if request.user == project.adviser: 
        form = UpdateProjectForm(request.POST or None, instance=project)
    else: 
        form = ProjectForm(request.POST or None, instance=project)
    
    # save data to the database and return somewhere 
    if form.is_valid(): 
        form.save()
        messages.success(request, "Project Updated Succesfully! ")
        return redirect('list-projects')
    # pass it to the page using render 
    return render(request, 'project/update_project.html', 
    {'project': project, 
     'form': form})

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
    student_list = Student.objects.all().order_by('last_name')    
    return render(request, 'project/student.html', 
    {'student_list': student_list})


def list_faculty(request): 
    faculty_list = User.objects.all().order_by('last_name')
    return render(request, 'project/faculty.html', 
    {'faculty_list': faculty_list})

def add_project(request): 
    
    if request.user.role == 'STUDENT': 
        submitted = False # variable to determine whether a user submitted a form or just viewing the page 
        if request.method == "POST":
            form = ProjectForm(request.POST)
            if form.is_valid(): # check if form is valid 
                # we're gonna save it but don't save it just yet
                project = form.save(commit=False)
                project.owner = request.user.id # logged in user
                project.save()

                form.save() # save it to the database
                return HttpResponseRedirect('/add_project?submitted=True') # return to add_project with variable
        
        else: # if they did not fill out the form, then
            form = ProjectForm # define the form
            if 'submitted' in request.GET:
                submitted = True

        return render(request, 'project/add_project.html', 
        {'form':form, 'submitted':submitted}) # pass the form 
    else: 
        messages.success(request, "Only Students are allowed to propose Projects. ")
        return redirect('home')

def home(request):
    return render(request, "project/home.html", {})

def all_projects(request):
    project_list = Project.objects.all().order_by('title')

    return render(request, 'project/project_list.html', 
    {'project_list': project_list,})

def all_proposals(request):
    project_list = Project.objects.all().order_by('title')
    return render(request, 'project/proposal_list.html', 
    {'project_list': project_list})

def show_project(request, project_id): 
    # look on faculty by ID 
    project = Project.objects.get(pk=project_id)
    project_owner = User.objects.get(pk=project.owner)
    
    # pass it to the page using render
    return render(request, 'project/show_project.html', 
    {'project': project, 
    'project_owner': project_owner})
    
def show_proposal(request, project_id): 
    # look on faculty by ID 
    project = Project.objects.get(pk=project_id)
    project_owner = User.objects.get(pk=project.owner)
    
    # pass it to the page using render
    return render(request, 'project/show_proposal.html', 
    {'project': project, 
    'project_owner': project_owner})
