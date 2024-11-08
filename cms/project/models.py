from django.conf import settings
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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

    # class Course(models.TextChoices)

    base_role = Role.STUDENT
    role = models.CharField(max_length=50, choices=Role.choices, default='STUDENT')
    
    email = models.EmailField(blank=True, default='', unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True )
    username = models.CharField(max_length=255, blank=True)
    phone = models.CharField('Contact Phone', max_length=25, blank=True, null=True)
    course = models.CharField('Course', max_length=100, null=True, blank=True )
    profile_image = models.ImageField(null=True, blank=True, default='static/images/default_profile_pic.jpg',upload_to="images/")
    
   
    #available_schedule = models.ManyToManyField(Available_schedule, related_name='Faculty_available', blank=True )

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)    
    eligible = models.BooleanField('Eligible as Student', default=False)
    eligility_deficiencies = models.CharField('Eligibility Deficiencies', max_length=500, blank=True)
    adviser_eligible = models.BooleanField('Eligible as Adviser', default=False)
    panel_eligible = models.BooleanField('Eligible as Panelist', default=False)
    is_current_coordinator = models.BooleanField('Current Coordinator', default=False)


    USERNAME_FIELD = "email" # user will login using their email
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

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
        ('invitation', 'Group Invitation'),
        ('accepted', 'Invitation Accepted'),
        ('rejected', 'Invitation Rejected'),
    )

    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    group = models.ForeignKey('Project_Group', on_delete=models.CASCADE)
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

class Project(models.Model): 


    title = models.CharField('Title', max_length=120, null=True) # 120 characters
    project_type = models.CharField('Project Type', null=True, max_length=50 )
    description = models.TextField(null=True) # we dont have to put a description if we do not want to
    comments= models.TextField(null=True, blank=True) # we dont have to put a description if we do not want to
    
    proponents = models.ForeignKey(Project_Group, null=True, on_delete=models.SET_NULL)   
    adviser = models.ForeignKey(Approved_Adviser, null=True, on_delete=models.SET_NULL) # If adviser deletes profile, then the projects' adviser will be set to null 
    panel = models.ManyToManyField(Faculty, related_name='project_panel', blank=True )

    # start_date = models.DateTimeField('Start date', null=True,  blank=True)
    # end_date =  models.DateTimeField('End Date', null=True, blank=True)
   
    # when somebody adds a project, whatever his ID is the owner of the project
    owner = models.IntegerField("Project Owner", blank=False, default=24)
    # defense_progress = models.CharField(max_length=50, choices=DEFENSE_PROGRESS, default="topic")
   

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]
    # determines whether a project is a approved project or a proposal 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # allows to use model in admin area.
    def __str__(self):
        return str(self.title) if self.title else "No Project"
    
class ProjectPhase(models.Model):
    PHASE_CHOICES = [
        ('proposal', 'Proposal Defense'),
        ('design', 'Graded 1 or Design Defense'),
        ('preliminary', 'Preliminary Defense'),
        ('final', 'Grade 2 or Final Defense'),
    ]

    RESULT_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('accepted_with_revisions', 'Accepted with Revisions'),
        ('redefense', 'Re-Defense'),
        ('not_accepted', 'Not Accepted'),
    ]

    project = models.ForeignKey(Project, related_name='phases', on_delete=models.CASCADE)
    phase_type = models.CharField(max_length=20, choices=PHASE_CHOICES, blank=False, default='proposal')
    verdict = models.CharField(max_length=50, choices=RESULT_CHOICES, blank=False, default='pending')  # Now defaults to 'pending'
    date = models.DateTimeField(auto_now_add=True)
    
    # class Meta:
    #     get_latest_by = 'date'

    def __str__(self):
        return f"{self.project.title} - {self.get_phase_type_display()}"


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
    abstract = models.TextField( null=True) # we dont have to put a description if we do not want to
    adviser = models.ForeignKey(Approved_Adviser, related_name='application_adviser', null=True, on_delete=models.SET_NULL) # If adviser deletes profile, then the projects' adviser will be set to null 
    panel = models.ManyToManyField(Approved_panel, related_name='capplication_panel', blank=True)
 
    document = models.FileField(upload_to='submissions/', null=True, blank=True )
    submission_date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.project}" if self.project else "No Project Assigned"
        
    # def __str__(self): 
    #     return f"{self.title} by {self.project_group}"
    
    #manuscript = # submit file manuscript 
    #payment = 
    #panel_recommendation = 
    #adviser_acknowledgment_to_defend = 

