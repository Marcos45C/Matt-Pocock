from contextlib import contextmanager
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from activities.models import Activity
from activities.services import cancel_registration, register

NOW = datetime(2030, 10, 1, 12, tzinfo=dt_timezone.utc)

@contextmanager
def freeze_view_clock(client, moment):
    """Fija el reloj de las vistas sin expirar la sesión de prueba.

    `activities.views.timezone` es el módulo compartido `django.utils.timezone`,
    que también decide la expiración de la sesión. Por eso se extiende el
    vencimiento antes de parchear el reloj.
    """
    session = client.session
    session.set_expiry(moment + timedelta(days=100))
    session.save()
    with patch("activities.views.timezone.now", return_value=moment):
        yield

def login_teacher(client):
    """Crea el superusuario docente y lo deja autenticado."""
    teacher = get_user_model().objects.create_superuser("teacher", "teacher@example.test", "pass")
    client.force_login(teacher)
    return teacher

def activity(**kwargs):
    responsible, _ = get_user_model().objects.get_or_create(username="responsable-test", defaults={"is_staff": True})
    values = dict(responsible=responsible, title="Práctica", description="Datos de prueba", starts_at=NOW+timedelta(hours=48), capacity=2)
    values.update(kwargs)
    return Activity.objects.create(**values)

class BaseCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ana = User.objects.create_user("ana", password="test-pass")
        self.bruno = User.objects.create_user("bruno", password="test-pass")
        self.activity = activity()
    def enroll(self, user=None, **kwargs):
        return register(student=user or self.ana, activity_id=self.activity.pk, now=NOW, **kwargs)
    def cancel(self, user=None, **kwargs):
        kwargs.setdefault("now", NOW)
        return cancel_registration(student=user or self.ana, activity_id=self.activity.pk, **kwargs)
