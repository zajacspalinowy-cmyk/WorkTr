from calendar import monthrange
from datetime import date as date_cls, datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from projects.models import Project
from .models import TimesheetEntry

# ============ KOSZYK w sesji ============
BASKET_KEY = "ts_basket"

def _basket_get(request):
    return request.session.get(BASKET_KEY, [])

def _basket_set(request, items):
    request.session[BASKET_KEY] = items
    request.session.modified = True

# ============ Pomocnicze ============
def _parse_float(val, default=None):
    try:
        return float(str(val).replace(",", "."))
    except Exception:
        return default

def _add_err(errors: dict, key: str, msg: str):
    errors.setdefault(key, []).append(msg)

def _is_hx(request) -> bool:
    return request.headers.get("HX-Request") == "true"

def _basket_upsert(request, project, dt, hours, note):
    """
    Merge w koszyku: (project_id, date) -> sumujemy godziny, notatkę łączymy ' | '.
    """
    basket = _basket_get(request)
    key_pid = int(project.id)
    key_date = dt.strftime("%Y-%m-%d")
    merged = False
    for item in basket:
        if int(item["project_id"]) == key_pid and item["date"] == key_date:
            try:
                item["hours"] = float(item.get("hours", 0.0)) + float(hours)
            except Exception:
                item["hours"] = float(hours)
            n_old = (item.get("note") or "").strip()
            n_new = (note or "").strip()
            if n_new and n_new != n_old:
                item["note"] = (f"{n_old} | {n_new}").strip(" |")
            merged = True
            break
    if not merged:
        basket.append({
            "project_id": key_pid,
            "project_label": str(project),
            "date": key_date,
            "hours": float(hours),
            "note": (note or "").strip(),
        })
    _basket_set(request, basket)
    return merged

def _draft_context(request):
    basket = _basket_get(request)
    total = sum(float(item.get("hours") or 0) for item in basket)
    return {"drafts": basket, "total": total, "has_drafts": bool(basket)}

def _draft_list_oob(request) -> str:
    """Zwraca OOB: <div id='draft-list'>... (tabela albo pusty)</div>"""
    inner = render_to_string("timesheets/_draft_list.html", _draft_context(request), request=request)
    return f"<div id='draft-list' hx-swap-oob='outerHTML'>{inner}</div>"

def _draft_actions_oob(request) -> str:
    """Zwraca OOB: <div id='draft-actions'>... (przyciski lub pusty div)</div>"""
    inner = render_to_string("timesheets/_draft_actions.html", _draft_context(request), request=request)
    return f"<div id='draft-actions' hx-swap-oob='outerHTML'>{inner}</div>"

def _month_grid_clear_oob() -> str:
    """Po zapisie trybu MIESIĄC zwijamy siatkę dni."""
    return "<div id='month-grid' hx-swap-oob='outerHTML'></div>"

# ============ Dodawanie wpisów (Dzień / Miesiąc) -> KOSZYK ============
@require_http_methods(["GET", "POST"])
@login_required
def new_bulk_timesheet(request):
    context = {
        "projects": Project.objects.all().order_by("number", "name"),
        "today": datetime.today().date(),
        "mode": (request.POST.get("mode") or request.GET.get("mode") or "DAY").upper(),
    }

    if request.method == "GET":
        # wstrzykujemy gotowe HTML-e (bez hx-get)
        ctx = _draft_context(request)
        context["draft_inner_html"] = render_to_string("timesheets/_draft_list.html", ctx, request=request)
        context["draft_actions_html"] = render_to_string("timesheets/_draft_actions.html", ctx, request=request)
        return TemplateResponse(request, "timesheets/new_bulk.html", context)

    mode = context["mode"]
    errors = {}
    created = 0
    messages = []

    if mode == "DAY":
        date_str = (request.POST.get("date") or "").strip()
        hours = _parse_float(request.POST.get("hours"))
        note = (request.POST.get("note") or "").strip()

        project_ids = request.POST.getlist("projects")
        if not project_ids:
            single = request.POST.get("project")
            if single:
                project_ids = [single]

        try:
            ts_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            ts_date = None
            _add_err(errors, "date", "Nieprawidłowa data.")

        if hours is None or hours <= 0 or hours > 24:
            _add_err(errors, "hours", "Godziny muszą być z zakresu 0–24.")
        if not project_ids:
            _add_err(errors, "projects", "Wybierz co najmniej jeden projekt.")

        if not errors:
            for pid in project_ids:
                try:
                    p = Project.objects.get(id=pid)
                except Project.DoesNotExist:
                    continue
                _basket_upsert(request, p, ts_date, hours, note)
                created += 1
            messages.append(f"Dodano {created} wpis(ów) do koszyka.")

    elif mode == "MONTH":
        note = (request.POST.get("note") or "").strip()
        project_id = request.POST.get("project")
        try:
            year = int(request.POST.get("year"))
            month = int(request.POST.get("month"))
            assert 1 <= month <= 12
        except Exception:
            _add_err(errors, "month", "Podaj poprawny rok i miesiąc.")

        if not project_id:
            _add_err(errors, "project", "Wybierz projekt.")

        rows = []
        if not errors:
            for key, val in request.POST.items():
                if not (key.startswith("hours_") and val.strip()):
                    continue
                try:
                    d = datetime.strptime(key[6:], "%Y-%m-%d").date()
                    h = _parse_float(val)
                    if h is None or h <= 0 or h > 24:
                        continue
                    if d.year == year and d.month == month:
                        rows.append((d, h))
                except Exception:
                    continue
            if not rows:
                _add_err(errors, "hours", "Nie podano godzin dla żadnego dnia.")

        if not errors:
            try:
                p = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                _add_err(errors, "project", "Wybrany projekt nie istnieje.")
            else:
                for d, h in rows:
                    _basket_upsert(request, p, d, h, note)
                    created += 1
                messages.append(f"Dodano {created} wpisów do koszyka.")

    else:
        _add_err(errors, "mode", "Nieznany tryb.")

    # HTMX: zwracamy tylko #ts-messages + OOB: draft-list, draft-actions i (dla MIESIĄCA) zwinięcie siatki dni
    if _is_hx(request):
        resp = TemplateResponse(request, "timesheets/_messages.html", {
            "form_errors": errors or None,
            "messages": messages if (messages and not errors) else None,
        })
        resp.context_data["draft_oob"] = _draft_list_oob(request)
        resp.context_data["draft_actions_oob"] = _draft_actions_oob(request)
        if mode == "MONTH" and not errors:
            resp.context_data["month_oob"] = _month_grid_clear_oob()
        return resp

    # Fallback pełna strona
    ctx = _draft_context(request)
    context["draft_inner_html"] = render_to_string("timesheets/_draft_list.html", ctx, request=request)
    context["draft_actions_html"] = render_to_string("timesheets/_draft_actions.html", ctx, request=request)
    return TemplateResponse(request, "timesheets/new_bulk.html", {
        **context,
        "form_errors": errors or None,
        "messages": messages if (messages and not errors) else None,
    })

# ============ KOSZYK (GET — pomocniczo) ============
@require_GET
@login_required
def draft_list(request):
    return TemplateResponse(request, "timesheets/_draft_list.html", _draft_context(request))

# ============ Wysłanie do akceptacji (PENDING) ============
@require_POST
@login_required
@transaction.atomic
def submit_entries(request):
    basket = _basket_get(request)
    if not basket:
        return TemplateResponse(request, "timesheets/_draft_messages.html", {
            "error": "Koszyk jest pusty.",
            "draft_oob": _draft_list_oob(request),
            "draft_actions_oob": _draft_actions_oob(request),
        })

    idx_list = request.POST.getlist("draft_idx")
    submit_all = request.POST.get("submit_all") == "1"
    if idx_list and submit_all:
        return HttpResponseBadRequest("Wybierz albo zaznaczone, albo wszystkie.")

    to_send = []
    if submit_all:
        to_send = list(range(len(basket)))
    elif idx_list:
        try:
            to_send = sorted({int(i) for i in idx_list if 0 <= int(i) < len(basket)})
        except Exception:
            return HttpResponseBadRequest("Nieprawidłowe indeksy.")

    if not to_send:
        return TemplateResponse(request, "timesheets/_draft_messages.html", {
            "error": "Nie wybrano żadnych pozycji.",
            "draft_oob": _draft_list_oob(request),
            "draft_actions_oob": _draft_actions_oob(request),
        })

    created = 0
    for idx in to_send:
        item = basket[idx]
        try:
            project = Project.objects.get(id=item["project_id"])
        except Project.DoesNotExist:
            continue
        TimesheetEntry.objects.create(
            technician=request.user,
            project=project,
            date=datetime.strptime(item["date"], "%Y-%m-%d").date(),
            hours=float(item["hours"]),
            note=item.get("note", ""),
            state=TimesheetEntry.State.PENDING,
        )
        created += 1

    for idx in sorted(to_send, reverse=True):
        basket.pop(idx)
    _basket_set(request, basket)

    return TemplateResponse(request, "timesheets/_draft_messages.html", {
        "ok": f"Wysłano do akceptacji: {created} wpisów.",
        "draft_oob": _draft_list_oob(request),
        "draft_actions_oob": _draft_actions_oob(request),
    })

# ============ Moje wpisy ============
@login_required
def my_entries(request):
    entries = (
        TimesheetEntry.objects
        .filter(technician=request.user)
        .select_related("project")
        .order_by("-date", "-id")
    )
    pending_count = entries.filter(state=TimesheetEntry.State.PENDING).count()
    approved_count = entries.filter(state=TimesheetEntry.State.APPROVED).count()
    return render(request, "timesheets/my_entries.html", {
        "entries": entries,
        "pending_count": pending_count,
        "approved_count": approved_count,
    })

# ============ Przegląd / akceptacja ============
@permission_required("timesheets.review_timesheets", raise_exception=True)
def review_entries(request):
    entries = (
        TimesheetEntry.objects
        .filter(state=TimesheetEntry.State.PENDING)
        .select_related("project", "technician")
        .order_by("date", "id")
    )
    return render(request, "timesheets/review.html", {"entries": entries})

@permission_required("timesheets.review_timesheets", raise_exception=True)
def approve_entry(request, entry_id: int):
    entry = get_object_or_404(TimesheetEntry, pk=entry_id)
    entry.state = TimesheetEntry.State.APPROVED
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.save(update_fields=["state", "approved_by", "approved_at"])
    return HttpResponseRedirect(reverse("timesheets:review"))

@permission_required("timesheets.review_timesheets", raise_exception=True)
def reject_entry(request, entry_id: int):
    entry = get_object_or_404(TimesheetEntry, pk=entry_id)
    entry.state = TimesheetEntry.State.REJECTED
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.save(update_fields=["state", "approved_by", "approved_at"])
    return HttpResponseRedirect(reverse("timesheets:review"))

# ============ (opcjonalnie) siatka dni ============
@require_GET
@login_required
def month_grid(request):
    try:
        year = int(request.GET.get("year"))
        month = int(request.GET.get("month"))
        assert 1 <= month <= 12
    except Exception:
        return TemplateResponse(request, "timesheets/_month_grid.html", {"days": []})

    _, last_day = monthrange(year, month)
    days = [date_cls(year, month, d) for d in range(1, last_day + 1)]
    return TemplateResponse(request, "timesheets/_month_grid.html", {"days": days})
