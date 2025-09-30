from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

ROLE_ADMIN = "Administrator"
ROLE_TECH = "Technik"  # spójnie po polsku

ADMIN_CUSTOM_PERMS = [
    "timesheets.review_timesheets",   # <- brakujący przecinek był tutaj
    "costs.review_costs",
    "projects.change_project_status",
]

TECH_MODEL_PERMS = {
    "timesheets.TimesheetEntry": ["add", "view"],
    "costs.ProjectCost": ["add", "view"],
    "projects.Project": ["view"],
}

ADMIN_FULL_MODELS = [
    "projects.Project",
    "projects.Location",
    "timesheets.TimesheetEntry",
    "costs.CostItem",
    "costs.ProjectCost",
]

def get_model(app_model_str):
    app_label, model_name = app_model_str.split(".")
    return apps.get_model(app_label, model_name)

def perms_for_model(app_model_str, actions=("add", "change", "delete", "view")):
    model = get_model(app_model_str)
    ct = ContentType.objects.get_for_model(model)
    codes = [f"{act}_{model._meta.model_name}" for act in actions]
    return list(Permission.objects.filter(content_type=ct, codename__in=codes))

class Command(BaseCommand):
    help = "Initialize default roles and permissions"

    def handle(self, *args, **options):
        # --- ADMIN ---
        admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        admin_perms = []
        for app_model in ADMIN_FULL_MODELS:
            admin_perms += perms_for_model(app_model, ("add", "change", "delete", "view"))

        # Bezpieczne parsowanie 'app_label.codename'
        for perm_path in ADMIN_CUSTOM_PERMS:
            perm_path = perm_path.strip()
            app_label, codename = perm_path.split(".", 1)
            try:
                p = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                admin_perms.append(p)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Brak uprawnienia: {perm_path} (czy wykonałeś migracje dla custom permissions?)"
                ))

        admin_group.permissions.set(set(admin_perms))
        self.stdout.write(self.style.SUCCESS(f"Zaktualizowano grupę: {ROLE_ADMIN}"))

        # --- TECHNIK ---
        # Jeżeli wcześniej utworzyłeś grupę 'Technician', scal i nazwij po polsku
        tech_group = Group.objects.filter(name__in=["Technician", ROLE_TECH]).first()
        if tech_group is None:
            tech_group = Group.objects.create(name=ROLE_TECH)
        elif tech_group.name != ROLE_TECH:
            tech_group.name = ROLE_TECH
            tech_group.save(update_fields=["name"])

        tech_perms = []
        for app_model, acts in TECH_MODEL_PERMS.items():
            tech_perms += perms_for_model(app_model, tuple(acts))
        tech_group.permissions.set(set(tech_perms))
        self.stdout.write(self.style.SUCCESS(f"Zaktualizowano grupę: {ROLE_TECH}"))

        self.stdout.write(self.style.SUCCESS("Gotowe."))
