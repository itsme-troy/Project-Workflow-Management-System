from django.db import models
from project.models import Defense_Application


# Create your models here.
class Defense_schedule(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255,null=True,blank=True)
    start = models.DateTimeField(null=True,blank=True)
    end = models.DateTimeField(null=True,blank=True)
    # faculty = models.ForeignKey(Faculty, null=True, on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default='#FMXCFF')  # Store the color in hex format (e.g., #FF5733)
    created_at = models.DateTimeField(auto_now_add=True)
    application = models.ForeignKey(Defense_Application, null=True, on_delete=models.CASCADE)
    
    # def save(self, *args, **kwargs):
    #     # Only set the group name if it's not already set
    #     if not self.title:
    #         # Save the object to get the ID
    #         super().save(*args, **kwargs)
    #         # Set the group name based on the ID
    #         self.title = f'{self.faculty.last_name}'  # or any format you prefer
    #     super().save(*args, **kwargs)

    def __str__(self):
        # Return the title of the associated Defense_Application
        if self.application:
            return self.application.project.title
        return "No Application Assigned"
