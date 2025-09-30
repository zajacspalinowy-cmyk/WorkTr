from django.urls import path
from . import views

app_name = "timesheets"
urlpatterns = [
    path("new-bulk/", views.new_bulk_timesheet, name="new_bulk"),
    path("mine/", views.my_entries, name="my_entries"),
    path("review/", views.review_entries, name="review"),
    path("<int:pk>/approve/", views.approve_entry, name="approve"),
    path("<int:pk>/reject/", views.reject_entry, name="reject"),
]