from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from projects.models import Project
from .models import CostItem, ProjectCost


@login_required
def new_cost(request):
    if request.method == "POST":
        project_id = request.POST.get("project")
        category = request.POST.get("category", "inne")
        item_name = request.POST.get("item_name", "").strip()
        unit = request.POST.get("unit", "").strip()
        qty = request.POST.get("qty") or "1"
        net_price = request.POST.get("net_price") or "0"
        note = request.POST.get("note", "")

        # Walidacja
        if not item_name or not unit:
            messages.error(request, "Podaj nazwę pozycji i jednostkę")
            projects = Project.objects.all().order_by("number")
            return render(request, "costs/new.html", {"projects": projects})

        # Utwórz nowy CostItem lub znajdź istniejący
        try:
            # Najpierw sprawdź czy istnieje
            item = CostItem.objects.filter(name=item_name, unit=unit).first()

            if not item:
                # Jeśli nie ma, utwórz nowy
                item = CostItem.objects.create(
                    name=item_name,
                    unit=unit,
                    default_net_price=net_price
                )

            # Utwórz koszt
            ProjectCost.objects.create(
                project_id=project_id,
                item=item,  # Przekaż obiekt, nie ID
                qty=qty,
                net_price=net_price,
                note=note,
                state=ProjectCost.State.PENDING,
                created_by=request.user
            )

            messages.success(request, f"Koszt '{item_name}' został zgłoszony")
            return redirect("costs:mine")

        except Exception as e:
            messages.error(request, f"Błąd podczas zapisywania: {str(e)}")
            projects = Project.objects.all().order_by("number")
            return render(request, "costs/new.html", {"projects": projects})

    projects = Project.objects.all().order_by("number")
    return render(request, "costs/new.html", {"projects": projects})


@login_required
def my_costs(request):
    rows = (ProjectCost.objects
            .filter(created_by=request.user)
            .select_related("project", "item")
            .order_by("-created_at"))

    # Policz statusy
    pending_count = rows.filter(state=ProjectCost.State.PENDING).count()
    approved_count = rows.filter(state=ProjectCost.State.APPROVED).count()

    return render(request, "costs/mine.html", {
        "rows": rows,
        "pending_count": pending_count,
        "approved_count": approved_count,
    })

@permission_required("costs.review_costs", raise_exception=True)
def review_costs(request):
    rows = (ProjectCost.objects
            .filter(state=ProjectCost.State.PENDING)
            .select_related("project","item","created_by")
            .order_by("created_at"))
    return render(request, "costs/review.html", {"rows": rows})

@permission_required("costs.review_costs", raise_exception=True)
def approve_cost(request, pk):
    row = get_object_or_404(ProjectCost, pk=pk)
    row.state = ProjectCost.State.APPROVED
    row.approved_by = request.user
    row.approved_at = timezone.now()
    row.save()
    return redirect("costs:review")

@permission_required("costs.review_costs", raise_exception=True)
def reject_cost(request, pk):
    row = get_object_or_404(ProjectCost, pk=pk)
    row.state = ProjectCost.State.REJECTED
    row.approved_by = request.user
    row.approved_at = timezone.now()
    row.save()
    return redirect("costs:review")
