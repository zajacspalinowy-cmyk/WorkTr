from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect

from .forms import ProjectForm, LocationQuickForm
from .models import Project
from timesheets.models import TimesheetEntry
from costs.models import ProjectCost
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, DecimalField, ExpressionWrapper

# Create your views here.

def project_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    qs = Project.objects.all().order_by('-date_received')
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(name__icontains=q) | Q(client_name__icontains=q))
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'status_choices': Project.Status.choices,
    }

    # WAŻNE: Sprawdź czy to request z HTMX
    if request.headers.get('HX-Request'):
        # Zwróć tylko fragment tabeli
        return render(request, 'projects/_table_partial.html', context)

    # Zwróć pełną stronę
    return render(request, 'projects/list.html', context)

def project_detail(request, pk):
    p = get_object_or_404(Project, pk=pk)

    hours_prev = (TimesheetEntry.objects
                  .filter(project=p, state=TimesheetEntry.State.APPROVED, date__year=(p.date_received.year - 1))
                  .aggregate(s=Sum("hours"))["s"] or 0)
    hours_curr = (TimesheetEntry.objects
                  .filter(project=p, state=TimesheetEntry.State.APPROVED, date__year=p.date_received.year)
                  .aggregate(s=Sum("hours"))["s"] or 0)

    cost_sum = (ProjectCost.objects
                .filter(project=p, state=ProjectCost.State.APPROVED)
                .aggregate(s=Sum(F("qty")*F("net_price")))["s"] or 0)

    costs = ProjectCost.objects.filter(project=p).select_related("item","created_by").order_by("-created_at")
    times = TimesheetEntry.objects.filter(project=p).select_related("technician").order_by("-date","-created_at")

    return render(request, "projects/detail.html", {
        "p": p,
        "hours_prev": hours_prev,
        "hours_curr": hours_curr,
        "cost_sum": cost_sum,
        "costs": costs,
        "times": times,
    })


@permission_required("projects.add_project", raise_exception=True)
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, "Projekt został utworzony.")
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, "projects/new.html", {"form": form})



@permission_required("projects.add_location", raise_exception=True)
def location_quick_add(request):
    """
    GET  -> zwraca mini-formularz dodania lokalizacji (partial)
    POST -> tworzy Location i OOB podmienia <select> z lokalizacjami (zaznacza nową)
    """
    if request.method == "POST":
        form = LocationQuickForm(request.POST)
        if form.is_valid():
            loc = form.save()
            # Przygotuj nowy ProjectForm z wybraną świeżo dodaną lokalizacją
            proj_form = ProjectForm()
            proj_form.fields["location"].initial = loc.pk
            return render(request, "projects/_location_quick_success.html", {
                "form": proj_form,
                "loc": loc,
            })
        else:
            # Błędy – renderujemy ponownie mini-form w tym samym miejscu
            return render(request, "projects/_location_quick_form.html", {"form": form})

    # GET – pokaż mini-formularz
    return render(request, "projects/_location_quick_form.html", {"form": LocationQuickForm()})

