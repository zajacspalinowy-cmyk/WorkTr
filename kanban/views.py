from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.db.models import Count
from django.utils import timezone

from projects.models import Project

EMPTY_TEXT = {
    "BACKLOG": "Brak projektów w backlogu",
    "IN_PROGRESS": "Brak projektów w realizacji",
    "BLOCKED": "Brak zablokowanych projektów",
    "REVIEW": "Brak projektów do weryfikacji",
    "DONE": "Brak zakończonych projektów",
    "CANCELLED": "Brak anulowanych projektów",
}


def _get_status_choices():
    return list(Project._meta.get_field("status").choices)


def _split_by_status():
    # WAŻNE: filtruj tylko niezarchiwizowane
    qs = Project.objects.filter(archived=False)
    return {
        "backlog": qs.filter(status="BACKLOG").order_by("-id"),
        "in_progress": qs.filter(status="IN_PROGRESS").order_by("-id"),
        "blocked": qs.filter(status="BLOCKED").order_by("-id"),
        "review": qs.filter(status="REVIEW").order_by("-id"),
        "done": qs.filter(status="DONE").order_by("-id"),
        "cancelled": qs.filter(status="CANCELLED").order_by("-id"),
    }



def board(request):
    ctx = _split_by_status()
    ctx["status_choices"] = _get_status_choices()

    if request.headers.get("HX-Request"):
        return render(request, "kanban/_board_inner.html", ctx)
    return render(request, "kanban/board.html", ctx)


def _oob_move_response(request, project, old_status, new_status):
    # Zlicz tylko niezarchiwizowane projekty
    counts = dict(
        Project.objects.filter(archived=False)
        .values_list("status")
        .annotate(c=Count("id"))
    )
    count_old = counts.get(old_status, 0)
    count_new = counts.get(new_status, 0)

    return render(
        request,
        "kanban/_card_move_oob.html",
        {
            "project": project,
            "old_status": old_status,
            "new_status": new_status,
            "count_old": count_old,
            "count_new": count_new,
            "empty_text_old": EMPTY_TEXT.get(old_status, "Brak elementów"),
            "empty_text_new": EMPTY_TEXT.get(new_status, "Brak elementów"),
            "status_choices": _get_status_choices(),
        },
    )


@login_required
@permission_required("projects.change_project", raise_exception=True)
def change_status(request, project_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    project = get_object_or_404(Project, pk=project_id)
    new_status = request.POST.get("status")
    valid = {v for v, _ in _get_status_choices()}
    if new_status not in valid:
        return HttpResponseBadRequest("Bad status")

    old_status = project.status
    if old_status != new_status:
        project.status = new_status
        project.save(update_fields=["status"])

    return _oob_move_response(request, project, old_status, new_status)


@login_required
@permission_required("projects.change_project", raise_exception=True)
def drag_move(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    pid = request.POST.get("project_id")
    new_status = request.POST.get("status")
    valid = {v for v, _ in _get_status_choices()}
    if not pid or new_status not in valid:
        return HttpResponseBadRequest("Bad params")

    project = get_object_or_404(Project, pk=pid)
    old_status = project.status
    if old_status != new_status:
        project.status = new_status
        project.save(update_fields=["status"])

    return _oob_move_response(request, project, old_status, new_status)


# ========== ARCHIWIZACJA ==========

@login_required
def archive(request):
    """Widok archiwum - tabela zarchiwizowanych projektów"""
    archived = Project.objects.filter(archived=True).select_related(
        'archived_by'
    ).order_by('-archived_at')

    # Filtry
    status_filter = request.GET.get('status')
    if status_filter:
        archived = archived.filter(status=status_filter)

    return render(request, "kanban/archive.html", {
        "projects": archived,
        "status_filter": status_filter,
        "status_choices": _get_status_choices(),
    })


@login_required
@permission_required("projects.change_project", raise_exception=True)
def archive_project(request, project_id):
    """Archiwizacja projektu - usuwa z kanbana"""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    project = get_object_or_404(Project, pk=project_id)

    # Tylko DONE i CANCELLED można archiwizować
    if project.status not in ["DONE", "CANCELLED"]:
        return HttpResponseBadRequest("Można archiwizować tylko zakończone/anulowane projekty")

    # Archiwizuj
    old_status = project.status
    project.archived = True
    project.archived_at = timezone.now()
    project.archived_by = request.user
    project.save(update_fields=["archived", "archived_at", "archived_by"])

    # Policz projekty (bez zarchiwizowanych)
    counts = dict(
        Project.objects.filter(archived=False)
        .values_list("status")
        .annotate(c=Count("id"))
    )
    count = counts.get(old_status, 0)

    # Zwróć OOB który usuwa kartę
    return render(request, "kanban/_archive_oob.html", {
        "project_id": project_id,
        "old_status": old_status,
        "count": count,
        "empty_text": EMPTY_TEXT.get(old_status, "Brak elementów"),
    })



@login_required
@permission_required("projects.change_project", raise_exception=True)
def unarchive_project(request, project_id):
    """Przywrócenie projektu z archiwum do kanbana"""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    project = get_object_or_404(Project, pk=project_id)

    # Sprawdź czy projekt jest zarchiwizowany
    if not project.archived:
        return HttpResponseBadRequest("Projekt nie jest zarchiwizowany")

    # Przywróć
    project.archived = False
    project.archived_at = None
    project.archived_by = None
    project.save(update_fields=["archived", "archived_at", "archived_by"])

    # Zwróć OOB który usuwa wiersz z tabeli
    return render(request, "kanban/_unarchive_oob.html", {
        "project_id": project_id,
    })