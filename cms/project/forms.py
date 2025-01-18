from django import forms 
from django.forms import ModelForm 
from .models import Project, Defense_Application, Project_Group, StudentProfile, Student
from .models import Faculty, ProjectPhase, Project_Idea, ProjectGroupSettings
# from .models import CustomPhaseGroup, Defense_order
from django.core.exceptions import ValidationError
# from .models import CustomPhase
from .models import PHASE_CHOICES, RESULT_CHOICES

from django.contrib.auth import get_user_model 
User = get_user_model()

# class CustomPhaseForm(forms.ModelForm):
#     class Meta:
#         model = Custom_Phase
#         fields = ['project', 'phases', 'name', 'description']

#     def __init__(self, *args, **kwargs):
#         project = kwargs.get('initial', {}).get('project', None)
#         super().__init__(*args, **kwargs)
#         if project:
#             # Limit the phases to the project-specific ones
#             self.fields['phases'].queryset = ProjectPhase.objects.filter(project=project)


class UpdateDeficienciesForm(forms.ModelForm):  

    class Meta: 
        model = User  # Ensure 'User' is the correct model you are using
        
        fields = ('first_name', 'last_name', 'email', 'student_id', 'course', 'deficiencies')

        course_choices = [
            ("BS Information Technology", "BS Information Technology"), 
            ("BS Computer Science", "BS Computer Science"), 
            ("BS Information Systems", "BS Information Systems"), 
        ]
        
        widgets = { 
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student ID'}),
            'course': forms.Select(choices=course_choices, attrs={'class': 'form-select'}),
            'deficiencies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,  # Adjust rows as needed
                'placeholder': 'Enter deficiencies or requirements for the student here...'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

         # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

         # Make fields read-only by disabling them
        for field_name in ['first_name', 'last_name', 'email', 'student_id', 'course']:
            self.fields[field_name].widget.attrs['disabled'] = 'disabled'

class UpdateDeficienciesFacultyForm(forms.ModelForm):  

    class Meta: 
        model = User  # Ensure 'User' is the correct model you are using
        
        fields = ('first_name', 'last_name', 'email', 'deficiencies')
        
        widgets = { 
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'deficiencies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,  # Adjust rows as needed
                'placeholder': 'Enter deficiencies or requirements for the Faculty here...'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

         # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

         # Make fields read-only by disabling them
        for field_name in ['first_name', 'last_name', 'email']:
            self.fields[field_name].widget.attrs['disabled'] = 'disabled'


class ProjectIdeaForm(forms.ModelForm):
    class Meta:
        model = Project_Idea
        fields = ['title','description', 'faculty']
        
        labels = {
            'title': 'Title', 
            'description' : 'Description'
        }

        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder':'Short Description of the Project Idea'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the logged-in user
        super(ProjectIdeaForm, self).__init__(*args, **kwargs)

        if user:
            # Set the initial value of the faculty field to the logged-in user
            self.initial['faculty'] = user
        
        # Disable the proponents field
        self.fields['faculty'].widget.attrs['disabled'] = 'disabled'


class CoordinatorForm(forms.Form):
        user = forms.ModelChoiceField(
            queryset=Faculty.objects.filter(role='FACULTY'),
            label="Select Coordinator",
            widget=forms.Select(attrs={'class': 'form-select', 'size': '10'})
        )

        def clean_user(self):
            user = self.cleaned_data.get('user')
            if not user:
                raise forms.ValidationError("You must select a coordinator.")
            return user

class ProjectGroupInviteForm(ModelForm):
    class Meta:
        model = Project_Group
        fields = ['proponents']
        
        labels = {
            'proponents': 'Select Additional Members',
        }
        help_texts = {
            'proponents': 'Hold "Ctrl" button to select multiple students',
        }
        widgets = {
            'proponents': forms.SelectMultiple(attrs={'class': 'form-select', 'placeholder': 'Select Proponents', 'size': '10'}),
        }
        
    def __init__(self, *args, **kwargs):
        max_proponents = kwargs.pop('max_proponents', ProjectGroupSettings.get_max_proponents())  # Get the limit from settings
        group = kwargs.pop('group', None)  # Get the existing group
        super(ProjectGroupInviteForm, self).__init__(*args, **kwargs)

        self.max_proponents = max_proponents  # Store the value in an instance variable

        # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

        if group:
            # Get all users who are either pending or approved
            existing_members = list(group.pending_proponents.all()) + list(group.proponents.all())
            existing_member_ids = [member.id for member in existing_members]

            # Exclude users who are already in any approved group
            users_in_approved_groups = Student.objects.filter(
                id__in=Project_Group.objects.filter(approved=True).values_list('proponents', flat=True)
            )

            # Store group reference for use in clean_proponents
            self.group = group

            # Calculate available slots
            available_slots = self.max_proponents - len(existing_members)


             # If the group already has # of members (pending + approved) greater than or equal to max proponents, disable new selections
            if len(existing_members) >= self.max_proponents:
                self.fields['proponents'].widget.attrs['disabled'] = 'disabled'
                self.fields['proponents'].help_text = f'Maximum group size {self.max_proponents} reached'

            else:
                # Dynamically update help text with available slots
                self.fields['proponents'].help_text = f'You can add {available_slots} more member{"s" if available_slots != 1 else ""}.'

            # Set the queryset to exclude existing members and users in approved groups
            self.fields['proponents'].queryset = (
                Student.objects.filter(role='STUDENT', eligible=True)
                .exclude(id__in=existing_member_ids)
                .exclude(id__in=users_in_approved_groups)
            )

            # Pre-select existing members and make them unselectable in the frontend
            self.fields['proponents'].initial = existing_member_ids
            
            # Add data attributes for JavaScFript to handle disabled selections
            self.fields['proponents'].widget.attrs['data-existing-members'] = ','.join(map(str, existing_member_ids))

    def clean_proponents(self):
        proponents = self.cleaned_data.get('proponents')
        group = getattr(self, 'group', None)

        if group:   
             # Get existing members (both pending and approved)
            existing_members = list(group.pending_proponents.all()) + list(group.proponents.all())
            
            # Calculate how many new members can be added
            available_slots = self.max_proponents - len(existing_members)
            
            if available_slots <= 0 and proponents:
                raise ValidationError(f'The group already has the maximum number of members {self.max_proponents}.')
            
            if len(proponents) > available_slots:
                raise ValidationError(f'You can only add {available_slots} more member{"s" if available_slots != 1 else ""} to this group.')

        return proponents

class ProjectGroupForm(ModelForm):
    class Meta:
        model = Project_Group
        fields = ['proponents']  # 'adviser', 
        
        labels = {
            # 'adviser': 'Select Adviser',
            'proponents': 'Select Proponents: hold "ctrl" button to select multiple',
        }
        widgets = {
            # 'adviser': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select Adviser'}),
            'proponents': forms.SelectMultiple(attrs={'class': 'form-select', 'placeholder': 'Select Proponents',  'data-selectable': 'true'}),
        }
    
    def __init__(self, *args, **kwargs):
        max_proponents = kwargs.pop('max_proponents', ProjectGroupSettings.get_max_proponents())  # Get the limit from settings
        user = kwargs.pop('user', None)  # Retrieve the logged-in user from the view
        approved_users = kwargs.pop('approved_users', [])  # List of users with approved project groups
        super(ProjectGroupForm, self).__init__(*args, **kwargs)

        self.max_proponents = max_proponents - 1  # Store the value in an instance variable
        if user:
            # Ensure user is cast to the actual user object if it's a SimpleLazyObject
            if hasattr(user, '_wrapped') and isinstance(user._wrapped, object):
                user = user._wrapped

            # Pre-select the logged-in user's ID in the proponents field
            if 'proponents' in self.fields:
                initial_proponents = self.initial.get('proponents', [])  # Get initial proponents
                self.initial['proponents'] = [user.id] + list(initial_proponents)  # Pre-select logged-in user's ID

             # Adjust the queryset to exclude users with approved project groups
            self.fields['proponents'].queryset = self.fields['proponents'].queryset.exclude(id__in=approved_users).filter(eligible=True)

            # Adjust the queryset to include the logged-in user but prevent them from being deselected
            self.fields['proponents'].queryset = self.fields['proponents'].queryset.exclude(id=user.id) | self.fields['proponents'].queryset.filter(id=user.id)
            self.fields['proponents'].widget.attrs['data-logged-in-user'] = str(user.id)  # Tag for the front-end to know the user

    def clean_proponents(self):
        proponents = self.cleaned_data.get('proponents')

          # Count the number of selected proponents
        selected_count = len(proponents)

          # Ensure that the number of proponents does not exceed the set limit
        if selected_count > self.max_proponents:
            raise ValidationError(
                f'You have selected {selected_count} proponents. The limit is {self.max_proponents}, including yourself.'
            )
        # Get the logged-in user's ID from the initial data
        user_id = self.initial.get('proponents', [None])[0]  # Get the first proponent's ID or None if not set

        # Ensure the logged-in user (by ID) is always part of the proponents
        if user_id and user_id not in [proponent.id for proponent in proponents]:
            proponents = list(proponents)  # Convert to a list if necessary
            # Add the logged-in user back to the proponents list
            proponents.append(self.fields['proponents'].queryset.get(id=user_id))

            # Ensure that the number of proponents does not exceed the set limit
        if selected_count > self.max_proponents:
            raise ValidationError(
                f'You have selected {selected_count} proponents. The limit is {self.max_proponents}, including yourself.'
            )
        
        return proponents

class VerdictForm(forms.ModelForm):
    class Meta:
        model = ProjectPhase
        fields = ['verdict']  # status stores the verdict
        widgets = {
            'verdict': forms.Select(choices=ProjectPhase.RESULT_CHOICES, attrs={'class': 'form-select'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.instance.project

        # Count the number of redefense verdicts
        redefense_count = project.phases.filter(verdict='redefense').count()

        # Fetch the last completed phase, if any
        last_completed_phase = project.phases.exclude(verdict='pending').order_by('-date').first()

         # Exclude "Redefense" if the project has already had two redefenses or if last phase was redefense
         # if the last phase was redefense, or if the phase_type is "design" or "final"
        if (redefense_count >= 2 or 
            (last_completed_phase and last_completed_phase.verdict == 'redefense') or
            self.instance.phase_type in ['design', 'final']):
            self.fields['verdict'].choices = [
                choice for choice in ProjectPhase.RESULT_CHOICES if choice[0] != 'redefense'
            ]
  
class CapstoneSubmissionForm(ModelForm):
    class Meta:
        model = Defense_Application
        fields = ['title', 'project', 'project_group', 'adviser', 'panel', 
                  'manuscript', 'revision_form', 'payment_receipt', 'adviser_confirmation']
        
        labels = {
            'title': 'Type of Defense',
            'project': 'Project',
            'project_group': 'Project Group',
            'adviser': 'Adviser',
            'panel': 'Panel',
            'manuscript': 'Manuscript',
            'revision_form': 'Revision Form',
            'payment_receipt': 'Payment Receipt',
            'adviser_confirmation': 'Proof of Adviser\'s Confirmation',
        }

        widgets = {
            'title': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select Type of Defense'}),
            'project': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Enter'}),
            'project_group': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Proponents'}),
            'adviser': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Panel'}),
            'panel': forms.SelectMultiple(attrs={'class': 'form-control', 'placeholder': 'Panel'}),
            'manuscript': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Manuscript'}),
            'revision_form': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Revision Form'}),
            'payment_receipt': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Payment Receipt'}),
            'adviser_confirmation': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Proof of Adviser\'s Confirmation'}),
        }
        help_texts = {
            'manuscript': 'Accepted formats: PDF only',
            'revision_form': 'Accepted formats: PDF only',
            'payment_receipt': 'Accepted formats: PNG, JPG',
            'adviser_confirmation': 'Accepted formats: PNG, JPG',
        }

    def __init__(self, *args, **kwargs):
        super(CapstoneSubmissionForm, self).__init__(*args, **kwargs)

        # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

        # Set the choices for the title field to use the human-readable names
        self.fields['title'].choices = Defense_Application.TITLE_CHOICES

        # Disable fields
        self.fields['project_group'].widget.attrs['disabled'] = 'disabled'
        self.fields['adviser'].widget.attrs['disabled'] = 'disabled'
        self.fields['project'].widget.attrs['disabled'] = 'disabled'
        self.fields['panel'].widget.attrs['disabled'] = 'disabled'
        self.fields['title'].widget.attrs['disabled'] = 'disabled'


        # Fetch the project from initial data or instance
        project = self.initial.get('project') if 'project' in self.initial else None    
        
        if project:
            # Set initial queryset and values for the panel
            self.fields['panel'].initial = project.panel.all()
            self.fields['panel'].queryset = project.panel.all()

            # Exclude the adviser from the panel queryset
            adviser_id = self.initial.get('adviser')
            if adviser_id:
                self.fields['panel'].queryset = self.fields['panel'].queryset.exclude(id=adviser_id)

            # Set the title in the form's initial data
            self.fields['title'].initial = self.initial.get('next_phase_type') 

    def clean_manuscript(self):
        manuscript = self.cleaned_data.get('manuscript')
        if manuscript and not manuscript.name.endswith('.pdf'):
            raise ValidationError('The manuscript must be a PDF file.')
        return manuscript

    def clean_revision_form(self):
        revision_form = self.cleaned_data.get('revision_form')
        if revision_form and not revision_form.name.endswith('.pdf'):
            raise ValidationError('The revision form must be a PDF file.')
        return revision_form
    
    def clean_payment_receipt(self):
        payment_receipt = self.cleaned_data.get('payment_receipt')
        if payment_receipt and not (payment_receipt.name.endswith('.jpg') or payment_receipt.name.endswith('.png')):
            raise ValidationError('The payment receipt must be a JPG or PNG file.')
        return payment_receipt

    def clean_adviser_confirmation(self):
        adviser_confirmation = self.cleaned_data.get('adviser_confirmation')
        if adviser_confirmation and not (adviser_confirmation.name.endswith('.jpg') or adviser_confirmation.name.endswith('.png')):
            raise ValidationError('The adviser confirmation must be a JPG or PNG file.')
        return adviser_confirmation
 
# Create a project form 
class ProjectForm(ModelForm): 
    # meta allows to sort of define things in a class
    class Meta: 
        model = Project
        project_type_choices = [ 
            ("Capstone Project", "Capstone Project" ),
            ("Senior Thesis", "Senior Thesis"),
            ("IS Plan", "IS Plan")
        ]

        fields =   ('title', 'project_type', 'proponents', 'adviser',
            'panel', 'description', 'comments') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Choose an Adviser', 
            'description': 'Project Description',
            'panel':'Select a Panel', 
            'comments': 'Faculty Comments'
             # 'defense_date':'YYYY-MM-DD HH:MM:SS',
        }
        help_texts = {
            'adviser': 'You are not allowed to submit proposals to multiple advisers unless the all the previous proposals are declined first.',
        }
        
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-control', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Select an Adviser'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder':'Please provide a brief description of the project'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel', 'size': '10'}), 
            'comments': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Comments'}),   
            }
        
    # defense_order = forms.ModelChoiceField(queryset=Defense_order.objects.all(), empty_label="Select Defense Order")
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProjectForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

        # Filter the queryset for the adviser field
        self.fields['adviser'].queryset = Faculty.objects.filter(adviser_eligible=True)

         # Filter the queryset for the panel field
        self.fields['panel'].queryset = Faculty.objects.filter(panel_eligible=True)


        # Disable the proponents field
        self.fields['proponents'].widget.attrs['disabled'] = 'disabled'

        # Hide the comments field if the user is a student
        if user and user.role == 'STUDENT':
            self.fields.pop('comments', None)


    def clean(self):
        cleaned_data = super().clean()
        adviser = cleaned_data.get('adviser')
        panel = cleaned_data.get('panel')
        errors = set()

        if adviser and panel:
            # Check if adviser is in panel
            if adviser in panel:
                errors.add(f"The adviser cannot be one of the panelists.")
        
            # If user is a student, enforce single selection
            if len(panel) > 1:
                errors.add(f'Students can select only one panelist.')

        # Add errors to the form if there are any
        if errors:
            for error in errors:
                self.add_error('panel', error)
            # Return None so that the form is marked invalid but not break with an exception
            return None
        
        return cleaned_data
    
# class ProjectDefenseOrderForm(forms.ModelForm): 
#     class Meta: 
#         model = Project
#         fields = ['']
    
class SelectPanelistForm(ModelForm): 
    # meta allows to sort of define things in a class
    class Meta: 
        model = Project
        project_type_choices = [ 
            ("Capstone Project", "Capstone Project" ),
            ("Senior Thesis", "Senior Thesis")
            #("Other", "Other")
        ]

        defense_result_choices = [
            ("-", "Pending"), 
            ("Accepted", "Accepted"), 
            ("Accepted with Revisions", "Accepted with Revisions"), 
            ("Re-defense", "Re-Defense"), 
            ("Not Accepted", "Not Accepted"), 
        ]

        fields =   ('title', 'project_type', 'proponents', 'adviser',
            'description', 'panel', 'comments') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Adviser', 
            'description': 'Executive Summary',
            'panel':'Panel', 
           # 'defense_date':'YYYY-MM-DD HH:MM:SS',
           'comments': 'Faculty Comments',
        }

        help_texts = {
            'panel': 'Hold "Ctrl" button to select multiple panelists',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel', 'size': '10'}), 
             #'defense_date': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Defense Date'}),
            'comments': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Enter Project Comments'}),
        }   

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

        # Make fields read-only by disabling them
        self.fields['title'].widget.attrs['disabled'] = 'disabled'
        self.fields['project_type'].widget.attrs['disabled'] = 'disabled'
        self.fields['proponents'].widget.attrs['disabled'] = 'disabled'
        self.fields['adviser'].widget.attrs['disabled'] = 'disabled'
        self.fields['description'].widget.attrs['disabled'] = 'disabled'

        # Pre-select the initial panelist and restrict panel selection
        self.pre_selected_panelist = self.instance.panel.all()[:1]  # Select the first panelist only
        self.fields['panel'].initial = [panelist.id for panelist in self.pre_selected_panelist]  # Use IDs
        self.fields['panel'].queryset = self.fields['panel'].queryset.exclude(id=self.instance.adviser.id)

    def clean_panel(self):
        panelists = self.cleaned_data.get('panel')
        errors = []

        # Ensure the pre-selected panelist is always included
        missing_panelists = [panelist for panelist in self.pre_selected_panelist if panelist not in panelists]
        if missing_panelists:
            missing_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in missing_panelists)  # Assuming 'name' is the attribute
            errors.append(f"The selected panelist(s) of students; {missing_names}, must remain selected.")

        # Allow up to 2 additional panelists if no pre-selected panelists exist
        if not self.pre_selected_panelist:
            # Remove pre-selection if no panelists are selected
            self.fields['panel'].initial = []  # Clear pre-selection
            if len(panelists) > 2:
                errors.append("You can only select up to 2 panelists.")
        else:
            # Allow only one additional panelist beyond the pre-selected one
            additional_panelists = panelists.exclude(id__in=[p.id for p in self.pre_selected_panelist])
            if len(additional_panelists) > 1:
                pre_selected_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in self.pre_selected_panelist)
                errors.append(f"You can only select one additional panelist in addition to the selected panelist(s) of students: {pre_selected_names}.")
            
         # Add errors to the form if there are any
        if errors:
            for error in errors:
                self.add_error('panel', error)
            # Return None so that the form is marked invalid but not break with an exception
            return None
        
        return panelists
    
class CoordinatorSelectPanelistForm(ModelForm): 
    # meta allows to sort of define things in a class
    class Meta: 
        model = Project
     
        fields =   ('title', 'project_type', 'proponents', 'adviser',
            'description', 'panel', 'comments') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Adviser', 
            'description': 'Executive Summary',
            'panel':'Panel', 
           # 'defense_date':'YYYY-MM-DD HH:MM:SS',
           'comments': 'Faculty Comments',
        }

        help_texts = {
            'panel': 'Hold "Ctrl" button to select multiple panelists',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=[
                ("Capstone Project", "Capstone Project"),
                ("Senior Thesis", "Senior Thesis")
            ], attrs={'class': 'form-select'}),
            'proponents': forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel', 'size': '10'}), 
             #'defense_date': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Defense Date'}),
            'comments': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Enter Project Comments'}),
        }   

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

        # Make fields read-only by disabling them
        for field_name in ['title', 'project_type', 'proponents', 'adviser', 'description']:
            self.fields[field_name].widget.attrs['disabled'] = 'disabled'


        # Pre-select the initial panelist and restrict panel selection
        self.pre_selected_panelist = self.instance.panel.all()[:2]  # Select the first panelist only
        self.fields['panel'].initial = self.pre_selected_panelist
        self.fields['panel'].queryset = self.fields['panel'].queryset.exclude(id=self.instance.adviser.id)

    def clean_panel(self):
        panelists = self.cleaned_data.get('panel')
        errors = []

        # Ensure the pre-selected panelists are always included
        missing_panelists = [panelist for panelist in self.pre_selected_panelist if panelist not in panelists]
        if missing_panelists:
            missing_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in missing_panelists)
            pre_selected_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in self.pre_selected_panelist)
            errors.append(f"The selected panelists; {missing_names}, must remain selected. The two pre-selected panelists are: {pre_selected_names}.")

        # Allow only one additional panelist beyond the pre-selected ones
        additional_panelists = panelists.exclude(id__in=[p.id for p in self.pre_selected_panelist])
        if len(additional_panelists) > 1:
            pre_selected_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in self.pre_selected_panelist)
            errors.append(f"You can only select one additional panelist in addition to the pre-selected panelists: {pre_selected_names}.")

        # Add errors to the form if there are any
        if errors:
            for error in errors:
                self.add_error('panel', error)
            # Return None so that the form is marked invalid but not break with an exception
            return None

        return panelists

class AddCommentsForm(ModelForm): 
    # meta allows to sort of define things in a class
    class Meta: 
        model = Project
        project_type_choices = [ 
            ("Capstone Project", "Capstone Project" ),
            ("Senior Thesis", "Senior Thesis")
            #("Other", "Other")
        ]

        defense_result_choices = [
            ("-", "Pending"), 
            ("Accepted", "Accepted"), 
            ("Accepted with Revisions", "Accepted with Revisions"), 
            ("Re-defense", "Re-Defense"), 
            ("Not Accepted", "Not Accepted"), 
        ]

        fields =   ('title', 'project_type', 'proponents', 'adviser',
            'description', 'panel', 'comments') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Adviser', 
            'description': 'Executive Summary',
            'panel':'Panel', 
           # 'defense_date':'YYYY-MM-DD HH:MM:SS',
           'comments': 'Faculty Comments',
        }

        help_texts = {
            'panel': 'Hold "Ctrl" button to select multiple panelists',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel', 'size': '10'}), 
             #'defense_date': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Defense Date'}),
            'comments': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Enter Project Comments'}),
        }   

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap class to help text
        for field in self.fields.values():
            if field.help_text:
                field.help_text = f'<small class="form-text text-muted">{field.help_text}</small>'

        # Make fields read-only by disabling them
        self.fields['title'].widget.attrs['disabled'] = 'disabled'
        self.fields['project_type'].widget.attrs['disabled'] = 'disabled'
        self.fields['proponents'].widget.attrs['disabled'] = 'disabled'
        self.fields['adviser'].widget.attrs['disabled'] = 'disabled'
        self.fields['description'].widget.attrs['disabled'] = 'disabled'
        self.fields['panel'].widget.attrs['disabled'] = 'disabled'  # Disable the panel field


        # Pre-select the initial panelist and restrict panel selection
        self.pre_selected_panelist = self.instance.panel.all()[:1]  # Select the first panelist only
        self.fields['panel'].initial = self.pre_selected_panelist
        self.fields['panel'].queryset = self.fields['panel'].queryset.exclude(id=self.instance.adviser.id)

    def clean_panel(self):
        panelists = self.cleaned_data.get('panel')
        errors = []

        # Ensure the pre-selected panelist is always included
        missing_panelists = [panelist for panelist in self.pre_selected_panelist if panelist not in panelists]
        if missing_panelists:
            missing_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in missing_panelists)  # Assuming 'name' is the attribute
            errors.append(f"The selected panelist(s) of students; {missing_names}, must remain selected.")

        # Allow only one additional panelist beyond the pre-selected one
        additional_panelists = panelists.exclude(id__in=[p.id for p in self.pre_selected_panelist])
        if len(additional_panelists) > 1:
            pre_selected_names = ', '.join(f"{panelist.first_name} {panelist.last_name}" for panelist in self.pre_selected_panelist)
            errors.append(f"You can only select one additional panelist in addition to the selected panelist(s) of students: {pre_selected_names}.")
        
         # Add errors to the form if there are any
        if errors:
            for error in errors:
                self.add_error('panel', error)
            # Return None so that the form is marked invalid but not break with an exception
            return None
        
        return panelists
    

# Allows users to add custom phases
# class CustomPhaseForm(forms.ModelForm):
#     class Meta:
#         model = CustomPhase
#         fields = ['phase_name', 'phase_order']