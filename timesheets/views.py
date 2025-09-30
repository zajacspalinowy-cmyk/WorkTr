from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from projects.models import Project
from .models import TimesheetEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.urls import reverse
# Create your views here.

@login_required
def new_bulk_timesheet(request):
    if request.method == "POST":
        date = request.POST.get("date")
        hours = request.POST.get("hours")
        note = request.POST.get("note", "")
        project_ids = request.POST.getlist("projects")

        for pid in project_ids:
            TimesheetEntry.objects.create(
                technician=request.user,
                project_id=pid,
                date=date,
                hours=hours,
                note=note,
                state=TimesheetEntry.State.PENDING
            )
        return redirect("timesheets:my_entries")

    projects = Project.objects.all().order_by("number")
    return render(request, "timesheets/new_bulk.html", {"projects": projects})

@staff_member_required
def review_entries(request):
    entries = TimesheetEntry.objects.filter(state=TimesheetEntry.State.PENDING).order_by("date")
    return render(request, "timesheets/review.html", {"entries": entries})


@login_required
def my_entries(request):
    entries = (TimesheetEntry.objects
               .filter(technician=request.user)
               .order_by('-date', '-created_at'))

    # Policz statusy
    pending_count = entries.filter(state=TimesheetEntry.State.PENDING).count()
    approved_count = entries.filter(state=TimesheetEntry.State.APPROVED).count()

    return render(request, "timesheets/my_entries.html", {
        "entries": entries,
        "pending_count": pending_count,
        "approved_count": approved_count,
    })


@permission_required("timesheets.review_timesheets", raise_exception=True)
def review_entries(request):
    entries = (TimesheetEntry.objects
               .filter(state=TimesheetEntry.State.PENDING)
               .order_by('date'))
    return render(request, "timesheets/review.html", {"entries": entries})


@permission_required("timesheets.review_timesheets", raise_exception=True)
def approve_entry(request, pk):
    entry = TimesheetEntry.objects.get(pk=pk)
    entry.state = TimesheetEntry.State.APPROVED
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.save()
    return HttpResponseRedirect(reverse("timesheets:review"))


@permission_required("timesheets.review_timesheets", raise_exception=True)
def reject_entry(request, pk):
    entry = TimesheetEntry.objects.get(pk=pk)
    entry.state = TimesheetEntry.State.REJECTED
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.save()
    return HttpResponseRedirect(reverse("timesheets:review"))