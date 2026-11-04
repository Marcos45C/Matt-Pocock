from datetime import timedelta
from unittest.mock import Mock, patch
from django.test import Client
from django.utils import timezone
from activities.models import Registration
from activities.services import register
from .support import NOW, BaseCase, activity, freeze_view_clock

class ViewTests(BaseCase):
    def test_session_login_and_logout_post(self):
        self.assertRedirects(self.client.get("/activities/"), "/accounts/login/?next=/activities/")
        response=self.client.post("/accounts/login/?next=/activities/", {"username":"ana","password":"test-pass","next":"/activities/"})
        self.assertRedirects(response, "/activities/")
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 405)
        self.assertRedirects(self.client.post("/accounts/logout/"), "/accounts/login/")
    def test_csrf_and_no_get_mutation(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.ana)
        url=f"/activities/{self.activity.pk}/register/"
        self.assertEqual(client.get(url).status_code, 405)
        self.assertEqual(client.post(url).status_code, 403)
        page=client.get(f"/activities/{self.activity.pk}/")
        self.assertEqual(page.status_code, 200)
        with patch("activities.views.register", side_effect=lambda **kwargs: register(now=NOW, **kwargs)):
            response=client.post(url, {"csrfmiddlewaretoken":client.cookies['csrftoken'].value,"student":self.bruno.pk})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Registration.objects.get().student,self.ana)
    def test_cancel_is_post_only_with_csrf_and_uses_session_identity(self):
        self.enroll()
        self.activity.starts_at=timezone.now()+timedelta(hours=48);self.activity.save()
        client=Client(enforce_csrf_checks=True);client.force_login(self.ana)
        url=f"/activities/{self.activity.pk}/cancel/"
        self.assertEqual(client.get(url).status_code,405)
        self.assertEqual(client.post(url).status_code,403)
        client.get(f"/activities/{self.activity.pk}/")
        response=client.post(url,{"csrfmiddlewaretoken":client.cookies['csrftoken'].value,"student":self.bruno.pk})
        self.assertRedirects(response,f"/activities/{self.activity.pk}/")
        registration=Registration.objects.get()
        self.assertEqual(registration.student,self.ana)
        self.assertContains(client.get(f"/activities/{self.activity.pk}/"),"Inscripción cancelada")
        self.assertContains(client.get("/activities/"),"2 cupos disponibles")
    def test_detail_cancel_states(self):
        self.client.force_login(self.ana);self.enroll()
        def page():
            with freeze_view_clock(self.client,NOW):
                return self.client.get(f"/activities/{self.activity.pk}/")
        self.assertContains(page(),"Cancelar inscripción")
        self.activity.starts_at=NOW+timedelta(hours=2);self.activity.save()
        response=page()
        self.assertNotContains(response,"Cancelar inscripción");self.assertContains(response,"hasta 24 horas antes del inicio")
        self.activity.starts_at=NOW+timedelta(hours=48);self.activity.save()
        self.assertEqual(self.cancel(),"cancelled")
        self.assertEqual(self.cancel(now=NOW+timedelta(hours=1)),"already_cancelled")
        response=page()
        self.assertContains(response,"Inscripción cancelada el 01/10/2030 09:00")
        self.assertNotContains(response,"Cancelar inscripción");self.assertNotContains(response,"Inscribirme")
    def test_reregistration_over_cancelled_explains_and_creates_no_row(self):
        self.client.force_login(self.ana); self.enroll(); self.cancel()
        with freeze_view_clock(self.client, NOW):
            page=self.client.get(f"/activities/{self.activity.pk}/")
            response=self.client.post(f"/activities/{self.activity.pk}/register/", follow=True)
        self.assertContains(page,"No podés volver a inscribirte en esta actividad.")
        self.assertNotContains(page,"Inscribirme")
        self.assertContains(response,"Cancelaste tu inscripción; no podés volver a inscribirte.")
        self.assertNotContains(response,"Ya estás inscripto")
        self.assertEqual(Registration.objects.count(),1)
    def test_http_reregistration_blocked_when_full_disabled_or_started(self):
        self.client.force_login(self.ana)
        configurations={"llena":dict(capacity=1),"deshabilitada":dict(is_active=False),"iniciada":dict(starts_at=timezone.now()-timedelta(hours=1))}
        for name,config in configurations.items():
            with self.subTest(name):
                target=activity(title=name,**config)
                Registration.objects.create(student=self.ana,activity=target,cancelled_at=NOW)
                if name=="llena": Registration.objects.create(student=self.bruno,activity=target)
                before=Registration.objects.count()
                response=self.client.post(f"/activities/{target.pk}/register/",follow=True)
                self.assertContains(response,"Cancelaste tu inscripción; no podés volver a inscribirte.")
                self.assertEqual(Registration.objects.count(),before)
    def test_catalog_filters_and_full_visible(self):
        self.client.force_login(self.ana)
        full=activity(title="Completa",capacity=1)
        Registration.objects.create(student=self.ana,activity=full)
        activity(title="Oculta",is_active=False); activity(title="Pasada",starts_at=NOW-timedelta(hours=2))
        with freeze_view_clock(self.client,NOW): response=self.client.get("/activities/")
        self.assertContains(response,"Completa");self.assertNotContains(response,"Oculta");self.assertNotContains(response,"Pasada")
    def test_catalog_orders_by_start_time(self):
        self.client.force_login(self.ana)
        early=NOW+timedelta(days=1,hours=-3)    # 02/10 09:00
        late=NOW+timedelta(days=1,hours=6)      # 02/10 18:00
        next_day=NOW+timedelta(days=3,hours=-2) # 04/10 10:00
        # Creadas al revés: el orden de inserción no debe filtrarse a la página.
        activity(title="Domingo",starts_at=next_day)
        activity(title="Tarde",starts_at=late)
        activity(title="Mañana",starts_at=early)
        html=self.client.get("/activities/").content.decode()
        self.assertLess(html.index("Mañana"),html.index("Tarde"))
        self.assertLess(html.index("Tarde"),html.index("Domingo"))
    def test_mine_shows_each_cancellation_state(self):
        self.client.force_login(self.ana); self.enroll()
        def page():
            with freeze_view_clock(self.client, NOW):
                return self.client.get("/my-registrations/")
        response=page()
        self.assertContains(response,"Cancelar inscripción");self.assertContains(response,"confirm('¿Cancelar tu inscripción?")
        self.activity.starts_at=NOW+timedelta(hours=2);self.activity.save()
        self.assertNotContains(page(),"Cancelar inscripción")
        self.activity.starts_at=NOW+timedelta(hours=48);self.activity.save()
        self.assertEqual(self.cancel(),"cancelled")
        response=page()
        self.assertContains(response,"Inscripción cancelada el 01/10/2030 09:00")
        self.assertNotContains(response,"Cancelar inscripción")
    def test_mine_evaluates_the_window_at_a_single_instant(self):
        self.client.force_login(self.ana)
        for title in ("Taller","Clínica"):
            edge=activity(title=title,starts_at=NOW+timedelta(hours=24))
            Registration.objects.create(student=self.ana,activity=edge)
        session=self.client.session
        session.set_expiry(NOW+timedelta(days=100))
        session.save()
        # La primera lectura ve el borde abierto; la segunda, tres horas después, lo ve cerrado.
        # Se reemplaza el reloj de la vista (no el módulo compartido) porque la carga de
        # sesión también lee el reloj real y consumiría el primer valor.
        clock=Mock(); clock.now.side_effect=[NOW, NOW+timedelta(hours=3)]
        with patch("activities.views.timezone", clock):
            response=self.client.get("/my-registrations/")
        self.assertContains(response,"Cancelar inscripción",count=2)
    def test_mine_isolated_between_students_including_cancelled(self):
        self.enroll(); other=activity(title="Cancelada de Bruno")
        Registration.objects.create(student=self.bruno,activity=other,cancelled_at=NOW)
        self.assertEqual(self.cancel(),"cancelled")
        self.client.force_login(self.ana)
        with freeze_view_clock(self.client,NOW): response=self.client.get("/my-registrations/")
        self.assertContains(response,"Inscripción cancelada el 01/10/2030 09:00")
        self.assertNotContains(response,"Cancelada de Bruno")
    def test_cancel_from_mine_lands_on_detail_with_message(self):
        self.client.force_login(self.ana); self.enroll()
        with freeze_view_clock(self.client,NOW):
            response=self.client.post(f"/activities/{self.activity.pk}/cancel/",follow=True)
            self.assertRedirects(response,f"/activities/{self.activity.pk}/")
            self.assertContains(response,"Inscripción cancelada. El cupo quedó liberado.")
            self.assertEqual(Registration.objects.get().cancelled_at,NOW)
    def test_mine_isolated_and_retains_past_disabled(self):
        self.enroll(); other=activity(title="Privada Bruno");Registration.objects.create(student=self.bruno,activity=other)
        self.activity.is_active=False;self.activity.starts_at=NOW-timedelta(hours=2);self.activity.save()
        self.client.force_login(self.ana); response=self.client.get("/my-registrations/")
        self.assertContains(response,"Práctica");self.assertNotContains(response,"Privada Bruno")
    def test_teacher_list_is_private_and_includes_all_own_activities(self):
        from django.contrib.auth import get_user_model
        User=get_user_model()
        teacher=User.objects.create_user("docente1",is_staff=True)
        other=User.objects.create_user("docente2",is_staff=True)
        activity(title="Propia pasada",responsible=teacher,is_active=False,starts_at=NOW-timedelta(days=1))
        activity(title="Ajena",responsible=other)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get("/teacher/activities/").status_code,403)
        self.client.force_login(teacher)
        response=self.client.get("/teacher/activities/")
        self.assertContains(response,"Propia pasada")
        self.assertContains(response,"Deshabilitada")
        self.assertContains(response,"0 / 2")
        self.assertNotContains(response,"Ajena")
    def test_teacher_list_empty_and_requires_authentication(self):
        self.assertRedirects(self.client.get("/teacher/activities/"),"/accounts/login/?next=/teacher/activities/")
        from django.contrib.auth import get_user_model
        teacher=get_user_model().objects.create_user("sin-actividades",is_staff=True)
        self.client.force_login(teacher)
        self.assertContains(self.client.get("/teacher/activities/"),"No tenés actividades asignadas")
    def test_teacher_disables_activity_and_preserves_student_registration(self):
        from django.contrib.auth import get_user_model
        teacher=get_user_model().objects.create_user('docente',is_staff=True)
        self.activity.responsible=teacher; self.activity.save()
        self.enroll()
        cancelled_student=get_user_model().objects.create_user('cancelado')
        Registration.objects.create(student=cancelled_student,activity=self.activity,cancelled_at=NOW)
        self.client.force_login(teacher)
        page=self.client.get('/teacher/activities/')
        self.assertContains(page,'1 / 2 inscripciones vigentes')
        url=f'/teacher/activities/{self.activity.pk}/disable/'
        confirmation=self.client.post(url)
        self.assertContains(confirmation,'Se conservarán 1 inscripciones vigentes')
        self.assertContains(self.client.get('/teacher/activities/'),'Habilitada')
        response=self.client.post(url, {'confirm': 'yes'}, follow=True)
        self.assertContains(response,'Deshabilitada')
        self.client.force_login(self.ana)
        self.assertNotContains(self.client.get('/activities/'),'Práctica')
        with freeze_view_clock(self.client,NOW):
            self.assertContains(self.client.get(f'/activities/{self.activity.pk}/'),'Cancelar inscripción')
            self.assertContains(self.client.post(f'/activities/{self.activity.pk}/cancel/',follow=True),'Inscripción cancelada')
        self.client.force_login(self.bruno)
        self.assertContains(self.client.post(f'/activities/{self.activity.pk}/register/',follow=True),'La actividad está deshabilitada.')
    def test_teacher_changes_only_own_activity_with_post_and_csrf(self):
        from django.contrib.auth import get_user_model
        User=get_user_model()
        teacher=User.objects.create_user('responsable',is_staff=True)
        other=User.objects.create_user('otro',is_staff=True)
        self.activity.responsible=teacher; self.activity.save()
        client=Client(enforce_csrf_checks=True)
        disable=f'/teacher/activities/{self.activity.pk}/disable/'
        enable=f'/teacher/activities/{self.activity.pk}/enable/'
        client.force_login(self.ana)
        client.get(f'/activities/{self.activity.pk}/')
        self.assertEqual(client.post(disable,{'csrfmiddlewaretoken':client.cookies['csrftoken'].value}).status_code,403)
        client.force_login(other)
        client.get('/teacher/activities/')
        self.assertEqual(client.post(disable,{'csrfmiddlewaretoken':client.cookies['csrftoken'].value}).status_code,404)
        self.assertEqual(client.post(enable,{'csrfmiddlewaretoken':client.cookies['csrftoken'].value}).status_code,404)
        client.force_login(teacher)
        self.assertEqual(client.get(disable).status_code,405)
        self.assertEqual(client.get(enable).status_code,405)
        self.assertEqual(client.post(disable).status_code,403)
        client.get('/teacher/activities/')
        token=client.cookies['csrftoken'].value
        confirmation=client.post(disable,{'csrfmiddlewaretoken':token, 'confirm':'yes'})
        self.assertContains(confirmation,'Confirmar deshabilitación')
        self.assertContains(client.get('/teacher/activities/'),'Habilitada')
        self.assertEqual(client.post(disable).status_code,403)
        self.assertEqual(client.post(disable,{'csrfmiddlewaretoken':token, 'confirm':'yes'}).status_code,302)
        self.assertContains(client.get('/teacher/activities/'),'Deshabilitada')
        self.assertEqual(client.post(enable,{'csrfmiddlewaretoken':token}).status_code,302)
        self.assertContains(client.get('/teacher/activities/'),'Habilitada')
        self.assertContains(client.post(disable,{'csrfmiddlewaretoken':token, 'confirm':'yes'}),'Confirmar deshabilitación')
        self.assertContains(client.get('/teacher/activities/'),'Habilitada')
    def test_reenable_preserves_capacity_and_started_rules(self):
        from django.contrib.auth import get_user_model
        teacher=get_user_model().objects.create_user('docente-reglas',is_staff=True)
        self.activity.responsible=teacher; self.activity.capacity=1; self.activity.is_active=False; self.activity.save()
        Registration.objects.create(student=self.ana,activity=self.activity)
        self.client.force_login(teacher)
        self.client.post(f'/teacher/activities/{self.activity.pk}/enable/')
        self.client.force_login(self.bruno)
        self.assertContains(self.client.post(f'/activities/{self.activity.pk}/register/',follow=True),'La actividad no tiene cupos disponibles.')
        self.activity.starts_at=timezone.now()-timedelta(hours=1); self.activity.is_active=False; self.activity.save()
        self.client.force_login(teacher)
        self.client.post(f'/teacher/activities/{self.activity.pk}/enable/')
        self.client.force_login(self.bruno)
        self.assertContains(self.client.post(f'/activities/{self.activity.pk}/register/',follow=True),'La actividad ya comenzó.')

    def test_teacher_can_disable_after_activity_started(self):
        from django.contrib.auth import get_user_model
        teacher=get_user_model().objects.create_user('docente-pasada',is_staff=True)
        self.activity.responsible=teacher; self.activity.starts_at=timezone.now()-timedelta(hours=1); self.activity.save()
        self.client.force_login(teacher)
        url=f'/teacher/activities/{self.activity.pk}/disable/'
        self.client.post(url)
        self.client.post(url, {'confirm':'yes'})
        self.assertContains(self.client.get('/teacher/activities/'),'Deshabilitada')
    def test_teacher_opens_own_activity_and_sees_registration_information_in_order(self):
        from django.contrib.auth import get_user_model
        teacher=get_user_model().objects.create_user("docente-detalle",is_staff=True)
        target=activity(title="Actividad histórica",responsible=teacher,is_active=False,starts_at=NOW-timedelta(days=1))
        cancelled=Registration.objects.create(student=self.ana,activity=target,cancelled_at=NOW)
        current=Registration.objects.create(student=self.bruno,activity=target)
        Registration.objects.filter(pk=cancelled.pk).update(created_at=NOW-timedelta(days=1))
        Registration.objects.filter(pk=current.pk).update(created_at=NOW-timedelta(days=2))
        self.client.force_login(teacher)
        listing=self.client.get('/teacher/activities/')
        url=f'/teacher/activities/{target.pk}/'
        self.assertContains(listing,f'href="{url}"')
        response=self.client.get(url)
        self.assertContains(response,'<th>Alumno</th>', html=True)
        self.assertContains(response,'Actividad histórica')
        self.assertContains(response,'Deshabilitada')
        self.assertContains(response,'bruno')
        self.assertContains(response,'ana')
        self.assertContains(response,'30/09/2030 09:00')
        self.assertContains(response,'29/09/2030 09:00')
        self.assertContains(response,'01/10/2030 09:00')
        self.assertContains(response,'Vigente')
        self.assertContains(response,'Cancelada')
        html=response.content.decode()
        self.assertLess(html.index('bruno'),html.index('ana'))
    def test_teacher_detail_requires_staff_and_ownership(self):
        from django.contrib.auth import get_user_model
        User=get_user_model()
        owner=User.objects.create_user("dueño",is_staff=True)
        other=User.objects.create_superuser("otro-docente",password="pass")
        target=activity(responsible=owner)
        Registration.objects.create(student=self.ana,activity=target)
        url=f"/teacher/activities/{target.pk}/"
        self.assertRedirects(self.client.get(url),f"/accounts/login/?next={url}")
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(url).status_code,403)
        self.client.force_login(other)
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get("/teacher/activities/999999/").status_code,404)
        self.client.force_login(owner)
        self.assertContains(self.client.get(url),"ana")
        self.client.post(url,{"student":self.bruno.pk,"cancelled_at":NOW.isoformat()})
        self.assertContains(self.client.get(url),"ana")
        self.assertNotContains(self.client.get(url),"bruno")
        self.assertContains(self.client.get(url),"Vigente")
