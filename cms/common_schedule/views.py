from django.shortcuts import render
from django.db.models import Q
from datetime import timedelta
from django.shortcuts import render
from django.contrib import messages
# from .models import Event

from django.http import JsonResponse
from free_schedule.models import Available_schedule, Faculty, Defense_Application
# Create your views here.
def find_common_times(schedules):
    # Sort schedules by start time
    sorted_schedules = sorted(schedules, key=lambda x: x.start)

    # Find overlapping schedules
    common_times = []
    for i in range(len(sorted_schedules) - 1):
        curr = sorted_schedules[i]
        next_sched = sorted_schedules[i + 1]

        # If the current schedule overlaps with the next one
        if curr.end > next_sched.start:
            common_start = max(curr.start, next_sched.start)
            common_end = min(curr.end, next_sched.end)
            common_times.append(Available_schedule(start=common_start, end=common_end))

    return common_times

def find_common_schedule(request):
    if request.method == 'POST':
        defense_application_id = request.POST.get('defense_application')
        
        # Get the selected defense application
        defense_application = Defense_Application.objects.get(id=defense_application_id)
        
        # Get the adviser (assuming Approved_Adviser is related to Faculty model)
        adviser = defense_application.adviser

        # Get all associated panelists
        panelists = defense_application.panel.all()

        # Combine adviser and panel schedules
        schedules = Available_schedule.objects.filter(
            Q(faculty=adviser.faculty) | Q(faculty__in=[panelist for panelist in panelists])
        )

        # Find the common availability by comparing schedules
        common_schedules = find_common_times(schedules)

        # Format the common schedules for FullCalendar
        formatted_schedules = [
            {
                'title': 'Common Available Time',
                'start': schedule.start.isoformat(),
                'end': schedule.end.isoformat(),
            }
            for schedule in common_schedules
        ]

        return JsonResponse({'success': True, 'common_schedules': formatted_schedules})

    return JsonResponse({'success': False})

def common_sched_calendar(request): # index 
    all_events = Available_schedule.objects.all()
    defense_applications = Defense_Application.objects.all() 
        
    return render(request, 'common_schedule/show_common_sched_calendar.html', {
        "events": all_events,
        "applications": defense_applications, 
    })

def all_events(request):                                                                                                 
    all_events = Available_schedule.objects.all()                                                                   
    out = []                                                                                                             
    for event in all_events:                                                                                             
        out.append({                                                                                                     
            'title': event.title,                                                                                         
            'id': event.id,                                                                                              
            'start': event.start.strftime("%m/%d/%Y, %H:%M:%S"),                                                         
            'end': event.end.strftime("%m/%d/%Y, %H:%M:%S"),                                                             
        })                                                                                                                                                                                                                                
    return JsonResponse(out, safe=False) 
 
# def add_event(request):
#     start = request.GET.get("start", None)
#     end = request.GET.get("end", None)
#     title = request.GET.get("title", None)
#     event = Event(title=str(title), start=start, end=end)
#     event.save()
#     data = {}
#     return JsonResponse(data)
