from django.contrib import admin
from django.db import transaction
from .models import Activity, Registration

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["title", "starts_at", "capacity", "is_active"]
    @transaction.atomic
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        # El mismo IMMEDIATE protege lectura de ocupación, validación y guardado.
        return super().changeform_view(request, object_id, form_url, extra_context)

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ["student", "activity", "created_at", "cancelled_at"]
    readonly_fields = ["student", "activity", "created_at", "cancelled_at"]
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError

class ResponsibleUserChangeForm(UserChangeForm):
    def clean_is_staff(self):
        is_staff = self.cleaned_data["is_staff"]
        if not is_staff and self.instance.pk and self.instance.responsible_activities.exists():
            raise ValidationError("Reasigná sus actividades antes de quitar el acceso docente.")
        return is_staff

class ResponsibleUserAdmin(UserAdmin):
    form = ResponsibleUserChangeForm

    @transaction.atomic
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        return super().changeform_view(request, object_id, form_url, extra_context)

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), ResponsibleUserAdmin)
