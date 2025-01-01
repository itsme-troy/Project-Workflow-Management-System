from django.conf import settings
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
import random
from django.contrib.auth import get_user_model

# Multiple User types 
# Users can have 1 role only, (Admin, Coordinator, Faculty, Student)
# Users cannot change their role (defined at user creation)
# Students and Teachers require separate profile data 

class AppUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        # Check if user provided email
        if not email:
            raise ValueError('An email is required.')
        if not password:
            raise ValueError("A password is required.")
        
        # Ensure the email is a GBox account
        if not email.endswith('@gbox.domain'):  # Replace 'gbox.domain' with the actual GBox domain
            raise ValueError('Only GBox accounts are allowed.')

        email = self.normalize_email(email)  # Clean email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user
    
    
    def create_user(self, email=None, password=None, **extra_fields): 
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
        
    def create_superuser(self, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError('An email is required.')
        if not password:
            raise ValueError("A password is required.")
        extra_fields.setdefault('is_staff', True) 
        extra_fields.setdefault('is_superuser', True) 
        extra_fields.setdefault('is_active', True) 
        
        user = self.create_user( email, password, **extra_fields)
        #user.is_superuser = True
        user.save()
        return user

class AppUser(AbstractUser, PermissionsMixin):  # permissionsMixin
    class Role(models.TextChoices):
        #ADMIN = "ADMIN" "Admin"
        COORDINATOR = "COORDINATOR", "Coordinator"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"

    base_role = Role.STUDENT
    role = models.CharField(max_length=50, choices=Role.choices, default='STUDENT')
    
    email = models.EmailField(blank=True, default='', unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True )
    username = models.CharField(max_length=255, blank=True)
    phone = models.CharField('Contact Phone', max_length=25, blank=True, null=True)
    course = models.CharField('Course', max_length=100, null=True, blank=True )
    profile_image = models.ImageField(null=True, blank=True, default='static/images/default_profile_pic.jpg', upload_to="images/")
    student_id = models.CharField(max_length=255, blank=True)
   
    #available_schedule = models.ManyToManyField(Available_schedule, related_name='Faculty_available', blank=True )

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)    
    eligible = models.BooleanField('Eligible as Student', default=False)
    deficiencies = models.CharField('Eligibility Deficiencies', max_length=500, blank=True)
    adviser_eligible = models.BooleanField('Eligible as Adviser', default=False)
    panel_eligible = models.BooleanField('Eligible as Panelist', default=False)
    is_current_coordinator = models.BooleanField('Current Coordinator', default=False)

    USERNAME_FIELD = "email" # user will login using their email
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    color = models.CharField(max_length=7, default="#007BFF")  # Hex color code

    def save(self, *args, **kwargs):
        # Assign a random color only if no color exists
        if not self.color:
            self.color = self.generate_random_color()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))


    def get_first_name(self): 
        return self.first_name
    def get_last_name(self): 
        return self.last_name
    
    class Meta: 
        verbose_name = "User"
        verbose_name_plural = "Users"

    objects = AppUserManager() # use this to get all users
        
    def __str__(self):
            return self.first_name + " " + self.last_name  # return

class StudentManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=AppUser.Role.STUDENT)
    
class Student(AppUser):
    base_role = AppUser.Role.STUDENT
    student = StudentManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for students"

@receiver(post_save, sender=Student)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "STUDENT": 
        user_profile = StudentProfile(user=instance)
    
        user_profile.save()
        #Have the user follow themselves 
        user_profile.groupmates.set([instance.id])
        user_profile.save()
        
        # StudentProfile.objects.create(user=instance)
        # StudentProfile.groupmates.set([instance.profile.id])

class StudentProfile(models.Model): 
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    student_id = models.IntegerField(null=True, blank=True)
    # groupmates = models.ManyToManyField(Student, 
    #     related_name="is_grouped_with", 
    #     blank=True)
    date_modified = models.DateTimeField(Student, auto_now=True)

    def __str__(self):
        return self.user.last_name + ", " + self.user.first_name 


class FacultyManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=AppUser.Role.FACULTY)

class Faculty(AppUser):
    base_role = AppUser.Role.STUDENT
    faculty = FacultyManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for Faculty"

@receiver(post_save, sender=Faculty)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "FACULTY": 
        FacultyProfile.objects.create(user=instance)


class FacultyProfile(models.Model): 
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    # faculty_id= models.IntegerField(null=True, blank=True)
    date_modified = models.DateTimeField(Faculty, auto_now=True)


class CoordinatorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=AppUser.Role.COORDINATOR)

class Coordinator(AppUser):
    base_role = AppUser.Role.COORDINATOR
    coordinator = CoordinatorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for Coordinator"

@receiver(post_save, sender=Coordinator)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "COORDINATOR": 
        CoordinatorProfile.objects.create(user=instance)    

class CoordinatorProfile(models.Model): 
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    # is_current = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.is_current:
            CoordinatorProfile.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class Project_Group(models.Model): 
    # adviser = models.ForeignKey(Faculty, related_name="group_adviser", null=True, on_delete=models.SET_NULL) 
    proponents = models.ManyToManyField(Student, related_name='project_proponents', blank=True )
    pending_proponents = models.ManyToManyField(Student, related_name='pending_project_groups', blank=True)
    approved_by_students = models.ManyToManyField(Student, related_name='approved_project_groups', blank=True)
    declined_proponents = models.ManyToManyField(Student, related_name='declined_groups', blank=True)
    
    declined_requests = models.ManyToManyField(Student,related_name='declined_requests', blank=True, help_text="Students who have been declined to join this group")
    join_requests = models.ManyToManyField(Student, related_name='requested_groups', blank=True, help_text="Students who have requested to join this group")
    requests = models.ManyToManyField(Student, related_name='sent_requests', blank=True, help_text="Students who have sent join requests to this group")

    approved = models.BooleanField('All Students Approved', default=False)
    creator = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='owned_groups', verbose_name="Project Group Creator")
    
    def __str__(self):
        # Fetch all last names in the group
        last_names = self.proponents.values_list('last_name', flat=True)  # Assuming 'last_name' is a field in the Student model
        return f"{', '.join(last_names)}" if last_names else 'No Students'
    
    def __str__(self):
        # Fetch all last names in the group
        last_names = self.proponents.values_list('last_name', flat=True)  # Assuming 'last_name' is a field in the Student model
        return f"{', '.join(last_names)}" if last_names else 'No Students'
    
class ProjectGroupManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(approved=True)
    
class ApprovedProjectGroup(Project_Group): 
    approved_project_group = ProjectGroupManager()
    
    class Meta: 
        proxy = True 

class AdviserManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(adviser_eligible=True)
    
class Approved_Adviser(Faculty): 
    approved_adviser = AdviserManager()
    
    class Meta: 
        proxy = True 

class PanelManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(panel_eligible=True)
    
class Approved_panel(Faculty): 
    approved_panel = PanelManager()
    
    class Meta: 
        proxy = True 

class ApprovedStudentManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(eligible=True)
    
class Approved_student(Student): 
    approved_panel = ApprovedStudentManager()
    
    class Meta: 
        proxy = True 

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('INVITATION', 'Group Invitation'),
        ('ACCEPTED', 'Accepted Group Invitation '),
        ('REJECTED', 'Rejected Group Invitation'),
        ('GROUP_COMPLETE', 'Group Completion'),
        ('GROUP_FINALIZED', 'Group Finalization'),
        ('LEAVE_GROUP', 'Left Group'),
        ('ROLE_CHANGE', 'New Coordinator'),
        ('ROLE_TRANSFER', 'Leader Role Transfer'),
        ('NEW_MEMBER', 'New Member Added'),
        ('ADDED_TO_GROUP', 'You have been added to a group'),
        ('DECLINED_JOIN_REQUEST', 'Join Request Declined'),
        ('JOIN_REQUEST', 'Join Request'),
        ('JOIN_REQUEST_CANCELLED', 'Join Request Cancelled'),   
        ('VERDICT', 'Verdict'),
        ('PROJECT_ACCEPTED', 'Project Accepted'),
        ('PROJECT_REJECTED', 'Project Rejected'),
        ('SUBMITTED_DEFENSE_APPLICATION', 'Defense Application'),
        ('PANELIST_SELECTED', 'Panelist Selected'),
        ('MEMBER_REMOVAL', 'Member Removed'),
        ('ADVISER_ELIGIBILITY', 'Adviser Eligibility'),
        ('PANELIST_ELIGIBILITY', 'Panelist Eligibility'),
        ('COMMENTS_UPDATED', 'Comments Updated'),
        ('NEW_PROJECT_PROPOSAL', 'New Project Proposal'),
        ('PANELIST_DECLINE', 'Panelist Decline'), 
        ('PANELIST_SELECTED', 'Panelist Selected'), 
        ('PROJECT_DELETED', 'Project Deleted'), 
        ('PROPOSAL_DELETED', 'Proposal Deleted'), 
        ('DEFICIENCIES', 'Deficiencies Updated'), 
    )   

    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    group = models.ForeignKey('Project_Group', on_delete=models.CASCADE, null=True, blank=True)
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    redirect_url = models.URLField(max_length=200, null=True, blank=True)
    verdict = models.CharField('Verdict', null=True, max_length=50 )

    class Meta:
        ordering = ['-created_at']

# Defined choices upfront for better maintainability
PHASE_CHOICES = [
    ('proposal', 'Proposal Defense'),
    ('design', 'Graded Defense 1'),
    ('preliminary', 'Preliminary Defense'),
    ('final', 'Graded Final Defense'),
]

RESULT_CHOICES = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('accepted_with_revisions', 'Accepted with Revisions'),
    ('redefense', 'Re-Defense'),
    ('not_accepted', 'Not Accepted'),
]

# # Phase Model: A phase for the defense, could be part of multiple defense orders
# class Phase(models.Model):
#     project = models.ForeignKey(Project)
#     name = models.CharField(max_length=100, blank=True, null=True)  # Custom name for the phase 
#     phase_type = models.CharField(max_length=20, choices=PHASE_CHOICES, blank=False, default='proposal')
#     verdict = models.CharField(max_length=50, choices=RESULT_CHOICES, blank=False, default='pending')  # Now defaults to 'pending'
#     date = models.DateTimeField(auto_now_add=True)  # Renamed `date` to `created_at` for clarity

#     def __str__(self):
#         return self.name if self.name else f"{self.get_phase_type_display()} - {self.get_verdict_display()}"

# # Through model to preserve phase order in a defense order
# class DefenseOrderPhase(models.Model):
#     defense_order = models.ForeignKey('Defense_order', related_name='defense_order_phases', on_delete=models.CASCADE)
#     phase = models.ForeignKey(Phase, related_name='defense_order_phases', on_delete=models.CASCADE)
#     phase_order = models.PositiveIntegerField()  # Field to store the order of phases in this defense order

#     class Meta:
#         ordering = ['phase_order']  # Ensures that phases are ordered by phase_order when queried
#         unique_together = ('defense_order', 'phase')  # Enforces uniqueness for each phase in a defense order

#     def __str__(self):
#         return f"{self.defense_order.name} - {self.phase.get_phase_type_display()}"

# # DefenseOrder Model: Customizable set of defense phases for a project
# class Defense_order(models.Model):
#     name = models.CharField('Custom Phase Name', max_length=120, null=True)
#     description = models.TextField(blank=True, null=True)  # Optional description for the custom set

#     # Accessor for the phases
#     @property
#     def phases(self):
#         return [d.phase for d in self.defense_order_phases.all()]

#     def __str__(self):
        # return self.name


class Project(models.Model): 
    title = models.CharField('Title', max_length=120, null=True) # 120 characters
    project_type = models.CharField('Project Type', null=True, max_length=50 )
    description = models.TextField(null=True) # we dont have to put a description if we do not want to
    comments= models.TextField(null=True, blank=True) # we dont have to put a description if we do not want to
    
    proponents = models.ForeignKey(Project_Group, null=True, on_delete=models.SET_NULL)  
    adviser = models.ForeignKey(Faculty, null=True, on_delete=models.SET_NULL) # If adviser deletes profile, then the projects' adviser will be set to null 
    panel = models.ManyToManyField(Faculty, related_name='project_panel', blank=True )    

    # when somebody adds a project, whatever his ID is the owner of the project
    owner = models.IntegerField("Project Owner", blank=False, default=24)
    # defense_progress = models.CharField(max_length=50, choices=DEFENSE_PROGRESS, default="topic")   

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    # defense_order = models.ForeignKey(Defense_order, null=True, on_delete=models.SET_NULL)

    # determines whether a project is a approved project or a proposal 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_archived = models.BooleanField(default=False)
    
    # allows to use model in admin area.
    def __str__(self):
        return str(self.title) if self.title else "No Project"
    
    @property
    def panel1(self):
        return self.panel.all()[0] if self.panel.count() > 0 else None

    @property
    def panel2(self):
        return self.panel.all()[1] if self.panel.count() > 1 else None

    @property
    def panel3(self):
        return self.panel.all()[2] if self.panel.count() > 2 else None
    

class ProjectPhase(models.Model):
    PHASE_CHOICES = [
        ('proposal', 'Proposal Defense'),
        ('design', 'Graded Defense 1'),
        ('preliminary', 'Preliminary Defense'),
        ('final', 'Graded Final Defense'),
    ]

    RESULT_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('accepted_with_revisions', 'Accepted with Revisions'),
        ('redefense', 'Re-Defense'),
        ('not_accepted', 'Not Accepted'),
    ]

    project = models.ForeignKey(Project, related_name='phases', on_delete=models.CASCADE)
    phase_type = models.CharField(max_length=20, choices=PHASE_CHOICES,  default='proposal')
    verdict = models.CharField(max_length=50, choices=RESULT_CHOICES, default='pending')  # Now defaults to 'pending'
    date = models.DateTimeField(auto_now_add=False)
    first_phase = models.BooleanField(default=False)
    
    # class Meta:
    #     get_latest_by = 'date'

    def __str__(self):
        return f"{self.project.title} - {self.get_phase_type_display()}"
    
    def clean(self):
        if self.first_phase:
            existing_first_phase = ProjectPhase.objects.filter(project=self.project, first_phase=True).exclude(id=self.id)
            if existing_first_phase.exists():
                raise ValidationError('A project can only have one first phase.')

# class Custom_PhaseSequence(models.Model): 
#     project = models.ForeignKey(Project, related_name="custom_phases", on_delete=models.CASCADE)
#     # phases allow a project to have a combination of phases
#     phases = models.ManyToManyField(ProjectPhase, related_name='custom_sets', blank=True)  # Many-to-many to ProjectPhase 
#     # phase_type = models.CharField(max_length=50)
#     # order = models.IntegerField()  # To define the order of phases
    
#     name = models.CharField(max_length=100, blank=False, default='Custom Defense Set')  # You can name the custom phase set
#     description = models.TextField(blank=True, null=True)  # Optional description for the custom set
#     # phase_order = models.IntegerField(default=0)  # Add an order field to manage the sequence

#     def __str__(self):
#         return f"Custom Phases for {self.project.title} ({self.name})"

    # class Meta:
    #     ordering = ['phase_order']  # Ensures that phases are ordered correctly

# class CustomPhaseGroup(models.Model): 
#     project=models.ForeignKey(Project, related_name="custom_phases", on_delete=models.CASCADE)
    
#     # phases allow a project to have a combination of phases
#     phases = models.ManyToManyField(ProjectPhase, related_name='custom_sets', blank=True)  # Many-to-many to ProjectPhase 
#     # phase_type = models.CharField(max_length=50)
#     # order = models.IntegerField()  # To define the order of phases
    
#     name = models.CharField(max_length=100, blank=False, default='Custom Defense Set')  # You can name the custom phase set
#     description = models.TextField(blank=True, null=True)  # Optional description for the custom set
#     phase_order = models.IntegerField(default=0)  # Add an order field to manage the sequence

#     def __str__(self):
#         return f"Custom Phases for {self.project.title} ({self.name})"

#     class Meta:
#         ordering = ['phase_order']  # Ensures that phases are ordered correctly

class ProjectManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(status='approved')
    
class ApprovedProject(Project): 
    approved_project = ProjectManager()
    
    class Meta: 
        proxy = True 

class Not_ApprovedProjectManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(status__in=['pending', 'declined'])
    
class Not_ApprovedProject(Project): 
    not_approved_project = Not_ApprovedProjectManager()
    
    class Meta: 
        proxy = True 

class Defense_Application(models.Model): 
    TITLE_CHOICES = [
            ('proposal', 'Proposal Defense'),
            ('design', 'Graded 1 Defense'),
            ('preliminary', 'Preliminary Defense'),
            ('final', 'Graded 2 Defense'),
        ]

    owner = models.IntegerField("Application Owner", blank=True, default=24)
    project_group = models.ForeignKey(ApprovedProjectGroup, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, choices=TITLE_CHOICES, null=True)
    project = models.ForeignKey(ApprovedProject, null=False, blank=False, on_delete=models.CASCADE)
    abstract = models.TextField( null=True, blank=True) # we dont have to put a description if we do not want to
    adviser = models.ForeignKey(Approved_Adviser, related_name='application_adviser', null=True, on_delete=models.SET_NULL) # If adviser deletes profile, then the projects' adviser will be set to null 
    panel = models.ManyToManyField(Approved_panel, related_name='capplication_panel', blank=True)
 
    manuscript = models.FileField(upload_to='submissions/manuscript', null=True, blank=True )
    revision_form = models.FileField(upload_to='submissions/revision_form', null=True, blank=True )
    payment_receipt = models.ImageField(upload_to='submissions/payment_receipt', null=True, blank=True )
    adviser_confirmation = models.ImageField(upload_to='submissions/adviser_confirmation', null=True, blank=True )
    
    submission_date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.project}" if self.project else "No Project Assigned"
        
    # def __str__(self): 
    #     return f"{self.title} by {self.project_group}"
    
    #manuscript = # submit file manuscript 
    #payment = 
    #panel_recommendation = 
    #adviser_acknowledgment_to_defend = 

class Project_Idea(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    faculty = models.ForeignKey(Faculty, null=True, on_delete=models.SET_NULL) # 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# class CustomPhase(models.Model):
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='custom_phases')
#     # Allows the user to define custom name for each phase
#     phase_name = models.CharField(max_length=100) 
#     # Helps manage the order of the phases
#     phase_order = models.PositiveIntegerField()

#     class Meta:
#         ordering = ['phase_order']

#     def __str__(self):
#         return self.phase_name