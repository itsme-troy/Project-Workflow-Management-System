from django import forms 
from django.forms import ModelForm 
from .models import Project, Defense_Application, Project_Group, StudentProfile, Student

class ProjectGroupForm(ModelForm): 
    class Meta: 
        model = Project_Group
        fields = ['group_name', 'adviser', 'proponents'] 
        
        labels = { 
            'group_name':'Group Name',
            'adviser': 'Adviser',
            'proponents': 'Proponents', 
        }
        widgets = { 
            'group_name': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Enter name of the Group'}),
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Select Adviser'}), 
            'proponents': forms.SelectMultiple(attrs={'class':'form-select', 'placeholder': 'Select Proponents'}), 
            }
        
class CapstoneSubmissionForm(ModelForm): 
    class Meta: 

        type_of_defense = [ 
            ("Topic Defense", "Topic Defense" ),
            ("Design Defense", "Design Defense"),
            ("Preliminary Defense", "Preliminary Defense"),
            ("Final Defense", "Final Defense")
        ]

        model = Defense_Application
        fields = ['title', 'project', 'project_group', 'adviser', 'panel','document' ]
        
        labels = { 
            'title':'Type of Defense',
            'project': 'Project',
            'project_group': 'Project Group',
            'adviser':'Adviser ', 
            'panel': 'Panel',
            'document': 'Manuscript',
        }
        widgets = { 
            'title': forms.Select(choices=type_of_defense, attrs={'class':'form-select', 'placeholder': 'Select Type of Defense'}), 
            'project': forms.Select(attrs={'class':'form-select', 'placeholder': 'Enter'}), 
            'project_group' : forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}),
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Panel'}),  
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel'}), 
            'document': forms.FileInput(attrs={'class':'form-control', 'placeholder': 'Title'}),
            #'document'
        }
        
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
            'panel', 'description') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Adviser', 
            'panel':'Panel', 
            'description': 'Executive Summary',
             # 'defense_date':'YYYY-MM-DD HH:MM:SS',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-control', 'placeholder': 'Panel'}), 
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
            #'defense_date': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Defense Date'}),
        }

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
            'panel', 'description', 'proposal_defense', 'design_defense',
            'preliminary_defense', 'final_defense') 
    
        labels = { 
            'title':'Title',
            'project_type': 'Project Type',
            'proponents':'Proponents',
            'adviser':'Adviser', 
            'panel':'Panel', 
            'description': 'Executive Summary',
            'proposal_defense':'Proposal Defense', 
            'design_defense': 'Design Defense', 
            'preliminary_defense': 'Preliminary Defense',  
            'final_defense': 'Final Defense', 
            # 'defense_date':'YYYY-MM-DD HH:MM:SS',
        }
        widgets = { 
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Project Title'}),
            'project_type': forms.Select(choices=project_type_choices, attrs={'class':'form-select'}), 
            'proponents': forms.Select(attrs={'class':'form-select', 'placeholder': 'Proponents'}), 
            'adviser': forms.Select(attrs={'class':'form-select', 'placeholder': 'Adviser'}),
            'panel': forms.SelectMultiple(attrs={'class':'form-select', 'placeholder': 'Panel'}), 
            'description': forms.Textarea(attrs={'class':'form-control', 'placeholder': 'Project Description'}),
            'proposal_defense': forms.Select(choices=defense_result_choices,  attrs={'class':'form-select'}),
            'design_defense': forms.Select(choices=defense_result_choices,  attrs={'class':'form-select'}),
            'preliminary_defense':  forms.Select(choices=defense_result_choices,  attrs={'class':'form-select'}),
            'final_defense': forms.Select(choices=defense_result_choices,  attrs={'class':'form-select'}),
             #'defense_date': forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Defense Date'}),
}
