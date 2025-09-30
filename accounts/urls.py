from django.urls import path,reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", __import__("django.contrib.auth.views").contrib.auth.views.LoginView.as_view(
        template_name="accounts/login.html"
    ), name="login"),
    path("logout/", views.logout_then_login, name="logout"),
]