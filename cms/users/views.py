from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages 
from django.contrib.auth.forms import UserCreationForm
from .forms import RegisterFacultyForm, RegisterStudentForm
from .forms import UpdateStudentProfileForm, UpdateFacultyProfileForm
from .forms import ProfilePicForm
from django.contrib.auth import get_user_model 
from django.http import HttpResponse

User = get_user_model()
import requests

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
import uuid
import logging
logger = logging.getLogger(__name__)
from django.utils.safestring import mark_safe
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage

from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .authentication import EmailVerifiedBackend

def validate_email_with_abstract_api(email):
    """
    Validate email using Abstract API.
    """
    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={settings.ABSTRACT_API_KEY}&email={email}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("is_valid_format", {}).get("value") and data.get("deliverability") == "DELIVERABLE":
            return True
    return False


def activate(request, uidb64, token):
    try:
        # Decode the UID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        return HttpResponse(f"Invalid activation link: {e}")

    # check the token 
    if user is not None and account_activation_token.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True  
        user.save()
        messages.success(request, "Account activated! You may now log in.")
        return redirect('login')
    else:
        return HttpResponse("Invalid activation link.")

def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account."
    message = render_to_string("authenticate/activate_account.html", {
        'user': user.first_name,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
       messages.success(request, mark_safe(
            f'Hello {user.first_name}, Please check your email (<b>{to_email}</b>) for the activation link. '
            f'Confirm your registration to proceed. <b>Check spam if needed.</b>'
        ))
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')

def register_student(request):
    if request.method == "POST":
        form = RegisterStudentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            # Double-check with API before finalizing registration
            if not validate_email_with_abstract_api(email):
                messages.error(request, "Email verification failed. Please enter a valid email.")
                return redirect('register_student')

            user = form.save(commit=False)
            user.role = "STUDENT"
            user.is_active = False  # Prevent login until verified
            user.save()
            activateEmail(request, user, email)  # Send verification email
            return redirect('home')
    else:
        form = RegisterStudentForm()

    return render(request, 'authenticate/register_student.html', {'form': form})

def register_faculty(request):
    if request.method == "POST":
        form = RegisterFacultyForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            # Double-check with API before finalizing registration
            if not validate_email_with_abstract_api(email):
                messages.error(request, "Email verification failed. Please enter a valid email.")
                return redirect('register_faculty')
            
            user = form.save(commit=False)
            user.role = "FACULTY"
            user.is_active=False
            user.save()
            activateEmail(request, user, email)
            return redirect('home')
       
    else:
        form = RegisterFacultyForm()

    return render(request, 'authenticate/register_faculty.html', {'form': form})


def update_user(request): 
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        if current_user.role=="STUDENT":
            user_form = UpdateStudentProfileForm(request.POST or None, request.FILES or None, instance=current_user)
            profile_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=current_user)
        else:
            user_form = UpdateFacultyProfileForm(
                request.POST or None,
                request.FILES or None, 
                instance=current_user,
                user=request.user, 
            )
            
            profile_form = ProfilePicForm(
                request.POST or None, 
                request.FILES or None, 
                instance=current_user
            )
        
        if user_form.is_valid() and profile_form.is_valid: 
            user_form.save()
            profile_form.save()

            login(request, current_user)
            
            messages.success(request, ("Your Profile has been Successfully Updated! "))
            return redirect('my-profile', profile_id=current_user.id)
        
        return render(request, 'project/update_user.html', {
            "user_form": user_form, 
            "profile_form": profile_form,
        })
    
    else: 
        messages.error(request, "Please login to view this page!")
        return redirect('home')

def select_registration(request): 
    return render(request, 'authenticate/select_registration.html', {
        })

# def register_user(request): 
#     if request.method == "POST": 
#         form = RegisterUserForm(request.POST)
#         if form.is_valid(): 
#             form.save()
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password1']
#             user = authenticate(email=email, password=password)
#             login(request, user)
#             messages.success(request, ("Registration Successful!"))
#             return redirect('home')
#     else: 
#         form = RegisterUserForm()

#     # pass the form back to the page 
#     return render(request, 'authenticate/register_user.html', {
#         'form':form, 
#         })

def login_user(request): 
    # If the user is already logged in, redirect them to the appropriate page
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        if request.user.role == "STUDENT": 
            return redirect('home-student')
        elif request.user.role == "FACULTY": 
            return redirect('home-faculty')
        elif request.user.is_current_coordinator:
            return redirect('coordinator-dashboard')
        else: 
            return redirect('home')
     # Or redirect to 'coordinator-dashboard' based on the user's role


    if request.method == "POST": 
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        
         # Check if the user exists in the database
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "User not registered. Please check your inputted details or sign up first.")
            return redirect('login')

        # Check if the user's email is verified
        if not user.is_email_verified:
            messages.error(
                request, 
                "Your email address is not verified. Please check your inbox and verify your email before logging in."
            )
            return redirect('login')

        # Authenticate the user
        user = authenticate(request, email=email, password=password)
    
        if user is not None:
            login(request, user)
            messages.success(request, f"Login Success! Welcome back, {user.first_name}!")

            if user.is_current_coordinator: 
                return redirect('coordinator-dashboard')
            elif user.role=='FACULTY': 
                return redirect('home-faculty')
            elif user.role=='STUDENT': 
                return redirect('home-student')
            else: 
                return redirect('home')
        
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect('login')

    else:
        return render(request, 'authenticate/login.html', {})

def logout_user(request): 
    logout(request)
    messages.success(request,"You Were Logged out!")
    return redirect('home')

# def register_user(request): 
#     if request.method == "POST": 
#         form = RegisterUserForm(request.POST)
#         if form.is_valid(): 
#             form.save()
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password1']
#             user = authenticate(username=username, password=password)
#             login(request, user)
#             messages.success(request, ("Registration Successful!"))
#             return redirect('home')
#     else: 
#         form = RegisterUserForm()

#     # pass the form back to the page 
#     return render(request, 'authenticate/register_user.html', {
#         'form':form, 
#         })

