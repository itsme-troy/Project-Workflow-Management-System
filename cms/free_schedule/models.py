from django.db import models
from project.models import Faculty
from project.models import Defense_Application

class Available_schedule(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255,null=True,blank=True)
    start = models.DateTimeField(null=True,blank=True)
    end = models.DateTimeField(null=True,blank=True)
    faculty = models.ForeignKey(Faculty, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Only set the group name if it's not already set
        if not self.title:
            # Save the object to get the ID
            super().save(*args, **kwargs)
            # Set the group name based on the ID
            self.title = f'{self.faculty.last_name}'  # or any format you prefer
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.faculty.last_name}, {self.faculty.first_name}"
    
    
# class Common_schedule(models.Model): # Common Available Schedule between faculty and adviser
#     id = models.AutoField(primary_key=True)
#     defense_application = models.ForeignKey(Defense_Application, null=True,  on_delete=models.CASCADE)

#     def __str__(self):
#         return self.defense_application
    




 