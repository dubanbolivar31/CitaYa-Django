from django import forms
from .models import Administrador, Paciente

class AdministradorForm(forms.ModelForm):
    class Meta:
        model = Administrador
        fields = '__all__'

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }