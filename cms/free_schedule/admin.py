from django.contrib import admin
from .models import Available_schedule
# Register your models here.


@admin.register(Available_schedule)
class Available_scheduleAdmin(admin.ModelAdmin): 
    fields = ( 'title', 'start', 'end', 'faculty', 'color') #'title',
    list_display = ( 'title','start', 'end', 'faculty') # 'title',


    