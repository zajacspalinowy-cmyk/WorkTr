from django.db import models
from django.conf import settings
from projects.models import Project

# Create your models here.


class CostItem(models.Model):
    name=models.CharField(max_length=120)
    unit=models.CharField(max_length=20,default='pcs')
    default_net_price=models.DecimalField(max_digits=10,decimal_places=2,default=0)

    def __str__(self):
        return  self.name

class ProjectCost(models.Model):

    class State (models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name="costs")
    item = models.ForeignKey(CostItem, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    net_price = models.DecimalField(max_digits=10, decimal_places=2)  # można prefill
    note = models.CharField(max_length=255, blank=True)

    state = models.CharField(max_length=10, choices=State.choices, default=State.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name="costs_created")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="costs_approved")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    @property
    def net_sum(self):
        return self.qty * self.net_price

    class Meta:
        permissions = [
            ("review_costs", "Może przeglądać i akceptować koszty"),
        ]
