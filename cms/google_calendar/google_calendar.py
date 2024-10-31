# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import Flow
# from googleapiclient.discovery import build
# from django.conf import settings
# import datetime

# class GoogleCalendarService:
#     SCOPES = ['https://www.googleapis.com/auth/calendar']

#     @staticmethod
#     def get_oauth_flow():
#         return Flow.from_client_config(
#             settings.GOOGLE_OAUTH_CONFIG,
#             scopes=GoogleCalendarService.SCOPES,
#             redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
#         )

#     @staticmethod
#     def build_service(credentials_dict):
#         credentials = Credentials.from_authorized_user_info(credentials_dict)
#         return build('calendar', 'v3', credentials=credentials)

#     @staticmethod
#     def create_event(service, summary, start_time, end_time, attendees=None):
#         event = {
#             'summary': summary,
#             'start': {
#                 'dateTime': start_time.isoformat(),
#                 'timeZone': 'Asia/Manila',
#             },
#             'end': {
#                 'dateTime': end_time.isoformat(),
#                 'timeZone': 'Asia/Manila',
#             },
#         }
        
#         if attendees:
#             event['attendees'] = [{'email': attendee} for attendee in attendees]

#         return service.events().insert(calendarId='primary', body=event).execute()