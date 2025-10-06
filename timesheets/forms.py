# timesheets/forms.py
from dataclasses import dataclass
from datetime import date
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from projects.models import Project
from timesheets.models import TimesheetEntry




class TimesheetDayForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=True)
    date = forms.DateField(required=True, input_formats=["%Y-%m-%d"])
    hours = forms.DecimalField(required=True, min_value=0, max_value=24, decimal_places=2)
    note = forms.CharField(required=False, max_length=500)

    def clean(self):
        cleaned = super().clean()
        # Ewentualne dodatkowe reguły
        return cleaned


class TimesheetMonthForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=True)
    year = forms.IntegerField(min_value=2000, max_value=2100, required=True)
    month = forms.IntegerField(min_value=1, max_value=12, required=True)

    # Uwaga: godziny dla poszczególnych dni przychodzą jako pola dynamiczne:
    # hours_YYYY-MM-DD = 0..24 (opcjonalne). Parsujemy to w widoku.

    def clean(self):
        cleaned = super().clean()
        year = cleaned.get("year")
        month = cleaned.get("month")
        if year and month:
            # Sprawdzenie poprawności daty (np. luty 30 nie istnieje — ale my generujemy z endpointu)
            pass
        return cleaned


@dataclass
class ParsedMonthHours:
    """Reprezentuje wyparsowane z POST wpisy dnia->godziny"""
    rows: list[tuple[date, float]]


