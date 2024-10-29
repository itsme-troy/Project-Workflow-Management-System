from django.contrib import admin
from django.contrib.auth.models import Group
from django.conf import settings 
User = settings.AUTH_USER_MODEL

# unregister group 
admin.site.unregister(Group)

from .models import AppUser, Project, Project_Group #, Profile
from .models import Defense_Application
from .models import Student, Faculty, Coordinator 
from .models import StudentProfile, FacultyProfile, ProjectPhase
from .models import ApprovedProject, ApprovedProjectGroup
from .models import Approved_Adviser, Approved_panel, Approved_student
#admin.site.register(Project_Group)
admin.site.register(AppUser)
admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(Coordinator)
#admin.site.register(StudentProfile)
admin.site.register(ApprovedProject)
admin.site.register(Approved_student)
# admin.site.register(ApprovedProjectGroup)
admin.site.register(Approved_Adviser)
# admin.site.register(ProjectPhase)
# admin.site.register(Approved_panel)
#  Mix Profile info into user info

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile


class StudentAdmin(admin.ModelAdmin): 
    model = Student
    fields = ["first_name", "last_name", "email", "profile_image"]
  
    inlines = [StudentProfileInline]

# Unregister initial User
admin.site.unregister(Student)
# Reregister User 
admin.site.register(Student, StudentAdmin)

#  Mix Profile info into user info
class FacultyProfileInline(admin.StackedInline):
    model = FacultyProfile

class FacultyAdmin(admin.ModelAdmin): 
    model = Faculty
    fields = ["first_name", "last_name", "profile_image"]
    inlines = [FacultyProfileInline]
    
# Unregister initial User
admin.site.unregister(Faculty)
# Reregister User 
admin.site.register(Faculty, FacultyAdmin)

@admin.register(Project) #  'project_type',
class ProjectAdmin(admin.ModelAdmin): #project_type'
    fields = ('title', 'adviser','description','proponents', 'panel', 'owner', 'approved')
    list_display = ('title', 'adviser', 'description')
    ordering = ('title', )
    search_fields = ('title', 'description', 'adviser')
    list_filter = ('adviser', )

@admin.register(ProjectPhase)
class ProjectPhaseAdmin(admin.ModelAdmin):
    model = ProjectPhase
    fields = ["project", "phase_type", "verdict", "date"]
    list_display = ["project", "phase_type", "verdict", "date"]
    ordering = ("project",)
    readonly_fields = ['date',]

@admin.register(Project_Group)
class Project_GroupAdmin(admin.ModelAdmin):
    fields = ('owner', 'approved', 'proponents')
    list_display = ( 'approved', 'owner')

@admin.register(Defense_Application)
class Defense_ApplicationAdmin(admin.ModelAdmin): 
    fields = ('project', 'project_group', 'adviser', 'title', 'abstract', 'panel', 'document', 'owner', 'submission_date')
    list_display = ('title', 'project', 'project_group', 'adviser' ,'submission_date')
    readonly_fields = ['submission_date', ]



