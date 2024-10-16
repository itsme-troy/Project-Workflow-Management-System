from .models import Available_schedule
from django.contrib import admin
# Register your models here.


@admin.register(Available_schedule)
class Available_scheduleAdmin(admin.ModelAdmin): 
    fields = ( 'title', 'start', 'end', 'faculty') #'title',
    list_display = ( 'title','start', 'end', 'faculty') # 'title',


