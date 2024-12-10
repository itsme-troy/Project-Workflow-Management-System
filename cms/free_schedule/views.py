
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Available_schedule
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import localtime  # Add this import

from datetime import datetime
import pytz  # Make sure to install pytz if you haven't

# def find_common_schedule 
# def find_common_schedule(request): 
#     schedules = Available_schedule.objects.all()  # or filter by some criteria
#     common_slots = {}
#     # Here, add logic to find overlapping time slots
#     for schedule in schedules:
#         start_time = schedule.start
#         end_time = schedule.end

#      # Assuming common_slots is a dictionary where keys are start times and values are lists of events
#         if (start_time, end_time) in common_slots:
#             common_slots[(start_time, end_time)].append(schedule)
        
#         else:
#             common_slots[(start_time, end_time)] = [schedule]

#     # Prepare the response in the required format
#     events = []
#     for (start, end), schedules in common_slots.items():
#         events.append({
#             'title': 'Common Slot',
#             'start': start.strftime("%Y-%m-%d %H:%M:%S"),
#             'end': end.strftime("%Y-%m-%d %H:%M:%S"),
#         })

#     return JsonResponse(events, safe=False)

def free_sched(request): # index 
    if not request.user.is_authenticated: 
        messages.error(request, "Please login to view this page")
        return redirect('login')    
    
    all_events = Available_schedule.objects.filter(faculty=request.user.id).order_by('-start')  # Order by start time descending
    return render(request, 'free_schedule/free_schedule.html', {
        "events": all_events,
    })

def all_sched(request):                                                                                                 
    all_events = Available_schedule.objects.filter(faculty=request.user.id).order_by('-start')  # Order by start time descending                                                                
    out = []                                                                                                             
    for event in all_events:          
        # start_local = localtime(event.start)
        # end_local = localtime(event.end)                                                                                  
        out.append({
            'title': event.title,
            'id': event.id,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
        })                                                                                                                                                                                                                               
    return JsonResponse(out, safe=False) 
 

def add_sched(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)

    start_datetime = datetime.fromisoformat(start)
    end_datetime = datetime.fromisoformat(end)
    
    # Set the timezone to Asia/Manila
    local_tz = pytz.timezone('Asia/Manila')
    start_datetime = local_tz.localize(start_datetime)
    end_datetime = local_tz.localize(end_datetime)

    event = Available_schedule(title=str(title), start=start_datetime, end=end_datetime, faculty=request.user)
    event.save()
    
    # Return a success message or the created event data
    data = {
    #     'id': event.id,
    #     'title': event.title,
    #     'start': event.start.strftime("%b-%d,%Y %H:%M:%S"),  # Updated format to abbreviated month
    #     'end': event.end.strftime("%b-%d,%Y %H:%M:%S"),      # Updated format to abbreviated month
    }

    return JsonResponse(data)

def update_sched(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)
    id = request.GET.get("id", None)

    try:
        # Convert start and end to datetime objects using `datetime.fromisoformat` for consistency
        start_datetime = datetime.fromisoformat(start)
        end_datetime = datetime.fromisoformat(end)

        # Set the timezone to Asia/Manila
        local_tz = pytz.timezone('Asia/Manila')
        start_datetime = local_tz.localize(start_datetime)
        end_datetime = local_tz.localize(end_datetime)

        # Fetch the event from the database
        event = Available_schedule.objects.get(id=id)
        event.start = start_datetime
        event.end = end_datetime
        event.title = title
        event.save()

        # Return success response
        data = {
            'status': 'success',
            'message': 'Schedule updated successfully',
            'id': event.id,
            'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
        }
    except Available_schedule.DoesNotExist:
        data = {
            'status': 'error',
            'message': 'Event not found',
        }
    except Exception as e:
        data = {
            'status': 'error',
            'message': str(e),
        }

    return JsonResponse(data)
 
def remove_sched(request):
    id = request.GET.get("id", None)
    event = Available_schedule.objects.get(id=id)
    event.delete()
    data = {}
    return JsonResponse(data)

