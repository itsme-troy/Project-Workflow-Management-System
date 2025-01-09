
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from free_schedule.models import Available_schedule
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from project.models import Faculty, Project
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import localtime  
from django.db.models import Subquery, OuterRef, Max, Q, F
from datetime import datetime
from pytz import timezone  
import pytz
from datetime import timedelta
from defense_schedule.models import Defense_schedule
from project.models import ProjectPhase, Defense_Application, Notification 
from django.urls import reverse
local_tz = pytz.timezone('Asia/Manila')

import logging

logger = logging.getLogger(__name__)
from django.utils.timezone import make_aware, localtime
from project.models import Defense_Application 
from free_schedule.models import Available_schedule
from django.views.decorators.http import require_POST
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


def calculate_common_schedules(schedules):
    """
    Calculate common time ranges from a list of schedules.
    Each schedule contains a start and end datetime.
    Excludes schedules that do not overlap with others and ensures overlaps involve multiple faculty members.
    """
    if not schedules:
        return []

    # Step 1: Group schedules by date for processing day by day
    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedule_date = schedule.start.date()
        schedules_by_day[schedule_date].append(schedule)

    common_ranges = []

    # Step 2: Process schedules day by day
    for day, daily_schedules in schedules_by_day.items():
        # Create a list of (start, end, faculty) tuples
        time_ranges = [(schedule.start, schedule.end, schedule.faculty) for schedule in daily_schedules]
        time_ranges.sort(key=lambda x: x[0])  # Sort by start time

        ongoing_ranges = [(time_ranges[0][0], time_ranges[0][1], {time_ranges[0][2]})]  # Track start, end, and faculties

        for start, end, faculty in time_ranges[1:]:
            if start <= ongoing_ranges[-1][1]:  # Overlapping schedules
                # Update the last range's end time and add faculty
                ongoing_ranges[-1] = (
                    max(ongoing_ranges[-1][0], start),  # Update start of overlap
                    min(ongoing_ranges[-1][1], end),    # Update end of overlap
                    ongoing_ranges[-1][2] | {faculty}   # Add faculty to the set
                )
            else:
                # Add the last range to common_ranges if it involved multiple faculties
                if len(ongoing_ranges[-1][2]) > 1:
                    common_ranges.append((ongoing_ranges[-1][0], ongoing_ranges[-1][1]))
                
                # Start a new range
                ongoing_ranges.append((start, end, {faculty}))

        # Final check for the last range of the day
        if len(ongoing_ranges[-1][2]) > 1:
            common_ranges.append((ongoing_ranges[-1][0], ongoing_ranges[-1][1]))

    return common_ranges

    # group events by faculty and pass them to template 
def view_schedule(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view this page")
        return redirect('login')

    project_id = request.GET.get('project')

    if project_id and project_id.isdigit():
        # Filter schedules based on the selected project with status='approved'
        project = get_object_or_404(Project, id=project_id, status='approved')
        # Get the panelists and the adviser of the project
        panelists = project.panel.all()
        adviser = project.adviser
        # Combine panelists and adviser into one query
        faculties = list(panelists) + ([adviser] if adviser else [])
        faculty_schedules = Available_schedule.objects.filter(
            Q(faculty__in=panelists) | Q(faculty=adviser)
        )

        # Create a list of faculty with their roles (panelist or adviser)
        faculty_roles = {faculty: 'panelist' for faculty in panelists}
        if adviser:
            faculty_roles[adviser] = 'adviser'

    else:
        project = None
        # Show all faculty schedules if no project is selected
        faculty_schedules = Available_schedule.objects.all().select_related('faculty')
        faculties = Faculty.objects.filter(role='FACULTY')
        faculty_roles = {}

    # Calculate common schedules
    common_schedules = calculate_common_schedules(faculty_schedules)

    # Group events by faculty, including those without schedules
    grouped_events = {faculty: [] for faculty in faculties}
    for schedule in faculty_schedules:
        grouped_events[schedule.faculty].append(schedule)

    # Pass approved projects to the modal
    approved_projects = Project.objects.filter(status='approved', is_archived=False)



    
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
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if AJAX
        return render(request, 'mutual_availability/partials/faculty_list.html', {
            "grouped_events": grouped_events,
            "faculty_roles": faculty_roles,
            "common_schedules": common_schedules,

            "events": all_events,
            "defense_applications": defense_applications,
        })
    
    # Defense Schedules 

    return render(request, 'mutual_availability/view_schedules.html', {
        "grouped_events": grouped_events,
        "projects": approved_projects,
        "faculty_roles": faculty_roles,
        "common_schedules": common_schedules,

        "events": all_events,
        "defense_applications": defense_applications,
    })

def all_sched(request):
    project_id = request.GET.get('project')
    
    if project_id:
        # Get the project and its panelists and adviser
        project = get_object_or_404(Project, id=project_id, status='approved')
        panelists = project.panel.all()
        adviser = project.adviser

        # Filter events for panelists and adviser of the selected project
        all_events = Available_schedule.objects.filter(
            Q(faculty__in=panelists) | Q(faculty=adviser)
        ).select_related('faculty').order_by('-created_at')
    else:
        # Show all faculty schedules if no project is selected
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

@csrf_exempt  # Optional if CSRF token is handled in JS
def update_faculty_color(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse JSON from the request body
            faculty_id = data.get("faculty_id")
            new_color = data.get("color")

            # Validate input
            if not faculty_id or not new_color:
                return JsonResponse({"success": False, "error": "Invalid data provided."}, status=400)

            # Update the faculty record
            faculty = Faculty.objects.get(id=faculty_id)
            faculty.color = new_color
            faculty.save()

            # Return a success response
            return JsonResponse({"success": True, "new_color": new_color})
        except Faculty.DoesNotExist:
            return JsonResponse({"success": False, "error": "Faculty not found."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

# def delete_all_defense_schedules(request):
#     if request.method == 'POST':
#         try:
#             schedules = Defense_schedule.objects.all()
#             if not schedules.exists():
#                 return JsonResponse({'status': 'error', 'message': 'No schedules available to delete.'})
            
#             # Delete all schedules
#             schedules.delete()
#             return JsonResponse({'status': 'success'})
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)})
#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


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
