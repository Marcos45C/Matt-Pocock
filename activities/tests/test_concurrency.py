from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connections, close_old_connections
from django.test import TransactionTestCase
from activities.models import Registration
from activities.services import cancel_registration, register, set_activity_enabled, with_availability
from .support import NOW, activity

class ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.ana=get_user_model().objects.create_user("a");self.bruno=get_user_model().objects.create_user("b")
        self.activity=activity(capacity=1)
    def test_default_clock_after_lock_rejects_activity_that_started(self):
        self.activity.starts_at=NOW+timedelta(seconds=1);self.activity.save()
        self.assertFalse(connections["default"].in_atomic_block)
        def after_lock():
            self.assertTrue(connections["default"].in_atomic_block)
            return NOW+timedelta(seconds=2)
        with patch("activities.services.timezone.now",side_effect=after_lock) as clock:
            self.assertEqual(register(student=self.ana,activity_id=self.activity.pk),"started")
            clock.assert_called_once()
        self.assertEqual(Registration.objects.count(),0)
        self.assertEqual(with_availability().get(pk=self.activity.pk).available,1)

    def race(self, calls):
        barrier=Barrier(len(calls))
        def worker(call):
            close_old_connections()
            try:
                database=str(connections["default"].settings_dict["NAME"])
                assert database.endswith("test.sqlite3"), database
                assert "memory" not in database, database
                barrier.wait(timeout=10)
                return call()
            finally:connections["default"].close()
        with ThreadPoolExecutor(max_workers=len(calls)) as executor: return list(executor.map(worker, calls))
    def race_registrations(self, users):
        return self.race([lambda user=user: register(student=user,activity_id=self.activity.pk,now=NOW) for user in users])
    def test_two_students_last_seat(self):
        self.assertCountEqual(self.race_registrations([self.ana,self.bruno]),["registered","full"])
        self.assertEqual(Registration.objects.count(),1)
        self.assertEqual(with_availability().get(pk=self.activity.pk).available,0)
    def test_simultaneous_duplicate(self):
        self.assertCountEqual(self.race_registrations([self.ana,self.ana]),["registered","already_registered"])
        self.assertEqual(Registration.objects.count(),1)

    def test_cancelling_the_last_seat_while_another_student_registers(self):
        self.assertEqual(register(student=self.ana,activity_id=self.activity.pk,now=NOW),"registered")
        outcomes=self.race([
            lambda: cancel_registration(student=self.ana,activity_id=self.activity.pk,now=NOW),
            lambda: register(student=self.bruno,activity_id=self.activity.pk,now=NOW),
        ])
        # Si Bruno se inscribe antes de la cancelación, encuentra el cupo ocupado; si no, entra.
        self.assertIn(sorted(outcomes),[["cancelled","full"],["cancelled","registered"]])
        self.assertLessEqual(Registration.objects.filter(cancelled_at__isnull=True).count(),1)
        self.assertEqual(Registration.objects.get(student=self.ana).cancelled_at,NOW)
        self.assertEqual(with_availability().get(pk=self.activity.pk).available,0 if "registered" in outcomes else 1)

    def test_simultaneous_cancellations_by_the_same_student_keep_one_instant(self):
        self.assertEqual(register(student=self.ana,activity_id=self.activity.pk,now=NOW),"registered")
        later=NOW+timedelta(hours=1)
        outcomes=self.race([
            lambda: cancel_registration(student=self.ana,activity_id=self.activity.pk,now=NOW),
            lambda: cancel_registration(student=self.ana,activity_id=self.activity.pk,now=later),
        ])
        self.assertCountEqual(outcomes,["cancelled","already_cancelled"])
        self.assertEqual(Registration.objects.count(),1)
        # La cancelación perdedora no pisa el instante de la ganadora.
        self.assertEqual(Registration.objects.get(student=self.ana).cancelled_at,NOW if outcomes[0]=="cancelled" else later)

    def test_registration_and_disabling_are_serialized(self):
        teacher=get_user_model().objects.create_user("docente-concurrencia",is_staff=True)
        self.activity.responsible=teacher; self.activity.save()
        outcomes=self.race([
            lambda: register(student=self.ana,activity_id=self.activity.pk,now=NOW),
            lambda: set_activity_enabled(teacher=teacher,activity_id=self.activity.pk,enabled=False),
        ])
        self.assertIn(outcomes,[["registered","disabled_activity"],["disabled","disabled_activity"]])
        self.assertFalse(with_availability().get(pk=self.activity.pk).is_active)
        self.assertEqual(Registration.objects.count(),1 if outcomes[0]=="registered" else 0)
        self.assertEqual(register(student=self.bruno,activity_id=self.activity.pk,now=NOW),"disabled")
