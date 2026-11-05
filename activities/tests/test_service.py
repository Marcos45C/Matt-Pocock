from datetime import timedelta
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, transaction
from activities.models import Registration
from activities.services import cancel_registration, register, with_availability
from .support import NOW, BaseCase, activity

class ServiceTests(BaseCase):
    def test_cancellation_keeps_the_registration_and_frees_the_seat(self):
        self.enroll()
        self.assertEqual(self.cancel(), "cancelled")
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 2)
    def test_cancellation_accepts_exactly_24_hours_before_start(self):
        self.enroll()
        self.activity.starts_at = NOW + timedelta(hours=24)
        self.activity.save()
        self.assertEqual(self.cancel(), "cancelled")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 2)
    def test_cancellation_rejects_one_second_inside_the_window(self):
        self.enroll()
        self.activity.starts_at = NOW + timedelta(hours=24) - timedelta(seconds=1)
        self.activity.save()
        self.assertEqual(self.cancel(), "window_closed")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
    def test_cancellation_rejects_started_or_past_activity(self):
        self.enroll()
        self.activity.starts_at = NOW
        self.activity.save()
        self.assertEqual(self.cancel(), "window_closed")
        self.activity.starts_at = NOW - timedelta(days=1)
        self.activity.save()
        self.assertEqual(self.cancel(), "window_closed")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
    def test_disabled_activity_still_allows_cancellation(self):
        self.enroll()
        self.activity.is_active = False
        self.activity.save()
        self.assertEqual(self.cancel(), "cancelled")
    def test_cancelling_someone_elses_registration_changes_nothing(self):
        self.enroll(self.bruno)
        self.assertEqual(self.cancel(), "not_registered")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
    def test_cancelling_an_unknown_activity_is_not_available(self):
        self.assertEqual(cancel_registration(student=self.ana, activity_id=999999, now=NOW), "not_available")
    def test_repeated_cancellation_keeps_the_first_instant(self):
        self.enroll()
        self.assertEqual(self.cancel(), "cancelled")
        self.assertEqual(self.cancel(now=NOW + timedelta(hours=1)), "already_cancelled")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 2)
    def test_cancellation_busy_is_recoverable_and_other_errors_propagate(self):
        self.enroll()
        with patch("activities.services.Activity.objects.filter", side_effect=OperationalError("database is locked")):
            self.assertEqual(self.cancel(), "busy")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
        with patch("activities.services.Activity.objects.filter", side_effect=OperationalError("broken schema")):
            with self.assertRaises(OperationalError): self.cancel()
    def test_capacity_validation_and_seats_count_only_current_registrations(self):
        self.enroll(); self.cancel()
        self.activity.capacity = 1
        self.activity.full_clean()
        self.assertEqual(self.enroll(self.bruno), "registered")
    def test_success_and_availability(self):
        self.assertEqual(self.enroll(), "registered")
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
    def test_cancellation_targets_the_current_registration_even_if_another_row_is_newer(self):
        self.enroll()
        current=Registration.objects.get()
        Registration.objects.create(student=self.ana,activity=self.activity,cancelled_at=NOW)
        self.assertEqual(self.cancel(), "cancelled")
        current.refresh_from_db()
        self.assertEqual(current.cancelled_at, NOW)
        self.assertEqual(Registration.objects.filter(cancelled_at__isnull=True).count(), 0)
    def test_duplicate_even_when_now_full_or_started(self):
        self.enroll()
        self.activity.capacity=1; self.activity.starts_at=NOW; self.activity.is_active=False; self.activity.save()
        self.assertEqual(self.enroll(), "already_registered")
        self.assertEqual(Registration.objects.count(), 1)
    def test_reregistration_creates_a_new_row_and_keeps_the_cancelled_one(self):
        self.enroll()
        cancelled=Registration.objects.get()
        self.cancel()
        self.assertEqual(self.enroll(), "registered")
        self.assertEqual(Registration.objects.count(), 2)
        self.assertEqual(Registration.objects.filter(student=self.ana,activity=self.activity,cancelled_at__isnull=True).count(), 1)
        self.assertTrue(Registration.objects.filter(pk=cancelled.pk,cancelled_at=NOW).exists())
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
    def test_reregistration_has_no_limit(self):
        for _ in range(2):
            self.assertEqual(self.enroll(), "registered")
            self.assertEqual(self.cancel(), "cancelled")
        self.assertEqual(self.enroll(), "registered")
        self.assertEqual(Registration.objects.count(), 3)
        self.assertEqual(Registration.objects.filter(cancelled_at__isnull=True).count(), 1)
        self.assertEqual(with_availability().get(pk=self.activity.pk).available, 1)
    def test_reregistration_is_rejected_when_activity_is_full(self):
        self.enroll(); self.cancel()
        self.activity.capacity=1; self.activity.save()
        self.assertEqual(self.enroll(self.bruno), "registered")
        self.assertEqual(self.enroll(), "full")
        self.assertEqual(Registration.objects.count(), 2)
        self.assertEqual(Registration.objects.filter(cancelled_at__isnull=True).count(), 1)
    def test_reregistration_is_rejected_when_activity_is_disabled(self):
        self.enroll(); self.cancel()
        self.activity.is_active=False; self.activity.save()
        self.assertEqual(self.enroll(), "disabled")
        self.assertEqual(Registration.objects.count(), 1)
    def test_reregistration_is_rejected_when_activity_started(self):
        self.enroll(); self.cancel()
        self.activity.starts_at=NOW; self.activity.save()
        self.assertEqual(self.enroll(), "started")
        self.assertEqual(Registration.objects.count(), 1)
    def test_full(self):
        self.activity.capacity=1; self.activity.save(); self.enroll()
        self.assertEqual(self.enroll(self.bruno), "full")
        self.assertEqual(Registration.objects.count(), 1)
    def test_exact_start_rejected(self):
        self.activity.starts_at=NOW; self.activity.save()
        self.assertEqual(self.enroll(), "started")
        self.assertFalse(Registration.objects.exists())
    def test_past_rejected(self):
        self.activity.starts_at=NOW-timedelta(seconds=1); self.activity.save()
        self.assertEqual(self.enroll(), "started")
    def test_disabled(self):
        self.activity.is_active=False; self.activity.save()
        self.assertEqual(self.enroll(), "disabled")
        self.assertFalse(Registration.objects.exists())
    def test_unknown_activity(self):
        self.assertEqual(register(student=self.ana, activity_id=999999, now=NOW), "not_available")
    def test_capacity_validation(self):
        self.enroll(); self.enroll(self.bruno)
        self.activity.capacity=1
        with self.assertRaises(ValidationError): self.activity.full_clean()
    def test_partial_unique_constraint_allows_many_cancelled_and_rejects_two_current(self):
        Registration.objects.create(student=self.ana,activity=self.activity,cancelled_at=NOW)
        Registration.objects.create(student=self.ana,activity=self.activity,cancelled_at=NOW+timedelta(hours=1))
        Registration.objects.create(student=self.ana,activity=self.activity)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Registration.objects.create(student=self.ana,activity=self.activity)
    def test_positive_capacity_database_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic(): activity(capacity=0)
    def test_busy_is_recoverable_other_errors_propagate(self):
        with patch("activities.services.Activity.objects.filter", side_effect=OperationalError("database is locked")):
            self.assertEqual(self.enroll(), "busy")
        with patch("activities.services.Activity.objects.filter", side_effect=OperationalError("broken schema")):
            with self.assertRaises(OperationalError): self.enroll()
