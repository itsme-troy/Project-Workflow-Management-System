from django.contrib import admin
from .models import Event
# Register your models here.


@admin.register(Event)
class EventAdmin(admin.ModelAdmin): 
    fields = ('defense_application', 'title', 'start', 'end', ) #'title',
    list_display = ('defense_application', 'title','start', 'end') # 'title',


