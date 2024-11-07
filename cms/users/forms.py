from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
# from django.contrib.auth.models import User 
from django.contrib.auth import get_user_model
User = get_user_model()

from django import forms 

# Profile Extras Form
class ProfilePicForm(forms.ModelForm): 
    profile_image = forms.ImageField(label="Profile Picture")

    class Meta: 
        model = User
        fields = ('profile_image', )

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
        





