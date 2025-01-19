from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
# from django.contrib.auth.models import User 
from django.contrib.auth import get_user_model
User = get_user_model()

from django import forms 

class UpdateFacultyProfileForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)
    skills = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)  # Add skills field


    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'facebook_link', 'skills']

    def __init__(self, *args, **kwargs):
        # Extract the `user` argument from kwargs
        user = kwargs.pop('user', None)
        super(UpdateFacultyProfileForm, self).__init__(*args, **kwargs)
        
        # Add 'form-control' class to each field
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['bio'].widget.attrs.update({'class': 'form-control'})
        self.fields['facebook_link'].widget.attrs.update({'class': 'form-control'}) 
        self.fields['skills'].widget.attrs.update({'class': 'form-control'})  # Add class to skills field

         # Change label for the email field to 'Gbox'
        self.fields['email'].label = 'Gbox'
        
        # Change the label for 'skills' to 'Additional Information' if user is a coordinator
        if user and getattr(user, 'is_current_coordinator', False):
            self.fields['skills'].label = 'Additional Information'

class UpdateStudentProfileForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)
    skills = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)  # Add skills field

    class Meta:
        model = User
        fields = ['student_id','first_name', 'last_name', 'email', 'bio', 'facebook_link', 'skills']

    def __init__(self, *args, **kwargs):
        super(UpdateStudentProfileForm, self).__init__(*args, **kwargs)
        
        # Add 'form-control' class to each field    
        self.fields['student_id'].widget.attrs.update({'class': 'form-control'})  # Add class to student_id
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['bio'].widget.attrs.update({'class': 'form-control'})
        self.fields['facebook_link'].widget.attrs.update({'class': 'form-control'}) 
        self.fields['skills'].widget.attrs.update({'class': 'form-control'})  # Add class to skills field
      
         # Change label for the email field to 'Gbox'
        self.fields['email'].label = 'Gbox'

# Profile Extras Form
class ProfilePicForm(forms.ModelForm): 
    profile_image = forms.ImageField(label="Profile Picture", required=False)
    clear_profile_image = forms.BooleanField(required=False, label="Clear Profile Image", initial=False)

    class Meta: 
        model = User
        fields = ('profile_image', )

    def save(self, commit=True):
        instance = super(ProfilePicForm, self).save(commit=False)
        
        # If the 'Clear Profile Image' checkbox is checked, set the profile image to None
        if self.cleaned_data.get('clear_profile_image'):
            instance.profile_image = None
        
        if commit:
            instance.save()
        return instance



class RegisterStudentForm(UserCreationForm):

    course_choices = [
        ("BS Information Technology", "BS Information Technology"), 
        ("BS Computer Science", "BS Computer Science"), 
        ("BS Information Systems" , "BS Information Systems"), 
    ]
    labels = {
        'student_id': 'Student ID', 
    }

    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
    student_id = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
    course = forms.CharField(max_length=50, widget=forms.Select(choices=course_choices, attrs={'class':'form-select'}))
    
    class Meta: 
        model = User 
        fields = ('email', 'first_name', 'last_name', 'student_id', 'course',
            'password1', 'password2')
    
    # tell view use this form

    def __init__(self, *args, **kwargs): 
        super(RegisterStudentForm, self).__init__(*args, **kwargs)

        # designate other fields and add widgets to them 
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

        # Change label for the email field to 'Gbox'
        self.fields['email'].label = 'Gbox'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@gbox.adnu.edu.ph'):  # Replace 'gbox.domain' with the actual GBox domain
            raise ValidationError('Only GBox accounts are allowed.')
        return email

class RegisterFacultyForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))

    
    class Meta: 
        model = User 
        fields = ('email', 'first_name', 'last_name', 
            'password1', 'password2')

    def __init__(self, *args, **kwargs): 
        super(RegisterFacultyForm, self).__init__(*args, **kwargs)

        # designate other fields and add widgets to them 
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

        # Change label for the email field to 'Gbox'
        self.fields['email'].label = 'Gbox'
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@gbox.adnu.edu.ph'):  # only gbox accounts are allowed
            raise ValidationError('Only GBox accounts are allowed.')
        return email

        
 
# class RegisterUserForm(UserCreationForm):
#     email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
#     first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
#     last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
#     role = forms.Select(attrs={'class':'form-select', 'placeholder': 'Student'}),

#     class Meta: 
#         model = User 
#         fields = ('email', 'first_name', 'last_name', 
#             'password1', 'password2', 'role')
        
#         labels = {
#             'role': "Are you a Student or Faculty?"
#         }
        
#     # tell view use this form

#     def __init__(self, *args, **kwargs): 
#         super(RegisterUserForm, self).__init__(*args, **kwargs)

#         # designate other fields and add widgets to them 
#         self.fields['email'].widget.attrs['class'] = 'form-control'
#         self.fields['password1'].widget.attrs['class'] = 'form-control'
#         self.fields['password2'].widget.attrs['class'] = 'form-control'
        





