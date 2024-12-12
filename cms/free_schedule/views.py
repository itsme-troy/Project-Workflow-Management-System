
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Available_schedule
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from django.utils.timezone import localtime  

from datetime import datetime
from pytz import timezone  
import pytz
local_tz = pytz.timezone('Asia/Manila')

import logging

logger = logging.getLogger(__name__)
from django.utils.timezone import make_aware, localtime
# from django.utils import timezone



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

def convert_to_utc(date_str):
    try:
        local_timezone = timezone('Asia/Manila')  # Correct usage of pytz.timezone
        local_time = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')  # Parse input format
        local_time = local_timezone.localize(local_time)  # Add timezone info
        return local_time.astimezone(pytz.utc)  # Convert to UTC
    except Exception as e:
        raise ValueError(f"Invalid date format: {e}")

def to_local(utc_time):
    try:
        manila_timezone = timezone('Asia/Manila')  # Correct usage of pytz.timezone
        return utc_time.astimezone(manila_timezone)
    except Exception as e:
        raise ValueError(f"Error converting time to local: {e}")

def free_sched(request): # index 
    if not request.user.is_authenticated: 
        messages.error(request, "Please login to view this page")
        return redirect('login')    
    
    all_events = Available_schedule.objects.filter(faculty=request.user.id).order_by('-start')  # Order by start time descending
    return render(request, 'free_schedule/free_schedule.html', {
        "events": all_events,
    })

def all_sched(request): # still return 
    all_events = Available_schedule.objects.filter(faculty=request.user.id)
    out = []
    for event in all_events:
         # Convert start and end to Asia/Manila timezone before sending to the frontend
        start_local = to_local(event.start)
        end_local = to_local(event.end)

        out.append({
            'id': event.id,
            'title': event.title,
            'start': start_local.isoformat(),
            'end': end_local.isoformat(),
        })
    
   # Log the output for debugging
    logger.debug("Returning events: " + json.dumps(out, indent=4))  
    return JsonResponse(out, safe=False)

def add_sched(request):
    title = request.GET.get("title")
    start = request.GET.get("start")
    end = request.GET.get("end")
    
    
    logger.debug(f"Received data: title={title}, start={start}, end={end}")

    if not start or not end or not title:
        return JsonResponse({'error': 'Missing required fields: start, end, or title'}, status=400)

    try:
         # Make sure the date format matches '%Y-%m-%dT%H:%M:%S' (the format used in ISO strings)
        start_datetime = datetime.fromisoformat(start).astimezone(pytz.utc)
        end_datetime = datetime.fromisoformat(end).astimezone(pytz.utc)
        # start_datetime = convert_to_utc(start)
        # end_datetime = convert_to_utc(end)

        logger.debug(f"Converted times: start={start_datetime}, end={end_datetime}")

        # Ensure end time is after start time
        if end_datetime <= start_datetime:
            logger.error("End time must be after start time")
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

        event = Available_schedule(
            title=title,
            start=start_datetime,
            end=end_datetime,
            faculty=request.user
        )
        event.save()

        logger.info(f"Event saved: {event.id}")
        return JsonResponse({'message': 'Event added successfully'}, status=200)
    
    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': f"Unexpected error: {e}"}, status=500)
    
def update_sched(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    title = request.GET.get("title")
    event_id = request.GET.get("id")
    
    try:
        start_datetime = datetime.fromisoformat(start).astimezone(pytz.utc)
        end_datetime = datetime.fromisoformat(end).astimezone(pytz.utc)

        event = Available_schedule.objects.get(id=event_id)
        event.start = start_datetime
        event.end = end_datetime
        event.title = title
        event.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Schedule updated successfully',
            'id': event.id,
            'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
        })
    except Available_schedule.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Event not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
 
def remove_sched(request):
    if request.method == 'GET':
        id = request.GET.get("id", None)
        try:
            event = Available_schedule.objects.get(id=id)
            print(f"Deleting event: {event}")  # Debug print to ensure the event is found
            event.delete()
            return JsonResponse({'status': 'success', 'message': 'Event removed successfully'})
        except Available_schedule.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def delete_all_schedules(request):
    if request.method == 'POST':
        try:
            # Delete all schedules for the logged-in user
            Available_schedule.objects.filter(faculty=request.user).delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@csrf_exempt
def create_schedule(request):
    if request.method == 'POST' and request.user.is_authenticated:
        start = request.POST.get('start')
        end = request.POST.get('end')

        if not start or not end:
            return JsonResponse({'error': 'Missing required fields: start, end, or title'}, status=400)

        start_datetime = datetime.fromisoformat(start).astimezone(pytz.utc)
        end_datetime = datetime.fromisoformat(end).astimezone(pytz.utc)
        
         # Ensure end time is after start time
        if end_datetime <= start_datetime:
            logger.error("End time must be after start time")
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

        # Validate inputs and create a schedule
        if start and end:
            try:
                schedule = Available_schedule.objects.create(faculty=request.user, start=start_datetime, end=end_datetime)
                return JsonResponse({'status': 'success', 'schedule_id': schedule.id})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Invalid inputs'})
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)