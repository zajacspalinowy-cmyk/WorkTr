# dashboard/views.py
from collections import defaultdict
from datetime import datetime
from django.shortcuts import render
from django.db.models import Sum, Count, F, Min, DecimalField, ExpressionWrapper
from django.utils.timezone import now

from projects.models import Project
from timesheets.models import TimesheetEntry
from costs.models import ProjectCost


def _year_context(year: int):
    """Buduje cały kontekst „roczny”: kafelki, wykres, tabela projektów."""
    prev = year - 1

    # ---- Kafelki godzin ----
    hours_curr = (TimesheetEntry.objects
                  .filter(state="APPROVED", date__year=year)
                  .aggregate(s=Sum("hours"))["s"] or 0)

    hours_prev = (TimesheetEntry.objects
                  .filter(state="APPROVED", date__year=prev)
                  .aggregate(s=Sum("hours"))["s"] or 0)

    # ---- Koszty (łączna kwota zatwierdzona – nie zależy od roku,
    # ale trzymamy tu dla spójności kafelków)
    cost_total = (ProjectCost.objects
                  .filter(state="APPROVED")
                  .aggregate(s=Sum(
                      ExpressionWrapper(F("qty") * F("net_price"),
                                        output_field=DecimalField(max_digits=14, decimal_places=2))
                  ))["s"] or 0)

    # ---- Godziny per miesiąc (wykres) ----
    months_labels = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"]
    monthly = [0.0] * 12
    for m, s in (TimesheetEntry.objects
                 .filter(state="APPROVED", date__year=year)
                 .values_list("date__month")
                 .annotate(s=Sum("hours"))
                 .order_by("date__month")):
        monthly[m - 1] = float(s or 0)

    max_val = max(monthly) if monthly else 0.0
    monthly_bars = []
    for label, val in zip(months_labels, monthly):
        if max_val > 0:
            pct = (val / max_val) * 100.0
            if val > 0 and pct < 6:
                pct = 6.0
        else:
            pct = 0.0
        monthly_bars.append({"label": label, "value": val, "pct": pct})

    # ---- Statusy projektów (do kafelka „informacyjnego”) ----
    status_counts = dict(Project.objects.values_list("status").annotate(c=Count("id")))

    # ---- Macierz godzin per projekt ----
    curr_dict = defaultdict(lambda: [0.0] * 12)
    for pid, m, s in (TimesheetEntry.objects
                      .filter(state="APPROVED", date__year=year)
                      .values_list("project_id", "date__month")
                      .annotate(s=Sum("hours"))
                      .order_by()):
        curr_dict[int(pid)][m - 1] = float(s or 0)

    prev_dict = dict((int(pid), float(s or 0))
                     for pid, s in (TimesheetEntry.objects
                                    .filter(state="APPROVED", date__year=prev)
                                    .values_list("project_id")
                                    .annotate(s=Sum("hours"))
                                    .order_by()))

    earlier_dict = dict((int(pid), float(s or 0))
                        for pid, s in (TimesheetEntry.objects
                                       .filter(state="APPROVED", date__year__lt=prev)
                                       .values_list("project_id")
                                       .annotate(s=Sum("hours"))
                                       .order_by()))

    project_rows = []
    projects = Project.objects.all().order_by("number", "name")
    for p in projects:
        months_list = curr_dict.get(p.id, [0.0] * 12)
        sum_curr = sum(months_list)
        sum_prev_p = prev_dict.get(p.id, 0.0)
        sum_earlier = earlier_dict.get(p.id, 0.0)
        project_rows.append({
            "project": p,
            "prev_year": sum_prev_p,
            "earlier_years": sum_earlier,
            "months": months_list,
            "sum_current": sum_curr,
            "sum_curr_prev": sum_curr + sum_prev_p,
            "sum_all": sum_curr + sum_prev_p + sum_earlier,
        })

    totals_months = [0.0] * 12
    for i in range(12):
        totals_months[i] = sum(r["months"][i] for r in project_rows)
    totals_prev = sum(r["prev_year"] for r in project_rows)
    totals_earlier = sum(r["earlier_years"] for r in project_rows)
    totals_curr = sum(totals_months)
    totals_curr_prev = totals_curr + totals_prev
    totals_all = totals_curr_prev + totals_earlier

    empty_colspan = len(months_labels) + 6  # Projekt + prev + <prev + 12 mies> + 3 sumy

    return {
        "year": year,
        "prev": prev,
        "months": months_labels,
        "hours_curr": hours_curr,
        "hours_prev": hours_prev,
        "cost_total": cost_total,
        "monthly": monthly,
        "monthly_bars": monthly_bars,
        "status_counts": status_counts,
        "project_rows": project_rows,
        "totals": {
            "prev_year": totals_prev,
            "earlier_years": totals_earlier,
            "months": totals_months,
            "sum_current": totals_curr,
            "sum_curr_prev": totals_curr_prev,
            "sum_all": totals_all,
        },
        "empty_colspan": empty_colspan,
    }


def home(request):
    """Pełna strona: nagłówek + pasek lat + pierwszy „blok roczny”."""
    today = now().date()
    year = today.year

    # zakres lat do wyboru (od najstarszego wpisu do bieżącego)
    min_date = (TimesheetEntry.objects
                .filter(state="APPROVED")
                .aggregate(m=Min("date"))["m"])
    min_year = (min_date.year if min_date else year)
    # ograniczamy do sensownej liczby (np. max 10 lat wstecz)
    start = max(min_year, year - 9)
    year_choices = list(range(year, start - 1, -1))  # malejąco

    ctx = _year_context(year)
    ctx.update({"year_choices": year_choices})
    return render(request, "dashboard/home.html", ctx)


def year_block(request, year: int):
    """Partial HTMX – podmienia część z kafelkami/wykresem/tabelą dla wskazanego roku."""
    ctx = _year_context(year)
    return render(request, "dashboard/_year_block.html", ctx)


# (opcjonalne – utrzymujemy, jeśli masz w URL-ach)
def htmx_test(request):
    return render(request, "dashboard/htmx_test.html")


def htmx_ping(request):
    return render(request, "dashboard/htmx_ping.html", {"now": datetime.now()})
