from django.db.models import Sum, Q, DecimalField
from django.utils.timezone import now


def annotate_year_hours(qs):
    today = now().date()
    curr_year = today.year
    prev_year = curr_year - 1
    return qs.annotate(
        prev_year_hours=Sum(
            'timesheets__hours',
            filter=Q(timesheets__state='APPROVED', timesheets__date__year=prev_year),
            output_field=DecimalField(max_digits=8, decimal_places=2)
        ),
        current_year_hours=Sum(
            'timesheets__hours',
            filter=Q(timesheets__state='APPROVED', timesheets__date__year=curr_year),
            output_field=DecimalField(max_digits=8, decimal_places=2)
        ),
    )