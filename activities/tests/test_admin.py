from .support import NOW, BaseCase, login_teacher

class AdminTests(BaseCase):
    def test_admin_rejects_capacity_and_read_only_registration(self):
        self.enroll();self.enroll(self.bruno)
        login_teacher(self.client)
        response=self.client.post(f"/admin/activities/activity/{self.activity.pk}/change/", {"title":"Práctica","description":"Datos","starts_at_0":"2030-10-03","starts_at_1":"09:00:00","capacity":1,"responsible":self.activity.responsible_id,"is_active":"on","_save":"Guardar"})
        self.assertEqual(response.status_code,200);self.assertContains(response,"No puede reducir")
        self.activity.refresh_from_db();self.assertEqual(self.activity.capacity,2)
        self.assertEqual(self.client.get("/admin/activities/registration/add/").status_code,403)
    def test_admin_shows_cancelled_at_in_list_and_detail(self):
        self.enroll();self.cancel()
        login_teacher(self.client)
        registration=self.activity.registrations.get()
        # NOW en UTC 12:00 se lee 09:00 en Ushuaia.
        expected="1 Oct. 2030 09:00"
        self.assertContains(self.client.get("/admin/activities/registration/"),expected)
        self.assertContains(self.client.get(f"/admin/activities/registration/{registration.pk}/change/"),expected)
    def test_admin_registration_stays_read_only(self):
        self.enroll();self.cancel()
        login_teacher(self.client)
        registration=self.activity.registrations.get()
        url=f"/admin/activities/registration/{registration.pk}/change/"
        self.assertEqual(self.client.get("/admin/activities/registration/add/").status_code,403)
        self.assertEqual(self.client.post(f"/admin/activities/registration/{registration.pk}/delete/").status_code,403)
        self.client.post(url,{"student":self.bruno.pk,"activity":self.activity.pk,"_save":"Guardar"})
        registration.refresh_from_db()
        self.assertEqual(registration.student,self.ana);self.assertEqual(registration.cancelled_at,NOW)
    def test_admin_can_reduce_capacity_after_a_cancellation(self):
        self.enroll();self.enroll(self.bruno);self.cancel(self.bruno)
        login_teacher(self.client)
        response=self.client.post(f"/admin/activities/activity/{self.activity.pk}/change/", {"title":"Práctica","description":"Datos","starts_at_0":"2030-10-03","starts_at_1":"09:00:00","capacity":1,"responsible":self.activity.responsible_id,"is_active":"on","_save":"Guardar"})
        self.assertEqual(response.status_code,302)
        self.activity.refresh_from_db();self.assertEqual(self.activity.capacity,1)
    def test_admin_requires_staff_responsible(self):
        login_teacher(self.client)
        response=self.client.post(f"/admin/activities/activity/{self.activity.pk}/change/", {"title":"Práctica","description":"Datos","starts_at_0":"2030-10-03","starts_at_1":"09:00:00","capacity":2,"is_active":"on","responsible":self.ana.pk,"_save":"Guardar"})
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"Seleccione una opción válida")
    def test_admin_cannot_remove_staff_from_responsible(self):
        login_teacher(self.client)
        responsible=self.activity.responsible
        response=self.client.post(f"/admin/auth/user/{responsible.pk}/change/", {"username":responsible.username,"is_active":"on","_save":"Guardar"})
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"Reasigná sus actividades")
        responsible.refresh_from_db()
        self.assertTrue(responsible.is_staff)
    def test_reassignment_preserves_registration_and_state_and_unblocks_deletion(self):
        from django.contrib.auth import get_user_model
        self.enroll()
        self.activity.is_active=False; self.activity.save()
        old=self.activity.responsible
        replacement=get_user_model().objects.create_user("reemplazo",is_staff=True)
        login_teacher(self.client)
        delete_url=f"/admin/auth/user/{old.pk}/delete/"
        self.assertContains(self.client.get(delete_url),"Práctica")
        self.client.post(delete_url,{"post":"yes"})
        self.assertTrue(get_user_model().objects.filter(pk=old.pk).exists())
        response=self.client.post(f"/admin/activities/activity/{self.activity.pk}/change/", {"title":"Práctica","description":"Datos","starts_at_0":"2030-10-03","starts_at_1":"09:00:00","capacity":2,"responsible":replacement.pk,"_save":"Guardar"})
        self.assertEqual(response.status_code,302)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.responsible,replacement)
        self.assertFalse(self.activity.is_active)
        self.assertEqual(self.activity.registrations.count(),1)
        self.client.post(delete_url,{"post":"yes"})
        self.assertFalse(get_user_model().objects.filter(pk=old.pk).exists())
