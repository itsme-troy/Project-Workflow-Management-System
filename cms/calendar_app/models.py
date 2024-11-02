from django.db import models
from project.models import ApprovedProject, Defense_Application

# Create your models here.
class Event(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255,null=True,blank=True)
    start = models.DateTimeField(null=True,blank=True)
    end = models.DateTimeField(null=True,blank=True)
    defense_application = models.ForeignKey(Defense_Application, null=True, on_delete=models.CASCADE, related_name='events')

    def __str__(self):
        return f"{self.defense_application}" 

