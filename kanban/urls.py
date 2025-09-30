from django.urls import path
from . import views

app_name = "kanban"
urlpatterns = [
    path("", views.board, name="board"),
    path("change-status/<int:pk>/", views.change_status, name="change_status"),

]
