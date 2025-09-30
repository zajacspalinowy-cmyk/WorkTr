from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import logout
# Create your views here.


def logout_then_login(request):
    logout(request)
    return redirect("accounts:login")