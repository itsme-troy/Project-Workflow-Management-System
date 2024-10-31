# from django.db import models

# from django.contrib.auth import get_user_model


# # class Event(models.Model):
# #     user = models.ForeignKey(User, on_delete=models.CASCADE)
# #     event_id = models.CharField(max_length=255)
# #     summary = models.CharField(max_length=255)
# #     start_time = models.DateTimeField()
# #     end_time = models.DateTimeField()
# #     created_at = models.DateTimeField(auto_now_add=True)

# class GoogleCalendarCredentials(models.Model):
#     user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
#     credentials = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

# class FacultyAvailability(models.Model):
#     faculty = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     recurring = models.BooleanField(default=False)
#     day_of_week = models.IntegerField(null=True, blank=True)  # 0=Monday, 6=Sunday
#     created_at = models.DateTimeField(auto_now_add=True)

# class DefenseSchedule(models.Model):
#     defense_application = models.ForeignKey('Defense_Application', on_delete=models.CASCADE)
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     google_event_id = models.CharField(max_length=1024, null=True, blank=True)
#     created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)