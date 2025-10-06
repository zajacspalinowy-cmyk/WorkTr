from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("year/<int:year>/", views.year_block, name="year_block"),  # <— HTMX partial
    path("htmx-test/", views.htmx_test, name="htmx_test"),
    path("htmx-ping/", views.htmx_ping, name="htmx_ping"),
]
