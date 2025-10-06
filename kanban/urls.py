from django.urls import path
from . import views

app_name = "kanban"

# kanban/urls.py
urlpatterns = [
    path("", views.board, name="board"),
    path("archive/", views.archive, name="archive"),
    path("archive-project/<int:project_id>/", views.archive_project, name="archive_project"),
    path("unarchive-project/<int:project_id>/", views.unarchive_project, name="unarchive_project"),  # NOWE
    path("change-status/<int:project_id>/", views.change_status, name="change_status"),
    path("drag-move/", views.drag_move, name="drag_move"),
]