from django.urls import path
from . import views
app_name = "dashboard"
urlpatterns = [ path("", views.home, name="home"),
                path("htmx-test/", views.htmx_test, name="htmx_test"),  # NOWE
                path("htmx-ping/", views.htmx_ping, name="htmx_ping"),  # NOWE

                ]
