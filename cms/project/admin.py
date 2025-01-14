from django.contrib import admin
from django.contrib.auth.models import Group
from django.conf import settings 
User = settings.AUTH_USER_MODEL

# unregister group 
admin.site.unregister(Group)

from .models import AppUser, Project, Project_Group #, Profile
from .models import Defense_Application, Project_Idea
from .models import Student, Faculty, Coordinator
from .models import StudentProfile, FacultyProfile, CoordinatorProfile, ProjectPhase
from .models import ApprovedProject, ApprovedProjectGroup, Not_ApprovedProject
from .models import Approved_Adviser, Approved_panel, Notification, Approved_student
from .models import ProjectGroupSettings

# from .models import CustomPhaseGroup, Defense_order, Phase
# from .models import CustomPhase
#admin.site.register(Project_Group)
# admin.site.register(CustomPhaseGroup)
admin.site.register(AppUser)
admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(Coordinator)
#admin.site.register(StudentProfile)
admin.site.register(ApprovedProject)
admin.site.register(Approved_student)
# admin.site.register(ApprovedProjectGroup)
admin.site.register(Approved_Adviser)
admin.site.register(Not_ApprovedProject)
# admin.site.register(Defense_order)
# admin.site.register(CustomPhase)

# admin.site.register(ProjectPhase)
# admin.site.register(Approved_panel)
#  Mix Profile info into user info

@admin.register(ProjectGroupSettings)
class ProjectGroupSettingsAdmin(admin.ModelAdmin):
    list_display = ['max_proponents']
    fields = ['max_proponents']

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile


class StudentAdmin(admin.ModelAdmin): 
    model = Student
    fields = ["first_name", "last_name", "email", 'deficiencies', 'student_id', "skills","bio","profile_image"]
  
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
    fields = ["first_name", "last_name", "role", "adviser_eligible", "panel_eligible", "profile_image", 'color']
    inlines = [FacultyProfileInline]
    
# Unregister initial User
admin.site.unregister(Faculty)
# Reregister User 
admin.site.register(Faculty, FacultyAdmin)

#  Mix Profile info into user info
class CoordinatorProfileInline(admin.StackedInline):
    model = CoordinatorProfile

    list_display = ["is_current"]

class CoordinatorAdmin(admin.ModelAdmin): 
    model = Coordinator
    fields = ["first_name", "last_name", "role", 'is_current_coordinator', "profile_image"]
    list_display = ["first_name", "last_name", "role", 'is_current_coordinator']
    inlines = [CoordinatorProfileInline]
    
# Unregister initial User
admin.site.unregister(Coordinator)
# Reregister User 
admin.site.register(Coordinator, CoordinatorAdmin)

@admin.register(Project_Idea)
class Project_IdeaAdmin(admin.ModelAdmin):
    fields = 'title', 'description', 'faculty'
    display = 'title', 'faculty'
    readonly_fields = ['created_at',]


@admin.register(Notification) 
class NotificationAdmin(admin.ModelAdmin): #project_type'
    fields = ('sender', 'recipient','notification_type','group', 'message', 'redirect_url', 'created_at', 'is_read')
    list_display = ('sender', 'recipient', 'notification_type', 'created_at')
    readonly_fields = ['created_at', ]
    ordering = ('-created_at', )
   
@admin.register(Project) #  'project_type',
class ProjectAdmin(admin.ModelAdmin): #project_type'
    fields = ('title', 'adviser','description','proponents', 'panel', 'owner', 'status', 'defense_order', 'is_archived')
    list_display = ('title', 'adviser', 'description')
    ordering = ('title', )
    search_fields = ('title', 'description', 'adviser')
    list_filter = ('adviser', )


@admin.register(ProjectPhase)
class ProjectPhaseAdmin(admin.ModelAdmin):
    model = ProjectPhase
    fields = ["project", "phase_type", "verdict", "date", 'first_phase']
    list_display = ["project", "phase_type", "verdict", "date"]
    ordering = ("project",)
    readonly_fields = ['date',]

@admin.register(Project_Group)
class Project_GroupAdmin(admin.ModelAdmin):
    fields = ('proponents', 'pending_proponents', 'approved_by_students', 'declined_proponents', 'requests', 'join_requests', 'declined_requests', 'approved', 'creator')
    list_display = ( 'approved', 'creator')

@admin.register(Defense_Application)
class Defense_ApplicationAdmin(admin.ModelAdmin): 
    fields = ('project', 'project_group', 'adviser', 'title', 'abstract', 'panel', 'manuscript', 'revision_form', 'payment_receipt', 'adviser_confirmation', 'owner', 'submission_date')
    list_display = ('title', 'project', 'project_group', 'adviser' ,'submission_date')
    readonly_fields = ['submission_date', ]



