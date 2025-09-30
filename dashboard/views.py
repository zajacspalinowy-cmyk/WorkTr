# dashboard/views.py
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.utils.timezone import now
from projects.models import Project
from timesheets.models import TimesheetEntry
from costs.models import ProjectCost
from datetime import datetime

def home(request):
    today = now().date()
    y = today.year
    prev = y - 1

    hours_curr = (TimesheetEntry.objects
                  .filter(state="APPROVED", date__year=y)
                  .aggregate(s=Sum("hours"))["s"] or 0)
    hours_prev = (TimesheetEntry.objects
                  .filter(state="APPROVED", date__year=prev)
                  .aggregate(s=Sum("hours"))["s"] or 0)

    # Sumaryczny koszt: qty * net_price (zatwierdzone)
    cost_total = (ProjectCost.objects
                  .filter(state="APPROVED")
                  .aggregate(s=Sum(
                      ExpressionWrapper(F("qty") * F("net_price"),
                                        output_field=DecimalField(max_digits=14, decimal_places=2))
                  ))["s"] or 0)

    # Godziny per miesiąc (bieżący rok)
    monthly = [0]*12
    for m, s in (TimesheetEntry.objects
                 .filter(state="APPROVED", date__year=y)
                 .values_list("date__month")
                 .annotate(s=Sum("hours"))
                 .order_by("date__month")):
        monthly[m-1] = float(s or 0)

    # Liczba projektów w statusach (kod -> liczba)
    status_counts = dict(Project.objects.values_list("status").annotate(c=Count("id")))

    # Nazwy miesięcy do szablonu (bez .split w template)
    months = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"]

    return render(request, "dashboard/home.html", {
        "hours_curr": hours_curr,
        "hours_prev": hours_prev,
        "cost_total": cost_total,
        "monthly": monthly,
        "status_counts": status_counts,
        "months": months,     # ⬅️ to dodajemy
        "year": y,
        "prev": prev,
    })



def htmx_test(request):
    return render(request, "dashboard/htmx_test.html")

def htmx_ping(request):
    # zwracamy „ponga” z aktualną godziną – idealne do sprawdzenia auto-refresh
    return HttpResponse(f"pong: {datetime.now().strftime('%H:%M:%S')}")