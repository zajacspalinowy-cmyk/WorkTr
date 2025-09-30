from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path("", views.project_list, name="list"),
    path("new/", views.project_create, name="create"),
    path("locations/quick-add/", views.location_quick_add, name="location_quick_add"),  # <— NOWE
    path("<int:pk>/", views.project_detail, name="detail"),
]