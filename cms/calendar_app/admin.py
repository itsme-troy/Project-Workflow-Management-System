from django.contrib import admin
from .models import Defense_schedule

# @admin.register(Defense_schedule)
# class Defense_scheduleAdmin(admin.ModelAdmin): 
#     fields = ( 'title', 'start', 'end','color', 'application') #'title',
#     list_display = ( 'title','start', 'end', 'get_project_title') # 'title',

#     # Create a custom method to display the project title
#     def get_project_title(self, obj):
#         # Access the title of the project related to the Defense_Application
#         return obj.application.project.title if obj.application and obj.application.project else "No Project"
    
#      # Name of the custom method for display
#     get_project_title.short_description = 'Project Title'