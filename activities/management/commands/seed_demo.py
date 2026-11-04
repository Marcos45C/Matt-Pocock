from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from activities.models import Activity, DemoSeed, Registration
from activities.services import register

PASSWORD = "untdf-demo-2026"

def parse_reference(value):
    if not value:
        return timezone.now()
    result = parse_datetime(value)
    if result is None or timezone.is_naive(result):
        raise CommandError("--reference-time requiere ISO 8601 con zona horaria.")
    return result

class Command(BaseCommand):
    help = "Completa datos ficticios faltantes sin cambiar datos existentes."
    def add_arguments(self, parser):
        parser.add_argument("--reference-time")
    @transaction.atomic
    def handle(self, *args, **options):
        reference = parse_reference(options.get("reference_time"))
        seed, _ = DemoSeed.objects.get_or_create(key="untdf-demo", defaults={"reference_time": reference})
        reference = seed.reference_time
        User = get_user_model()
        users = {}
        for username in ["ana", "bruno", "docente", "docente1", "docente2"]:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(PASSWORD)
                user.is_staff = username in {"docente", "docente1", "docente2"}
                user.is_superuser = username == "docente"
                user.save()
            users[username] = user
        for username in ("docente1", "docente2"):
            if not users[username].is_staff:
                raise CommandError(f"La cuenta {username} existente no es staff; se conservó sin cambios.")
        scenarios = [
            ("taller", "Taller de agentes", 48, 4, True),
            ("proxima", "Clínica de Django", 12, 3, True),
            ("completa", "Laboratorio de SDD", 72, 1, True),
            ("deshabilitada", "Encuentro deshabilitado", 96, 4, False),
            ("iniciada", "Actividad ya iniciada", -2, 3, True),
        ]
        activities = {}
        for index, (key, title, hours, capacity, active) in enumerate(scenarios):
            activity, _ = Activity.objects.get_or_create(seed_key=key, defaults={"responsible": users["docente1" if index % 2 == 0 else "docente2"], "title": title, "description": "Actividad ficticia para practicar el desarrollo asistido por agentes en la UNTDF.", "starts_at": reference + timedelta(hours=hours), "capacity": capacity, "is_active": active})
            activities[key] = activity
        for username, key in [("ana", "taller"), ("ana", "proxima"), ("bruno", "completa"), ("bruno", "taller")]:
            activity = activities[key]
            if Registration.objects.filter(student=users[username], activity=activity).exists():
                continue
            result = register(student=users[username], activity_id=activity.pk, now=reference)
            if result != "registered":
                self.stderr.write(f"No se completó {username}/{key}: {result}; datos existentes preservados.")
        self.stdout.write(self.style.SUCCESS(f"Datos preparados. Ancla conservada: {reference.isoformat()}"))
