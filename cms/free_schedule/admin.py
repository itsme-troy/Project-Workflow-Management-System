from django.contrib import admin
from .models import Available_schedule
# Register your models here.


@admin.register(Available_schedule)
class Available_scheduleAdmin(admin.ModelAdmin): 
    fields = ( 'start', 'end', 'faculty', 'color') 
    list_display = ('start', 'end', 'faculty') 


    