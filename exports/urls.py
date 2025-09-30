# exports/urls.py
from django.urls import path
from . import views

app_name = "exports"
urlpatterns = [
    path("projects/pdf/", views.projects_table_pdf, name="projects_table_pdf"),
    path("projects/excel/", views.projects_table_excel, name="projects_table_excel"),
]
