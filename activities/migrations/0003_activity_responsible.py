from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_responsible(apps, schema_editor):
    Activity = apps.get_model("activities", "Activity")
    if not Activity.objects.using(schema_editor.connection.alias).exists():
        return
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    users = User.objects.using(schema_editor.connection.alias)
    responsible = users.filter(is_staff=True).order_by("pk").first()
    if responsible is None:
        username = "responsable-migracion"
        suffix = 0
        while users.filter(username=username).exists():
            suffix += 1
            username = f"responsable-migracion-{suffix}"
        responsible = users.create(username=username, is_staff=True, password="!")
    Activity.objects.using(schema_editor.connection.alias).filter(responsible__isnull=True).update(responsible=responsible)


class Migration(migrations.Migration):
    dependencies = [("activities", "0002_registration_cancelled_at"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name="activity", name="responsible", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="responsible_activities", to=settings.AUTH_USER_MODEL, verbose_name="responsable", limit_choices_to={"is_staff": True})),
        migrations.RunPython(assign_responsible, migrations.RunPython.noop),
        migrations.AlterField(model_name="activity", name="responsible", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="responsible_activities", to=settings.AUTH_USER_MODEL, verbose_name="responsable", limit_choices_to={"is_staff": True})),
    ]
