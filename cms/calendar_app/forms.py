from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        type_of_defense = [ 
            ("Topic Defense", "Topic Defense" ),
            ("Design Defense", "Design Defense"),
            ("Preliminary Defense", "Preliminary Defense"),
            ("Final Defense", "Final Defense")
        ]
    
        model = Event
        fields = [ 'title', 'start', 'end', 'defense_application'] #'title',
        widgets = {
            'title': forms.Select(choices=type_of_defense, attrs={'class':'form-select', 'placeholder': 'Select Type of Defense'}), 
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'defense_application': forms.Select(attrs={'class':'form-select', 'placeholder': 'Select Application'}), 

}