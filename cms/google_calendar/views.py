# from django.shortcuts import redirect
# from django.contrib.auth.decorators import login_required, user_passes_test
# from .utils.google_calendar import GoogleCalendarService
# from .models import GoogleCalendarCredentials, FacultyAvailability, DefenseSchedule
# from django.urls import reverse

# @login_required
# def google_calendar_init(request):
#     flow = GoogleCalendarService.get_oauth_flow()
#     authorization_url, state = flow.authorization_url()
#     request.session['google_oauth_state'] = state
#     return redirect(authorization_url)

# @login_required
# def google_calendar_callback(request):
#     flow = GoogleCalendarService.get_oauth_flow()
#     flow.fetch_token(
#         authorization_response=request.build_absolute_uri(),
#     )

#     credentials = flow.credentials
#     GoogleCalendarCredentials.objects.update_or_create(
#         user=request.user,
#         defaults={'credentials': credentials_to_dict(credentials)}
#     )
    
#     messages.success(request, "Successfully connected to Google Calendar!")
#     return redirect('faculty_availability')

# @login_required
# @user_passes_test(lambda u: u.role == 'FACULTY')
# def set_availability(request):
#     if request.method == 'POST':
#         start_time = request.POST.get('start_time')
#         end_time = request.POST.get('end_time')
#         recurring = request.POST.get('recurring', False)
#         day_of_week = request.POST.get('day_of_week') if recurring else None

#         FacultyAvailability.objects.create(
#             faculty=request.user,
#             start_time=start_time,
#             end_time=end_time,
#             recurring=recurring,
#             day_of_week=day_of_week
#         )
        
#         messages.success(request, "Availability set successfully!")
#         return redirect('faculty_availability')

#     availabilities = FacultyAvailability.objects.filter(faculty=request.user)
#     return render(request, 'project/set_availability.html', {
#         'availabilities': availabilities
#     })

# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def schedule_defense(request, application_id):
#     application = get_object_or_404(Defense_Application, id=application_id)
    
#     if request.method == 'POST':
#         start_time = request.POST.get('start_time')
#         end_time = request.POST.get('end_time')
        
#         # Create defense schedule
#         schedule = DefenseSchedule.objects.create(
#             defense_application=application,
#             start_time=start_time,
#             end_time=end_time,
#             created_by=request.user
#         )

#         # Get all involved faculty emails
#         attendees = [application.adviser.email]
#         attendees.extend(panelist.email for panelist in application.panel.all())
        
#         try:
#             # Get coordinator's calendar credentials
#             creds = GoogleCalendarCredentials.objects.get(user=request.user)
#             service = GoogleCalendarService.build_service(creds.credentials)
            
#             # Create calendar event
#             event = GoogleCalendarService.create_event(
#                 service,
#                 f"Defense: {application.project.title}",
#                 schedule.start_time,
#                 schedule.end_time,
#                 attendees
#             )
            
#             schedule.google_event_id = event['id']
#             schedule.save()
            
#             messages.success(request, "Defense scheduled successfully!")
#         except Exception as e:
#             messages.error(request, f"Error scheduling defense: {str(e)}")
#             schedule.delete()
        
#         return redirect('list-defense-applications')

#     # Get all faculty availabilities for the panel members
#     panel_availabilities = FacultyAvailability.objects.filter(
#         faculty__in=[application.adviser] + list(application.panel.all())
#     )
    
#     return render(request, 'project/schedule_defense.html', {
#         'application': application,
#         'panel_availabilities': panel_availabilities
#     })