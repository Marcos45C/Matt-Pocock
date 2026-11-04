from datetime import timedelta
from django.db import OperationalError, transaction
from django.db.models import Count, F, Q
from django.utils import timezone
from .models import Activity, Registration

CANCELLATION_WINDOW_HOURS = 24
CANCELLATION_WINDOW = timedelta(hours=CANCELLATION_WINDOW_HOURS)

MESSAGES = {
    "enabled": "Actividad habilitada.",
    "disabled_activity": "Actividad deshabilitada; se conservaron las inscripciones vigentes.",
    "registered": "Inscripción confirmada.",
    "already_registered": "Ya estás inscripto en esta actividad.",
    "previously_cancelled": "Cancelaste tu inscripción; no podés volver a inscribirte.",
    "full": "La actividad no tiene cupos disponibles.",
    "started": "La actividad ya comenzó.",
    "disabled": "La actividad está deshabilitada.",
    "not_available": "La actividad no está disponible.",
    "busy": "La base está ocupada. Intentá nuevamente; no se modificaron datos.",
    "cancelled": "Inscripción cancelada. El cupo quedó liberado.",
    "already_cancelled": "Ya cancelaste esta inscripción.",
    "not_registered": "No tenés una inscripción para cancelar en esta actividad.",
    "window_closed": f"Solo podés cancelar hasta {CANCELLATION_WINDOW_HOURS} horas antes del inicio de la actividad.",
}

def with_availability():
    # Solo las inscripciones vigentes ocupan cupo; las canceladas se conservan.
    return Activity.objects.annotate(occupied=Count("registrations", filter=Q(registrations__cancelled_at__isnull=True))).annotate(available=F("capacity") - F("occupied"))

def within_cancellation_window(activity, now=None):
    """Ventana inclusiva, compartida por el servicio y las plantillas."""
    return activity.starts_at - (now or timezone.now()) >= CANCELLATION_WINDOW

def can_cancel(registration, now=None):
    """Una inscripción vigente puede cancelarse solo dentro de la ventana."""
    return registration is not None and registration.cancelled_at is None and within_cancellation_window(registration.activity, now)

def register(*, student, activity_id, now=None):
    try:
        # SQLite adquiere la reserva de escritura ANTES de leer cupos (IMMEDIATE).
        with transaction.atomic():
            activity = Activity.objects.filter(pk=activity_id).first()
            if activity is None:
                return "not_available"
            registration = Registration.objects.filter(student=student, activity=activity).first()
            if registration is not None:
                return "already_registered" if registration.cancelled_at is None else "previously_cancelled"
            if not activity.is_active:
                return "disabled"
            now = now or timezone.now()  # Instante real después de adquirir IMMEDIATE.
            if activity.starts_at <= now:
                return "started"
            if activity.registrations.filter(cancelled_at__isnull=True).count() >= activity.capacity:
                return "full"
            Registration.objects.create(student=student, activity=activity)
            return "registered"
    except OperationalError as error:
        # Solo la contención conocida se vuelve recuperable; otros errores se propagan.
        if "locked" in str(error).lower():
            return "busy"
        raise

def cancel_registration(*, student, activity_id, now=None):
    try:
        # Mismo IMMEDIATE que la inscripción: la reserva de escritura se toma antes de leer.
        with transaction.atomic():
            activity = Activity.objects.filter(pk=activity_id).first()
            if activity is None:
                return "not_available"
            registration = Registration.objects.filter(student=student, activity=activity).first()
            if registration is None:
                return "not_registered"
            if registration.cancelled_at is not None:
                return "already_cancelled"
            now = now or timezone.now()  # Instante real después de adquirir IMMEDIATE.
            if not within_cancellation_window(activity, now):
                return "window_closed"
            registration.cancelled_at = now
            registration.save(update_fields=["cancelled_at"])
            return "cancelled"
    except OperationalError as error:
        if "locked" in str(error).lower():
            return "busy"
        raise


def set_activity_enabled(*, teacher, activity_id, enabled):
    try:
        with transaction.atomic():
            activity = Activity.objects.filter(pk=activity_id, responsible=teacher).first()
            if activity is None:
                return "not_found"
            activity.is_active = enabled
            activity.save(update_fields=["is_active"])
            return "enabled" if enabled else "disabled_activity"
    except OperationalError as error:
        if "locked" in str(error).lower():
            return "busy"
        raise
