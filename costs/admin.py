from django.contrib import admin
from .models import CostItem, ProjectCost

@admin.register(CostItem)
class CostItemAdmin(admin.ModelAdmin):
    list_display = ("name","unit","default_net_price")
    search_fields = ("name",)

@admin.register(ProjectCost)
class ProjectCostAdmin(admin.ModelAdmin):
    list_display = ("project","item","qty","net_price","state","created_by","approved_by","created_at")
    list_filter = ("state","created_at","project")
    search_fields = ("project__number","project__name","item__name")
