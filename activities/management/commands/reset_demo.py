from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from activities.models import Activity, DemoSeed
from .seed_demo import parse_reference

class Command(BaseCommand):
    help = "Borra solo actividades identificadas de la demo, sus inscripciones y ancla; conserva cuentas y actividades ajenas."
    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument("--reference-time")
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(f"Base destino: {settings.DATABASES['default']['NAME']}")
        self.stdout.write("Efecto: elimina las 5 actividades ficticias y sus inscripciones; recalcula horarios. No elimina cuentas ni actividades ajenas.")
        if not options["confirm"]:
            raise CommandError("Sin cambios. Lea los efectos y repita con --confirm.")
        reference = parse_reference(options.get("reference_time"))
        Activity.objects.filter(seed_key__in=["taller", "proxima", "completa", "deshabilitada", "iniciada"]).delete()
        DemoSeed.objects.filter(key="untdf-demo").delete()
        call_command("seed_demo", reference_time=reference.isoformat(), stdout=self.stdout)
