
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from free_schedule.models import Available_schedule
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
from project.models import Defense_Application 
from free_schedule.models import Available_schedule

from collections import defaultdict
import random
# from django.utils import timezone


FACULTY_COLOR_MAP = {}  # A global dictionary to map faculty to colors

def generate_random_color():
    """Generate a random hex color."""
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def get_faculty_color(faculty):
    """Retrieve or assign a color for a specific faculty."""
    if faculty.id not in FACULTY_COLOR_MAP:
        FACULTY_COLOR_MAP[faculty.id] = generate_random_color()
    return FACULTY_COLOR_MAP[faculty.id]


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

    # group events by faculty and pass them to template 
def manage_availability(request):
    if not request.user.is_authenticated: 
        messages.error(request, "Please login to view this page")
        return redirect('login')    

    # Retrieve all events ordered by faculty and start time
    all_events = Available_schedule.objects.all().select_related('faculty').order_by('faculty', 'start')
    
    # Group schedules by faculty with assigned colors
    grouped_events = {}
    faculty_colors = {}

    grouped_events = {}
    for event in all_events:
        faculty = event.faculty
        if faculty:
            if faculty not in grouped_events:
                grouped_events[faculty] = []
            grouped_events[faculty].append(event)
            
        
    return render(request, 'mutual_availability/view_schedules.html', {
        "grouped_events": grouped_events,
        "faculty_colors": faculty_colors,
    })

def all_sched(request):
    all_events = Available_schedule.objects.all().select_related('faculty').order_by('-created_at')
    out = []

    for event in all_events:
        start_local = to_local(event.start)
        end_local = to_local(event.end)

        # Retrieve the faculty's color from the model
        faculty = event.faculty
        faculty_color = faculty.color if faculty else '#007BFF'

        event_data = {
            'id': event.id,
            'start': start_local.isoformat(),
            'end': end_local.isoformat(),
            'color': faculty_color,
            'faculty': {
                'id': faculty.id if faculty else None,
                'first_name': faculty.first_name if faculty else "Unknown",
                'last_name': faculty.last_name if faculty else "Faculty",
            },
        }
        out.append(event_data)

    return JsonResponse(out, safe=False)

# def filter_schedules_by_defense(request):
#     defense_id = request.GET.get('defense')
#     defenses = Defense_Application.objects.all()

#     # Fetch schedules related to the selected defense application
#     if defense_id:
#         selected_defense = get_object_or_404(Defense_Application, id=defense_id)
#         schedules = Available_schedule.objects.filter(defense_application=selected_defense)  # Adjust field names
#     else:
#         schedules = Available_schedule.objects.none()  # Return no schedules if no defense is selected

#     context = {
#         'defenses': defenses,
#         'events': schedules,
#     }
#     return render(request, 'free_schedule/schedule_list.html', context)

# # def find_common_schedule 
# # def find_common_schedule(request): 
# #     schedules = Available_schedule.objects.all()  # or filter by some criteria
# #     common_slots = {}
# #     # Here, add logic to find overlapping time slots
# #     for schedule in schedules:
# #         start_time = schedule.start
# #         end_time = schedule.end

# #      # Assuming common_slots is a dictionary where keys are start times and values are lists of events
# #         if (start_time, end_time) in common_slots:
# #             common_slots[(start_time, end_time)].append(schedule)
        
# #         else:
# #             common_slots[(start_time, end_time)] = [schedule]

# #     # Prepare the response in the required format
# #     events = []
# #     for (start, end), schedules in common_slots.items():
# #         events.append({
# #             'title': 'Common Slot',
# #             'start': start.strftime("%Y-%m-%d %H:%M:%S"),
# #             'end': end.strftime("%Y-%m-%d %H:%M:%S"),
# #         })

# #     return JsonResponse(events, safe=False)

# def view_free_schedules(request): 
#     users = request.GET.getlist('users', [])  # List of user IDs
#     defense_application = request.GET.get('defense_application')  # ID of a defense application
    
#     schedules = Available_schedule.objects.all()

#     if users:
#         schedules = schedules.filter(faculty__id__in=users)
#     if defense_application:
#         schedules = schedules.filter(defense_application__id=defense_application)
    
#     context = {'schedules': schedules}
#     return render(request, 'free_schedule/view_schedules.html', context)

# def filter_schedules_by_defense(request):
#     defense_id = request.GET.get('defense')
#     defenses = Defense_Application.objects.all()

#     # Fetch schedules related to the selected defense application
#     if defense_id:
#         selected_defense = get_object_or_404(Defense_Application, id=defense_id)
#         schedules = Schedule.objects.filter(defense_application=selected_defense)  # Adjust field names
#     else:
#         schedules = Schedule.objects.none()  # Return no schedules if no defense is selected

#     context = {
#         'defenses': defenses,
#         'events': schedules,
#     }
#     return render(request, 'free_schedule/schedule_list.html', context)
