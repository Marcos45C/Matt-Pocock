from django import forms
class RegistrationForm(forms.Form):
    """La identidad se obtiene de la sesión, nunca de un campo del formulario."""
