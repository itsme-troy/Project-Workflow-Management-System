from django import forms 
from django.forms import ModelForm 
from .models import Project, Defense_Application, Project_Group, StudentProfile, Student
from .models import Faculty, ProjectPhase
from django.core.exceptions import ValidationError

class ProjectGroupInviteForm(ModelForm):
    class Meta:
        model = Project_Group
        fields = ['proponents']
        
        labels = {
            'proponents': 'Select Additional Members: hold "ctrl" button to select multiple',
        }
        widgets = {
            'proponents': forms.SelectMultiple(attrs={'class': 'form-select', 'placeholder': 'Select Proponents'}),
        }
        
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)  # Get the existing group
        super(ProjectGroupInviteForm, self).__init__(*args, **kwargs)

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

             # If the group already has 3 members (pending + approved), disable new selections
            if len(existing_members) >= 3:
                self.fields['proponents'].widget.attrs['disabled'] = 'disabled'
                self.fields['proponents'].help_text = 'Maximum group size (3) reached'

            # Set the queryset to exclude existing members and users in approved groups
            self.fields['proponents'].queryset = (
                Student.objects.filter(role='STUDENT')
                .exclude(id__in=existing_member_ids)
                .exclude(id__in=users_in_approved_groups)
            )

            # Pre-select existing members and make them unselectable in the frontend
            self.fields['proponents'].initial = existing_member_ids
            
            # Add data attributes for JavaScript to handle disabled selections
            self.fields['proponents'].widget.attrs['data-existing-members'] = ','.join(map(str, existing_member_ids))

    def clean_proponents(self):
        proponents = self.cleaned_data.get('proponents')
        group = getattr(self, 'group', None)

        if group:
             # Get existing members (both pending and approved)
            existing_members = list(group.pending_proponents.all()) + list(group.proponents.all())
            
            # Calculate how many new members can be added
            available_slots = 3 - len(existing_members)
            
            if available_slots <= 0 and proponents:
                raise ValidationError('The group already has the maximum number of members (3).')
            
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
            'proponents': forms.SelectMultiple(attrs={'class': 'form-select', 'placeholder': 'Select Proponents'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Retrieve the logged-in user from the view
        approved_users = kwargs.pop('approved_users', [])  # List of users with approved project groups
        super(ProjectGroupForm, self).__init__(*args, **kwargs)

        if user:
            # Ensure user is cast to the actual user object if it's a SimpleLazyObject
            if hasattr(user, '_wrapped') and isinstance(user._wrapped, object):
                user = user._wrapped

            # Pre-select the logged-in user's ID in the proponents field
            if 'proponents' in self.fields:
                initial_proponents = self.initial.get('proponents', [])  # Get initial proponents
                self.initial['proponents'] = [user.id] + list(initial_proponents)  # Pre-select logged-in user's ID

             # Adjust the queryset to exclude users with approved project groups
            self.fields['proponents'].queryset = self.fields['proponents'].queryset.exclude(id__in=approved_users)

            # Adjust the queryset to include the logged-in user but prevent them from being deselected
            self.fields['proponents'].queryset = self.fields['proponents'].queryset.exclude(id=user.id) | self.fields['proponents'].queryset.filter(id=user.id)
            self.fields['proponents'].widget.attrs['data-logged-in-user'] = str(user.id)  # Tag for the front-end to know the user

    def clean_proponents(self):
        proponents = self.cleaned_data.get('proponents')

        # Get the logged-in user's ID from the initial data
        user_id = self.initial.get('proponents', [None])[0]  # Get the first proponent's ID or None if not set

        # Ensure the logged-in user (by ID) is always part of the proponents
        if user_id and user_id not in [proponent.id for proponent in proponents]:
            proponents = list(proponents)  # Convert to a list if necessary
            # Add the logged-in user back to the proponents list
            proponents.append(self.fields['proponents'].queryset.get(id=user_id))

        # Limit proponents to 3 (including the logged-in user)
        if len(proponents) > 3:
            raise ValidationError('You can only select up to 3 proponents, including yourself.')

        return proponents

class VerdictForm(forms.ModelForm):
    class Meta:
        model = ProjectPhase
        fields = ['verdict']  # status stores the verdict
        widgets = {
            'verdict': forms.Select(choices=ProjectPhase.RESULT_CHOICES, attrs={'class': 'form-select'}),
        }

class CapstoneSubmissionForm(ModelForm):
    class Meta:
        model = Defense_Application
        fields = ['title', 'project', 'project_group', 'adviser', 'panel', 'document']
        
        labels = {
            'title': 'Type of Defense',
            'project': 'Project',
            'project_group': 'Project Group',
            'adviser': 'Adviser',
            'panel': 'Panel',
            'document': 'Manuscript',
        }

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Select Type of Defense'}),
            'project': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Enter'}),
            'project_group': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Proponents'}),
            'adviser': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Panel'}),
            'panel': forms.SelectMultiple(attrs={'class': 'form-control', 'placeholder': 'Panel'}),
            'document': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disable fields
        self.fields['project_group'].widget.attrs['disabled'] = 'disabled'
        self.fields['adviser'].widget.attrs['disabled'] = 'disabled'
        self.fields['project'].widget.attrs['disabled'] = 'disabled'
        self.fields['panel'].widget.attrs['disabled'] = 'disabled'
        self.fields['title'].widget.attrs['readonly'] = 'readonly'

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
            
            # Auto-set the title (phase) based on the last completed phase
            # last_phase = project.phases.order_by('-date').first()
            # next_phase_type = 'Proposal Defense'  # Default for new projects

            # if last_phase:
            #     if last_phase.phase_type == 'proposal' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
            #         next_phase_type = 'Design Defense'
            #     elif last_phase.phase_type == 'design' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
            #         next_phase_type = 'Preliminary Defense'
            #     elif last_phase.phase_type == 'preliminary' and last_phase.verdict in ['accepted', 'accepted_with_revisions']:
            #         next_phase_type = 'Final Defense'
            #     elif last_phase.verdict == 'redefense':
            #         next_phase_type = last_phase.get_phase_type_display()  # Repeat current phase

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
            'adviser':'Adviser', 
            'panel':'Panel', 
            'description': 'Executive Summary',
            'comments': 'Faculty Comments'
             # 'defense_date':'YYYY-MM-DD HH:MM:SS',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-control', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel'}), 
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
            'comments': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Comments'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProjectForm, self).__init__(*args, **kwargs)

        # Disable the proponents field
        self.fields['proponents'].widget.attrs['disabled'] = 'disabled'

        # Hide the comments field if the user is a student
        if user and user.role == 'STUDENT':
            self.fields.pop('comments', None)

    def clean(self):
        cleaned_data = super().clean()
        adviser = cleaned_data.get('adviser')
        panel = cleaned_data.get('panel')

        if adviser and panel:
            # Check if adviser is in panel
            if adviser in panel:
                raise ValidationError('The adviser cannot be one of the panelists.')

            # If user is a student, enforce single selection
            if len(panel) > 1:
                raise ValidationError( 'Students can select only one panelist.')

        return cleaned_data
    
class UpdateProjectForm(ModelForm): 
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
            'panel', 'description', 'comments') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Adviser', 
            'panel':'Panel', 
            'description': 'Executive Summary',
           # 'defense_date':'YYYY-MM-DD HH:MM:SS',
           'comments': 'Faculty Comments',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-select', 'placeholder': 'Panel'}), 
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
             #'defense_date': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Defense Date'}),
            'comments': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Enter Project Comments'}),
        }   

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields read-only by disabling them
        self.fields['title'].widget.attrs['disabled'] = 'disabled'
        self.fields['project_type'].widget.attrs['disabled'] = 'disabled'
        self.fields['proponents'].widget.attrs['disabled'] = 'disabled'
        self.fields['adviser'].widget.attrs['disabled'] = 'disabled'
        self.fields['description'].widget.attrs['disabled'] = 'disabled'

        # Pre-select the initial panelist and restrict panel selection
        self.pre_selected_panelist = self.instance.panel.all()[:1]  # Select the first panelist only
        self.fields['panel'].initial = self.pre_selected_panelist
        self.fields['panel'].queryset = self.fields['panel'].queryset.exclude(id=self.instance.adviser.id)

    def clean_panel(self):
        panelists = self.cleaned_data.get('panel')
        errors = []

        # Ensure the pre-selected panelist is always included
        if not all(panelist in panelists for panelist in self.pre_selected_panelist):
            errors.append("The selected panelist of Students must remain selected.")
        
        # Allow only one additional panelist beyond the pre-selected one
        additional_panelists = panelists.exclude(id__in=[p.id for p in self.pre_selected_panelist])
        if len(additional_panelists) > 1:
            errors.append("You can only select one additional panelist.")
        
         # Add errors to the form if there are any
        if errors:
            for error in errors:
                self.add_error('panel', error)
            # Return None so that the form is marked invalid but not break with an exception
            return None
        
        return panelists