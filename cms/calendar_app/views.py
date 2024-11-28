from django.shortcuts import render
from django.contrib import messages
from .models import Event
from django.http import JsonResponse
from project.models import ApprovedProject
from project.models import Defense_Application
from .forms import EventForm
from django.http import JsonResponse
from django.shortcuts import render, redirect

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.

from .models import Event

def show_calendar(request): # index 
    if request.user.is_authenticated: 
    
        all_events = Event.objects.all()
        defense_applications = Defense_Application.objects.all() 
        
        return render(request, 'calendar_app/show_calendar.html', {
            "events": all_events,
            "applications": defense_applications, 
        })
    else:
        messages.success(request, "Please Login to view this Page.")
        return redirect('home')

def all_events(request):         
    all_events = Event.objects.all()                                                                   
    out = []                 
    # event  >> defense_application(project) >> approved_project 

    for event in all_events:    
         # We serialize the related Defense_Application object
        # problem is
        defense_application = event.defense_application 
        project = defense_application.project
       
          # Append the event data with the serialized defense_application object                                                                                      
        out.append({         
            'id': event.id,       
            'title':project.title,    
            'defense_application': {
                'id': defense_application.id,
                'project': {
                    'id': project.id,
                    'title': project.title,  # Ensure title is here as well
                }
            },                                                 
            'start': event.start.strftime("%m/%d/%Y, %H:%M:%S") if event.start else 'N/A',                                                        
            'end': event.end.strftime("%m/%d/%Y, %H:%M:%S") if event.end else 'N/A',                                                              
            
        })                                                                                                                                                                                                                                
    return JsonResponse(out, safe=False) 
 
def add_event(request):

            if request.method == 'POST':
                form = EventForm(request.POST)
                if form.is_valid():
                    form.save()
                    return JsonResponse({'success': True})
                return JsonResponse({'success': False, 'errors': form.errors})
            return JsonResponse({'success': False})

def update(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)
    id = request.GET.get("id", None)
    event = Event.objects.get(id=id)
    event.start = start
    event.end = end
    event.title = title
    event.save()
    data = {}
    return JsonResponse(data)
 
def remove(request):
    id = request.GET.get("id", None)
    event = Event.objects.get(id=id)
    event.delete()
    data = {}
    return JsonResponse(data)