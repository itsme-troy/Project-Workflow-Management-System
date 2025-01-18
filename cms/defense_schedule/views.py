from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Defense_schedule
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.timezone import localtime  
from project.models import Defense_Application, Notification 
from django.urls import reverse

from datetime import datetime
from pytz import timezone  
import pytz
local_tz = pytz.timezone('Asia/Manila')

import logging

from project.models import ProjectPhase
from django.db.models import Subquery, OuterRef, Max, Q, F

logger = logging.getLogger(__name__)
from django.utils.timezone import make_aware, localtime
# from django.utils import timezone

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


# Create your views here.
def defense_sched(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please login to view this page")
        return redirect('login')    
    
    # Pass Defense Applications to the modal
    # Subquery to fetch the latest submission date per project
    latest_application_date_subquery = Defense_Application.objects.filter(
        project=OuterRef('project')
    ).order_by('-submission_date').values('submission_date')[:1]

    # Filter for the latest defense application per project with date comparison
    defense_applications = Defense_Application.objects.annotate(
        latest_application_date=Subquery(latest_application_date_subquery)
    ).filter(submission_date=F('latest_application_date')).prefetch_related('panel').all()

    # Check for 'pending' verdict in the latest phase
    latest_phase_subquery = ProjectPhase.objects.filter(
        project=OuterRef('project')
    ).order_by('-date').values('verdict')[:1]

    defense_applications = defense_applications.annotate(
        latest_verdict=Subquery(latest_phase_subquery)
    ).filter(latest_verdict='pending')

    all_events = Defense_schedule.objects.all().order_by('-created_at')   # Order by start time descending
    return render(request, 'defense_schedule/defense_schedule.html', {
        "events": all_events,
        "defense_applications": defense_applications,
    })

def view_defense_schedule(request): 
    if not request.user.is_authenticated: 
        messages.error(request, "Please login to view this page")
        return redirect('login')   

    all_events = Defense_schedule.objects.all().order_by('start')   # Order by start time descending
    return render(request, 'defense_schedule/schedule_table.html', {
        "events": all_events,
    }) 


def all_sched(request): # still return 
    all_events = Defense_schedule.objects.all().order_by('-created_at') 
    out = []
    for event in all_events:
         # Convert start and end to Asia/Manila timezone before sending to the frontend
        start_local = to_local(event.start)
        end_local = to_local(event.end)

        out.append({
            'id': event.id,
            # 'title': event.title,
            'start': start_local.isoformat(),
            'end': end_local.isoformat(),
            'color': event.color, 
            'application': event.application.project.title if event.application else None,
        })
    
   # Log the output for debugging
    logger.debug("Returning events: " + json.dumps(out, indent=4))  
    return JsonResponse(out, safe=False)

def add_sched(request):
    # title = request.GET.get("title")
    start = request.GET.get("start")
    end = request.GET.get("end")
    color = request.GET.get("color", None)
    application_id = request.GET("application")
    # all_day = request.GET.get("allDay", "false") == "true"
    # logger.debug(f"Received data: title={title}, start={start}, end={end}")

    if not start or not end or not application_id: 
        return JsonResponse({'error': 'Missing required fields: start, end, or title'}, status=400)

    try:
        application = Defense_Application.objects.get(id=application_id)  # Fetch application
        # Make sure the date format matches '%Y-%m-%dT%H:%M:%S' (the format used in ISO strings)
        start_datetime = datetime.fromisoformat(start).astimezone(pytz.utc)
        end_datetime = datetime.fromisoformat(end).astimezone(pytz.utc)
        # start_datetime = convert_to_utc(start)
        # end_datetime = convert_to_utc(end)

        # logger.debug(f"Converted times: start={start_datetime}, end={end_datetime}")

        # Ensure end time is after start time
        if end_datetime <= start_datetime:
            logger.error("End time must be after start time")
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

         # Fetch existing colors for the user
        existing_colors = list(
            Defense_schedule.objects.all().values_list('color', flat=True)
        )

        # Default color palette
        default_colors = [
            '#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#F3FF33', '#33FFF6', '#A333FF'
        ]

        # Assign the first unused color from the palette
        if not color:
            color = next((c for c in default_colors if c not in existing_colors), '#007BFF')

        # Save the new event   
        event = Defense_schedule(
            # title=title,
            start=start_datetime,
            end=end_datetime,
            application = application,
            # faculty=request.user,
            color = color, 
            # all_day=all_day,  # Save the allDay status
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
    event_id = request.GET.get("id")
    
    if not event_id:  # Validate event_id
        return JsonResponse({'status': 'error', 'message': 'Missing event ID'}, status=400)
    
    try:
        start_datetime = datetime.fromisoformat(start).astimezone(pytz.utc)
        end_datetime = datetime.fromisoformat(end).astimezone(pytz.utc)
        event = Defense_schedule.objects.get(id=event_id)
        event.start = start_datetime
        event.end = end_datetime
        # event.title = title
        event.save()

            # Notify all proponents about the schedule update
        application = event.application  # Get the associated application
        for proponent in application.project.proponents.proponents.all():
            Notification.objects.create(
                recipient=proponent,
                notification_type='SCHEDULE_UPDATED',
                group=application.project.proponents,
                sender=request.user,
                message=f"The defense schedule for the project '{application.project.title}' has been updated.",
                redirect_url=reverse('defense-schedule')
            )
        # Notify the adviser about the schedule update
        if application.project.adviser:
            Notification.objects.create(
                recipient=application.project.adviser,
                notification_type='SCHEDULE_UPDATED',
                group=application.project.proponents,
                sender=request.user,
                message=f"The defense schedule for the project '{application.project.title}' has been updated.",
                redirect_url=reverse('defense-schedule')
            )


        return JsonResponse({
            'status': 'success',
            'message': 'Schedule updated successfully',
            'id': event.id,
            # 'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
            'application': event.application, 
        })
    
    except Defense_schedule.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Event not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
 
def remove_sched(request):
    # pass
    if request.method == 'GET':
        id = request.GET.get("id", None)
        try:
            event = Defense_schedule.objects.get(id=id)
            print(f"Deleting event: {event}")  # Debug print to ensure the event is found
            event.delete()
            return JsonResponse({'status': 'success', 'message': 'Event removed successfully'})
        except Defense_schedule.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def delete_all_defense_schedules(request):
    if request.method == 'POST':
        try:
            schedules = Defense_schedule.objects.all()
            if not schedules.exists():
                return JsonResponse({'status': 'error', 'message': 'No schedules available to delete.'})
            
            # Delete all schedules
            schedules.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# @csrf_exempt
def create_defense_schedule(request):
    if not request.user.is_current_coordinator: 
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('defense-schedule')
      
    if request.method == 'POST' and request.user.is_authenticated:
        # Get form data
        start = request.POST.get('start')
        end = request.POST.get('end')
        color = request.POST.get('color', '#FFFFFF')  # Default to white if no color is selected
        application_id = request.POST.get('application')
        
        # Validate inputs
        if not start or not end or not application_id:
            return JsonResponse({'error': 'Missing required fields: start, end, or title'}, status=400)

         # Convert start and end times to aware datetime
        try:
            start_datetime = make_aware(datetime.fromisoformat(start))
            end_datetime = make_aware(datetime.fromisoformat(end))

            if end_datetime <= start_datetime:
                return JsonResponse({'status': 'error', 'message': 'End time must be after start time'}, status=400)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid datetime format'}, status=400)

         # Check if the Defense_Application exists
        try:
            application = Defense_Application.objects.get(id=application_id)
        except Defense_Application.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Defense Application selected'}, status=404)

        # Create the Defense Schedule
        try:
            schedule = Defense_schedule.objects.create(
                start=start_datetime,
                end=end_datetime,
                color=color,
                application=application
            )
             # Notify all proponents
            for proponent in application.project.proponents.proponents.all():
                Notification.objects.create(
                    recipient=proponent,
                    notification_type='SCHEDULE_CREATED',
                    group=application.project.proponents,
                    sender=request.user,
                    message=f"A new defense schedule has been created for the project '{application.project.title}'.",
                    redirect_url=reverse('defense-schedule')
                )
            # Notify the adviser
            if application.project.adviser:
                Notification.objects.create(
                    recipient=application.project.adviser,
                    notification_type='SCHEDULE_CREATED',
                    group=application.project.proponents,
                    sender=request.user,
                    message=f"A new defense schedule has been created for the project '{application.project.title}'.",
                    redirect_url=reverse('defense-schedule')
                )

            return JsonResponse({'status': 'success', 'schedule_id': schedule.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)


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