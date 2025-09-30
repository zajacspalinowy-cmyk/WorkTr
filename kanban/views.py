# kanban/views.py
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from projects.models import Project


def _board_context():
    # WAŻNE: sortowanie po -id zamiast -updated_at dla stabilnej kolejności
    return {
        "backlog":    Project.objects.filter(status=Project.Status.BACKLOG).order_by("-id"),
        "in_progress":Project.objects.filter(status=Project.Status.IN_PROGRESS).order_by("-id"),
        "blocked":    Project.objects.filter(status=Project.Status.BLOCKED).order_by("-id"),
        "review":     Project.objects.filter(status=Project.Status.REVIEW).order_by("-id"),
        "done":       Project.objects.filter(status=Project.Status.DONE).order_by("-id"),
        "cancelled":  Project.objects.filter(status=Project.Status.CANCELLED).order_by("-id"),
        "status_choices": Project.Status.choices,
    }

@login_required
def board(request):
    ctx = _board_context()
    template = "kanban/_board_inner.html" if getattr(request, "htmx", False) else "kanban/board.html"
    return render(request, template, ctx)

@require_POST
@permission_required("projects.change_project_status", raise_exception=True)
def change_status(request, pk):
    project = get_object_or_404(Project, pk=pk)
    old_status = project.status
    new_status = request.POST.get("status")

    allowed = {c[0] for c in Project.Status.choices}
    if new_status in allowed and new_status != old_status:
        project.status = new_status
        project.save(update_fields=["status", "updated_at"])
    else:
        new_status = project.status

    # Policz aktualne liczby tylko dla dwóch dotkniętych statusów
    counts = dict(
        Project.objects
        .filter(status__in=[old_status, new_status])
        .values_list("status")
        .annotate(c=Count("id"))
    )
    count_old = counts.get(old_status, 0)
    count_new = counts.get(new_status, 0)

    return render(request, "kanban/_card_move_oob.html", {
        "project": project,
        "status_choices": Project.Status.choices,
        "old_status": old_status,
        "new_status": new_status,
        "count_old": count_old,
        "count_new": count_new,
    })