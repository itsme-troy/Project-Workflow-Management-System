from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages 
from django.contrib.auth.forms import UserCreationForm
from .forms import RegisterFacultyForm, RegisterStudentForm
from .forms import UpdateStudentProfileForm, UpdateFacultyProfileForm
from .forms import ProfilePicForm
from django.contrib.auth import get_user_model 

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

ABSTRACT_API_KEY = "27979452bb704be3a9fcdcaf1d5ab7b6"

class EmailVerifiedBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Use email instead of username
        email = kwargs.get('email', username)  # Support both username and email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        # Check password
        if user.check_password(password):
            # Check if the user is active and verified
            if not user.is_email_verified:
                raise ValidationError("Your email address is not verified.")
            if not user.email.endswith('@gbox.adnu.edu.ph'):
                raise ValidationError("Only GBox accounts are allowed.")
            if not user.is_active:
                raise ValidationError("Your account is inactive.")
            return user
        return None

def verify_email(request, token):
    user_data = cache.get(token)
    if not user_data:
        messages.error(request, "The verification link is invalid or has expired.")
        return redirect('register_student')

    # Save the user to the database
    user = User(
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        email=user_data['email'],
        student_id=user_data['student_id'],
        course=user_data['course'],
        role=user_data['role'],
        is_email_verified=True,
        is_active=True,
    )
    user.set_password(user_data['password'])  # Hash the password
    user.save()

    # Clear the cache
    cache.delete(token)

    messages.success(request, "Your email has been verified successfully! You can now log in.")
    return redirect('login')


def send_verification_email(user):
    
    """ 
        Send a verification email with a unique token to the user's email address.
    """

    try:
        # Generate a unique verification token
        user.email_verification_token = str(uuid.uuid4())
        user.save()  # Save the token in the database


        # Print the token for debugging purposes
        print(f"Generated email verification token: {user.email_verification_token}")

        
        # Create the verification link
        verification_link = f"http://SeniorsProjectHub.com/verify-email/{user.email_verification_token}"
        subject = "Verify Your Email Address"
        message = (
            f"Hi {user.first_name},\n\n"
            f"Please click the link below to verify your email address:\n\n"
            f"{verification_link}\n\n"
            "Thank you!"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        logger.info(f"Sending email to: {recipient_list}, from: {from_email}")
        send_mail(subject, message, from_email, recipient_list)
        logger.info("Verification email sent successfully.")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise e
    

    
def validate_email_with_abstract_api(email):
    """
    Validate email using Abstract API.
    """
    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY}&email={email}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("is_valid_format").get("value") and data.get("deliverability") == "DELIVERABLE":
            return True
        else:
            return False
    return False


def register_faculty(request):
    if request.method == "POST":
        form = RegisterFacultyForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Validate email using Abstract API
            if not validate_email_with_abstract_api(email):
                messages.error(request, "Invalid email address. Please provide a valid GBox email.")
                return render(request, 'authenticate/register_faculty.html', {'form': form})
            
            user = form.save(commit=False)
            user.is_email_verified = False
            user.role = "FACULTY"
            user.save()
            
            # Send verification email
            try:
                send_verification_email(user)
                messages.success(
                    request, 
                    "Faculty Registration Successful! A verification email has been sent to your GBox email address. Please verify your email to activate your account."
                )
            except Exception as e:
                messages.error(request, "An error occurred while sending the verification email. Please try again later.")
                return render(request, 'authenticate/register_faculty.html', {'form': form})
            
            return redirect('home')
    else:
        form = RegisterFacultyForm()

    return render(request, 'authenticate/register_faculty.html', {'form': form})



def register_student(request):
    if request.method == "POST":
        form = RegisterStudentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Validate email using Abstract API
            try:
                if not validate_email_with_abstract_api(email):
                    messages.error(request, "Invalid GBox email. Please provide a valid GBox email.")
                    return render(request, 'authenticate/register_student.html', {'form': form})
            except Exception:
                messages.error(request, "An error occurred during email validation.")
                return render(request, 'authenticate/register_student.html', {'form': form})

            # Generate a unique token and store user data in cache
            token = str(uuid.uuid4())
            user_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': email,
                'student_id': form.cleaned_data['student_id'],
                'course': form.cleaned_data['course'],
                'password': form.cleaned_data['password1'],
                'role': 'STUDENT',
            }
            cache.set(token, user_data, timeout=3600)  # Cache user data for 1 hour

            # Send verification email
            try:
                verification_link = f"http://yourwebsite.com/verify-email/{token}/"
                send_mail(
                    subject="Verify Your Email Address",
                    message=f"Hi {form.cleaned_data['first_name']},\n\nPlease verify your email by clicking the following link:\n\n{verification_link}\n\nThank you!",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
                messages.success(
                    request,
                    "A verification email has been sent to your GBox email address. Please verify your email to complete registration."
                )
            except Exception:
                messages.error(request, "An error occurred while sending the verification email. Please try again.")
                return render(request, 'authenticate/register_student.html', {'form': form})

            return redirect('home')  # Redirect after submission
    else:
        form = RegisterStudentForm()

    return render(request, 'authenticate/register_student.html', {'form': form})


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
        email = request.POST["email"]
        password = request.POST["password"]
        
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

