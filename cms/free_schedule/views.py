
from django.shortcuts import render
from django.contrib import messages
from .models import Available_schedule
from django.http import JsonResponse

# def find_common_schedule 
def find_common_schedule(request): 
    schedules = Available_schedule.objects.all()  # or filter by some criteria
    common_slots = {}
    # Here, add logic to find overlapping time slots
    for schedule in schedules:
        start_time = schedule.start
        end_time = schedule.end

     # Assuming common_slots is a dictionary where keys are start times and values are lists of events
        if (start_time, end_time) in common_slots:
            common_slots[(start_time, end_time)].append(schedule)
        
        else:
            common_slots[(start_time, end_time)] = [schedule]

    # Prepare the response in the required format
    events = []
    for (start, end), schedules in common_slots.items():
        events.append({
            'title': 'Common Slot',
            'start': start.strftime("%Y-%m-%d %H:%M:%S"),
            'end': end.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse(events, safe=False)

def free_sched(request): # index 
    all_events = Available_schedule.objects.filter(faculty=request.user.id)
    return render(request, 'free_schedule/free_schedule.html', {
        "events": all_events,
    })

def all_sched(request):                                                                                                 
    all_events = Available_schedule.objects.filter(faculty=request.user.id)                                                                  
    out = []                                                                                                             
    for event in all_events:                                                                                             
        out.append({                                                                                                     
            'title': event.title,                                                                                         
            'id': event.id,                                                                                              
            'start': event.start.strftime("%m/%d/%Y, %H:%M:%S"),                                                         
            'end': event.end.strftime("%m/%d/%Y, %H:%M:%S"),                                                             
        })                                                                                                                                                                                                                                
    return JsonResponse(out, safe=False) 
 
def add_sched(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)

    event = Available_schedule(title=str(title), start=start, end=end, faculty = request.user)

    event.save()
    data = {}
    return JsonResponse(data)


def update_sched(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    title = request.GET.get("title", None)
    id = request.GET.get("id", None)
    event = Available_schedule.objects.get(id=id)
    event.start = start
    event.end = end
    event.title = title
    event.save()
    data = {}
    return JsonResponse(data)
 
def remove_sched(request):
    id = request.GET.get("id", None)
    event = Available_schedule.objects.get(id=id)
    event.delete()
    data = {}
    return JsonResponse(data)

