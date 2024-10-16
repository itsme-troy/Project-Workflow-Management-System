from django.conf import settings
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
#from free_schedule.models import Available_schedule
# Create your models here.

# Multiple User types 
# Users can have 1 role only, (Admin, Coordinator, Faculty, Student)
# Users cannot change their role (defined at user creation)
# Students and Teachers require separate profile data 

class AppUserManager(UserManager):
      
    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         self.role = self.base_role
    #         return super().save(*args, **kwargs)
        
    def _create_user(self, email, password, **extra_fields):
        # check if user provided email 
        if not email:
            raise ValueError('An email is required.')
        if not password:
            raise ValueError("A password is required.")
        email = self.normalize_email(email) # clean email
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
    faculty_id= models.IntegerField(null=True, blank=True)
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
    coordinator_id= models.IntegerField(null=True, blank=True)

class Project_Group(models.Model): 
    group_name = models.CharField('Group Name', max_length=120, blank=True, null=True, default='') # 120 characters
    adviser = models.ForeignKey(Faculty, related_name="group_adviser", null=True, on_delete=models.SET_NULL) 
    proponents = models.ManyToManyField(Student, related_name='project_proponents', blank=True )

    approved = models.BooleanField('Approved by an Adviser', default=False)
    owner = models.IntegerField("Project Group Creator", blank=False, default=24)

    def __str__(self):
        return self.group_name or ''  # return
    
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

class Project(models.Model): 
    # class Defense_result(models.TextChoices): 
    #     PENDING = "-", "PENDING"
    #     ACCEPTED = "Accepted", "ACCEPTED"
    #     ACCEPTED_WITH_REVISIONS = "Accepted with Revisions", "ACCEPTED_WITH_REVISIONS" 
    #     REDEFENSE = "Re-Defense", "REDEFENSE", 
    #     NOT_ACCEPTED =  "Not-Accepted", "NOT_ACCEPTED",

    title = models.CharField('Title', max_length=120, blank=True, null=True) # 120 characters
    project_type = models.CharField('Project Type', blank=True, null=True, max_length=50 )
    description = models.TextField(blank= True, null=True) # we dont have to put a description if we do not want to
    proponents = models.ForeignKey(Project_Group, blank=True, null=True, on_delete=models.SET_NULL)   
    adviser = models.ForeignKey(Approved_Adviser, blank=True, null=True, on_delete=models.SET_NULL) # If adviser deletes profile, then the projects' adviser will be set to null 
    panel = models.ManyToManyField(Faculty, related_name='project_panel', blank=True )

    # start_date = models.DateTimeField('Start date', null=True,  blank=True)
    # end_date =  models.DateTimeField('End Date', null=True, blank=True)
   
    # when somebody adds a project, whatever his ID is the owner of the project
    owner = models.IntegerField("Project Owner", blank=False, default=24)
    # defense_progress = models.CharField(max_length=50, choices=DEFENSE_PROGRESS, default="topic")
   
    # determines whether a project is a approved project or a proposal 
    approved = models.BooleanField('Approved by an Adviser', default=False)
    
    proposal_defense = models.CharField('Preliminary Defense', max_length=50, blank=True, null=True)
    design_defense = models.CharField('Design Defense', max_length=50,  blank=True, null=True )
    preliminary_defense = models.CharField('Preliminary Defense', max_length=50, blank=True, null=True)
    final_defense = models.CharField('Final Defense ', max_length=50, blank=True, null=True )
    
    # allows to use model in admin area.
    def __str__(self):  
        return self.title
    
class ProjectManager(BaseUserManager): 
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(approved=True)
    
class ApprovedProject(Project): 
    approved_project = ProjectManager()
    
    class Meta: 
        proxy = True 

class Defense_Application(models.Model): 
    owner = models.IntegerField("Application Owner", blank=True, default=24)
    project_group = models.ForeignKey(ApprovedProjectGroup, blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    project = models.ForeignKey(ApprovedProject, null=False, blank=False, on_delete=models.CASCADE)
    abstract = models.TextField(blank= True, null=True) # we dont have to put a description if we do not want to
    adviser = models.ForeignKey(Approved_Adviser, related_name='application_adviser', blank=True, null=True, on_delete=models.SET_NULL) # If adviser deletes profile, then the projects' adviser will be set to null 
    panel = models.ManyToManyField(Approved_panel, related_name='application_panel', blank=True, null=True)
 
    document = models.FileField(upload_to='submissions/', null=True, blank=True )
    submission_date = models.DateTimeField(auto_now_add=False, null=True, blank=True )

    def __str__(self):
        return f"{self.project}" 
        
    # def __str__(self): 
    #     return f"{self.title} by {self.project_group}"
    
    #manuscript = # submit file manuscript 
    #payment = 
    #panel_recommendation = 
    #adviser_acknowledgment_to_defend = 

