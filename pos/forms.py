# forms.py
from django import forms
from .models import Usuarios

class RegistroUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellido', 'dni', 'tipo_empleado']
