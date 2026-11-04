from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

class Activity(models.Model):
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="responsible_activities", verbose_name="responsable", limit_choices_to={"is_staff": True})
    title = models.CharField("título", max_length=160)
    description = models.TextField("descripción")
    starts_at = models.DateTimeField("inicio")
    capacity = models.PositiveIntegerField("capacidad")
    is_active = models.BooleanField("habilitada", default=True)
    seed_key = models.CharField(max_length=40, null=True, blank=True, unique=True, editable=False)
    class Meta:
        ordering = ["starts_at", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(capacity__gt=0), name="positive_capacity")]
        verbose_name = "actividad"
    def __str__(self):
        return self.title
    def clean(self):
        if self.pk and self.capacity < self.registrations.filter(cancelled_at__isnull=True).count():
            raise ValidationError({"capacity": "No puede reducir la capacidad por debajo de las inscripciones vigentes."})

class Registration(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField("cancelación", null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "activity"], name="one_registration_per_student_activity")]
        ordering = ["-created_at", "-pk"]
        verbose_name = "inscripción"
    def __str__(self):
        return f"{self.student} — {self.activity}"

class DemoSeed(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    reference_time = models.DateTimeField()
