from django.contrib import admin
from .models import Project, Location

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('number','name','client_name','location','date_received','date_due','status')
    search_fields = ('number','name','client_name','d_number')
    list_filter = ('status','date_received','date_due','location')

admin.site.register(Location)