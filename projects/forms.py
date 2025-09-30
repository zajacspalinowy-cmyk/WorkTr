# projects/forms.py
from django import forms
from .models import Project, Location

class DateInput(forms.DateInput):
    input_type = "date"

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "number", "d_number", "name", "client_name",
            "location", "devices",
            "date_received", "date_due",
            "status", "description",
        ]
        widgets = {
            "date_received": DateInput(),
            "date_due": DateInput(),
            "description": forms.Textarea(attrs={"rows": 4}),
        }



class LocationQuickForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["name", "sub_location"]
        labels = {"name": "Nazwa", "sub_location": "Pod-lokalizacja"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "np. Legnica"}),
            "sub_location": forms.TextInput(attrs={"placeholder": "np. Hala A (opcjonalnie)"}),
        }