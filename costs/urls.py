from django.urls import path
from . import views

app_name = "costs"
urlpatterns = [
    path("new/", views.new_cost, name="new"),
    path("mine/", views.my_costs, name="mine"),
    path("review/", views.review_costs, name="review"),
    path("<int:pk>/approve/", views.approve_cost, name="approve"),
    path("<int:pk>/reject/", views.reject_cost, name="reject"),
]
