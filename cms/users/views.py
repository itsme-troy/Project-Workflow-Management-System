from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages 
from django.contrib.auth.forms import UserCreationForm
from .forms import RegisterFacultyForm, RegisterStudentForm
from .forms import ProfilePicForm
from django.contrib.auth import get_user_model 

User = get_user_model()

def update_user(request): 
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        if current_user.role=="STUDENT":
            user_form = RegisterStudentForm(request.POST or None, request.FILES or None, instance=current_user)
            profile_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=current_user)
        else:
            user_form = RegisterFacultyForm(request.POST or None,  request.FILES or None, instance=current_user)
            profile_form = ProfilePicForm(request.POST or None, request.FILES or None, instance=current_user)
        if user_form.is_valid() and profile_form.is_valid: 
            user_form.save()
            profile_form.save()

            login(request, current_user)
            
            messages.success(request, ("Your Profile has been Successfully Updated! "))
            return redirect('home')
        return render(request, 'project/update_user.html', {
            "user_form": user_form, 
            "profile_form": profile_form
        })
    
    else: 
        messages.error(request, "Please login to view this page!")
        return redirect('home')

def register_faculty(request): 
    if request.method == "POST": 
        form = RegisterFacultyForm(request.POST)
        if form.is_valid(): 
            user = form.save(commit=False)
            user.role = "FACULTY"
            user.save()
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = authenticate(email=email, password=password)
            login(request, user)
            messages.success(request, ("Faculty Registration Successful!"))
            return redirect('home')
    else: 
        form = RegisterFacultyForm()

    # pass the form back to the page 
    return render(request, 'authenticate/register_faculty.html', {
        'form':form, 
        })

def register_student(request): 
    if request.method == "POST": 
        form = RegisterStudentForm(request.POST)
        if form.is_valid(): 
            user = form.save(commit=False)
            user.role = "STUDENT"
            user.save()
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = authenticate(email=email, password=password)
            login(request, user)
            messages.success(request, ("Student Registration Successful!"))
            return redirect('home')
    else: 
        form = RegisterStudentForm()

    # pass the form back to the page 
    return render(request, 'authenticate/register_student.html', {
        'form':form, 
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
    if request.method == "POST": 
        email = request.POST["email"]
        password = request.POST["password"]
        
        # Check if the user exists in the database
        if not User.objects.filter(email=email).exists():
            messages.error(request, "User not registered. Please sign up first.")
            return redirect('login')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "There was an error logging in. Please try again.")
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

