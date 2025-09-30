from django.db import models

# Create your models here.

class Location(models.Model):
    name=models.CharField(max_length=120,default="Unknown")
    sub_location=models.CharField(max_length=120,blank=True)

    def __str__(self):
        return f"{self.name}"+ (f"{self.sub_location}" if self.sub_location else "")


class Project(models.Model):
    class Status(models.TextChoices):
        BACKLOG = "BACKLOG", "Backlog"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        BLOCKED = "BLOCKED", "Blocked"
        REVIEW = "REVIEW", "Review"
        DONE = "DONE", "Done"
        CANCELLED = "CANCELLED", "Canceled"

    number = models.CharField("Project Number", max_length=50, unique=True)
    d_number = models.CharField("D-nr", max_length=50, blank=True)
    name = models.CharField("Project Name", max_length=200)
    client_name = models.CharField("Requestor", max_length=200)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    devices = models.CharField("Device", max_length=255, blank=True)
    date_received = models.DateField("Income Date")
    date_due = models.DateField("End Date", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BACKLOG)
    description = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("change_project_status", "Może zmieniać status projektu (Kanban)"),
        ]

    def __str__(self):
        return f"{self.number} – {self.name}"


