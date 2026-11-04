from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import RegistrationForm
from .models import Registration
from .services import CANCELLATION_WINDOW_HOURS, MESSAGES, can_cancel, cancel_registration, register, set_activity_enabled, with_availability

SUCCESS_RESULTS = {"registered", "cancelled", "enabled", "disabled_activity"}

def flash_result(request, result):
    severity = "success" if result in SUCCESS_RESULTS else "warning"
    messages.info(request, MESSAGES[result], extra_tags=f"{result} {severity}")

@login_required
def catalog(request):
    # El GROUP BY de annotate() ignora Meta.ordering; el orden explícito sostiene la agrupación por día.
    activities = list(
        with_availability()
        .filter(is_active=True, starts_at__gt=timezone.now())
        .order_by("starts_at", "pk")
    )
    return render(request, "activities/catalog.html", {"activities": activities})

@login_required
def detail(request, pk):
    activity = get_object_or_404(with_availability(), pk=pk)
    registration = Registration.objects.filter(activity=activity, student=request.user).first()
    now = timezone.now()
    open_for_registration = activity.is_active and activity.starts_at > now and activity.available > 0
    return render(request, "activities/detail.html", {"activity": activity, "registration": registration, "can_register": open_for_registration and registration is None, "can_cancel": can_cancel(registration, now), "cancellation_window_hours": CANCELLATION_WINDOW_HOURS, "form": RegistrationForm()})

@login_required
@require_POST
def enroll(request, pk):
    form = RegistrationForm(request.POST)
    if form.is_valid():
        result = register(student=request.user, activity_id=pk)
        flash_result(request, result)
    return redirect("activity_detail", pk=pk)

@login_required
@require_POST
def cancel(request, pk):
    result = cancel_registration(student=request.user, activity_id=pk)
    flash_result(request, result)
    return redirect("activity_detail", pk=pk)

@login_required
def mine(request):
    now = timezone.now()  # Un solo instante para todas las filas.
    registrations = Registration.objects.filter(student=request.user).select_related("activity")
    rows = [{"registration": registration, "can_cancel": can_cancel(registration, now)} for registration in registrations]
    return render(request, "activities/mine.html", {"rows": rows})

@login_required
def teacher_activities(request):
    if not request.user.is_staff:
        raise PermissionDenied
    activities = with_availability().filter(responsible=request.user).order_by("starts_at", "pk")
    return render(request, "activities/teacher_activities.html", {"activities": activities})

@login_required
@require_POST
def change_activity_enabled(request, pk, enabled):
    if not request.user.is_staff:
        raise PermissionDenied
    if not enabled:
        activity = get_object_or_404(with_availability().filter(responsible=request.user), pk=pk)
        if request.POST.get("confirm") != "yes" or request.session.get("confirm_disable_activity") != pk:
            request.session["confirm_disable_activity"] = pk
            return render(request, "activities/confirm_disable_activity.html", {"activity": activity})
        request.session.pop("confirm_disable_activity", None)
    result = set_activity_enabled(teacher=request.user, activity_id=pk, enabled=enabled)
    if result == "not_found":
        raise Http404
    flash_result(request, result)
    return redirect("teacher_activities")

@login_required
def teacher_activity_detail(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    activity = get_object_or_404(with_availability().filter(responsible=request.user), pk=pk)
    registrations = (Registration.objects.filter(activity=activity).select_related("student")
        .order_by(Case(When(cancelled_at__isnull=True, then=Value(0)), default=Value(1), output_field=IntegerField()), "created_at", "pk"))
    # Prototipo descartable: tres variantes en la pantalla docente existente.
    variant = request.GET.get("variant")
    if settings.DEBUG and variant in {"A", "B", "C"}:
        return render(request, "activities/prototype_teacher_detail.html", {"activity": activity, "registrations": registrations, "variant": variant})
    return render(request, "activities/teacher_activity_detail.html", {"activity": activity, "registrations": registrations})
