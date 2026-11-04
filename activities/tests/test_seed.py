from datetime import timedelta
from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from activities.models import Activity, DemoSeed, Registration
from activities.services import cancel_registration
from .support import NOW, BaseCase, activity

class SeedTests(BaseCase):
    def test_seed_idempotent_preserves_changes_and_anchor(self):
        call_command("seed_demo",reference_time=NOW.isoformat(),stdout=StringIO())
        seeded=Activity.objects.get(seed_key="taller");before=seeded.starts_at
        ana=get_user_model().objects.get(username="ana");old_password=ana.password
        seeded.title="Edición docente";seeded.save()
        count=Registration.objects.count()
        call_command("seed_demo",reference_time=(NOW+timedelta(days=3)).isoformat(),stdout=StringIO())
        seeded.refresh_from_db();ana.refresh_from_db()
        self.assertEqual(seeded.title,"Edición docente");self.assertEqual(seeded.starts_at,before)
        self.assertEqual(ana.password,old_password);self.assertEqual(Registration.objects.count(),count)
        self.assertEqual(DemoSeed.objects.get().reference_time,NOW)
    def test_seed_missing_data_does_not_overbook(self):
        call_command("seed_demo",reference_time=NOW.isoformat(),stdout=StringIO())
        seeded=Activity.objects.get(seed_key="taller")
        Registration.objects.filter(activity=seeded,student__username="bruno").delete()
        seeded.capacity=1;seeded.save(); warning=StringIO()
        call_command("seed_demo",stdout=StringIO(),stderr=warning)
        self.assertIn("full",warning.getvalue());self.assertEqual(seeded.registrations.count(),1)
    def test_reset_scoped_and_requires_confirmation(self):
        call_command("seed_demo",reference_time=NOW.isoformat(),stdout=StringIO())
        with self.assertRaises(CommandError):call_command("reset_demo",stdout=StringIO())
        call_command("reset_demo",confirm=True,reference_time=(NOW+timedelta(days=5)).isoformat(),stdout=StringIO())
        self.assertTrue(Activity.objects.filter(pk=self.activity.pk).exists())
        self.assertEqual(DemoSeed.objects.get().reference_time,NOW+timedelta(days=5))
    def test_seed_preserves_cancelled_registration_without_warning(self):
        call_command("seed_demo",reference_time=NOW.isoformat(),stdout=StringIO())
        taller=Activity.objects.get(seed_key="taller")
        ana=get_user_model().objects.get(username="ana")
        self.assertEqual(cancel_registration(student=ana,activity_id=taller.pk,now=NOW),"cancelled")
        warning=StringIO()
        call_command("seed_demo",stdout=StringIO(),stderr=warning)
        registration=Registration.objects.get(activity=taller,student=ana)
        self.assertEqual(registration.cancelled_at,NOW)
        self.assertEqual(taller.registrations.filter(student=ana).count(),1)
        self.assertEqual(taller.registrations.filter(cancelled_at__isnull=True).count(),1)
        self.assertEqual(warning.getvalue(),"")
    def test_reset_deletes_demo_activities_and_cancelled_registrations(self):
        call_command("seed_demo",reference_time=NOW.isoformat(),stdout=StringIO())
        taller=Activity.objects.get(seed_key="taller")
        ana=get_user_model().objects.get(username="ana")
        self.assertEqual(cancel_registration(student=ana,activity_id=taller.pk,now=NOW),"cancelled")
        demo_ids=list(Activity.objects.filter(seed_key__isnull=False).values_list("pk",flat=True))
        call_command("reset_demo",confirm=True,reference_time=NOW.isoformat(),stdout=StringIO())
        self.assertEqual(Activity.objects.filter(pk__in=demo_ids).count(),0)
        self.assertEqual(Registration.objects.filter(activity_id__in=demo_ids).count(),0)
    def test_seed_rejects_naive_reference(self):
        with self.assertRaises(CommandError):call_command("seed_demo",reference_time="2030-01-01T00:00:00",stdout=StringIO())
    def test_seed_assigns_staff_and_preserves_existing_non_staff_account(self):
        User=get_user_model()
        existing=User.objects.create_user("docente",password="original")
        call_command("seed_demo",reference_time=NOW.isoformat(),stdout=StringIO())
        existing.refresh_from_db()
        self.assertFalse(existing.is_staff)
        self.assertTrue(existing.check_password("original"))
        seeded=Activity.objects.filter(seed_key__isnull=False)
        self.assertEqual(seeded.count(),5)
        self.assertEqual(seeded.filter(responsible__is_staff=False).count(),0)
        self.assertGreaterEqual(seeded.values("responsible_id").distinct().count(),2)
