# timesheets/urls.py
from django.urls import path
from timesheets import views

app_name = "timesheets"

urlpatterns = [
    path("new-bulk/", views.new_bulk_timesheet, name="new_bulk"),
    path("month-grid/", views.month_grid, name="month_grid"),
    path("drafts/", views.draft_list, name="draft_list"),              # NEW: partial koszyka
    path("submit/", views.submit_entries, name="submit_entries"),      # NEW: wysłanie do akceptacji
    path("mine/", views.my_entries, name="mine"),
    path("review/", views.review_entries, name="review"),
    path("approve/<int:entry_id>/", views.approve_entry, name="approve"),
    path("reject/<int:entry_id>/", views.reject_entry, name="reject"),
]
