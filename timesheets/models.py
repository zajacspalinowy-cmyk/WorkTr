from django.db import models
from django.conf import settings
from projects.models import Project

# Create your models here.


class TimesheetEntry(models.Model):
    class State(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    technician=models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="timesheets"

        )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="timesheets")
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)  # np. 7.50
    note = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=10, choices=State.choices, default=State.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_timesheets"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [
            ("review_timesheets", "Może przeglądać i akceptować wpisy godzin"),
        ]

    def __str__(self):
        return f"{self.project.number} – {self.date} – {self.hours}h"

