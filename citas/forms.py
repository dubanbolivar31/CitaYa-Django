import re
from django import forms
from django.contrib.auth.hashers import make_password
from .models import Administrador, Medico, Paciente, Agendamiento, Historial_Clinico


# ──────────────────────────────────────────────────────────────────────────────
# VALIDADORES REUTILIZABLES
# ──────────────────────────────────────────────────────────────────────────────

def validar_solo_numeros(value, nombre_campo="Este campo"):
    if not value.isdigit():
        raise forms.ValidationError(f"{nombre_campo} solo puede contener números.")

def validar_telefono(value):
    if not value.isdigit():
        raise forms.ValidationError("El teléfono solo puede contener números.")
    if len(value) != 10:
        raise forms.ValidationError("El teléfono debe tener exactamente 10 dígitos.")

def validar_numero_doc(value):
    if not value.isdigit():
        raise forms.ValidationError("El número de documento solo puede contener números.")

def validar_contrasena(value):
    """
    Mínimo 10 caracteres, al menos una mayúscula, una minúscula y un carácter especial.
    Solo se llama cuando el campo tiene contenido.
    """
    if len(value) < 10:
        raise forms.ValidationError("La contraseña debe tener al menos 10 caracteres.")
    if not re.search(r'[A-Z]', value):
        raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r'[a-z]', value):
        raise forms.ValidationError("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r'[^A-Za-z0-9]', value):
        raise forms.ValidationError("La contraseña debe contener al menos un carácter especial (ej: *, @, #, !).")


# ──────────────────────────────────────────────────────────────────────────────
# FORM: ADMINISTRADOR
# ──────────────────────────────────────────────────────────────────────────────

class AdministradorForm(forms.ModelForm):
    contrasena = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label="Contraseña",
    )

    class Meta:
        model = Administrador
        fields = '__all__'

    def clean_numero_doc(self):
        value = self.cleaned_data.get('numero_doc', '').strip()
        validar_numero_doc(value)
        return value

    def clean_telefono(self):
        value = self.cleaned_data.get('telefono', '').strip()
        validar_telefono(value)
        return value

    def clean_contrasena(self):
        value = self.cleaned_data.get('contrasena', '').strip()
        if value:
            validar_contrasena(value)
        return value

    def clean_nombre(self):
        value = self.cleaned_data.get('nombre', '').strip()
        if not value:
            raise forms.ValidationError("El nombre es obligatorio.")
        return value

    def clean_apellido(self):
        value = self.cleaned_data.get('apellido', '').strip()
        if not value:
            raise forms.ValidationError("El apellido es obligatorio.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        pw = self.cleaned_data.get('contrasena', '').strip()
        if pw:
            instance.contrasena = make_password(pw)  # ✅ hashea la nueva contraseña
        elif instance.pk:
            # Sin cambio de contraseña: conserva el hash existente en la BD
            instance.contrasena = Administrador.objects.get(pk=instance.pk).contrasena
        if commit:
            instance.save()
        return instance


# ──────────────────────────────────────────────────────────────────────────────
# FORM: MÉDICO
# ──────────────────────────────────────────────────────────────────────────────

class MedicoForm(forms.ModelForm):
    contrasena = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label="Contraseña",
    )

    class Meta:
        model = Medico
        fields = '__all__'

    def clean_numero_doc(self):
        value = self.cleaned_data.get('numero_doc', '').strip()
        validar_numero_doc(value)
        return value

    def clean_telefono(self):
        value = self.cleaned_data.get('telefono', '').strip()
        validar_telefono(value)
        return value

    def clean_contrasena(self):
        value = self.cleaned_data.get('contrasena', '').strip()
        if value:
            validar_contrasena(value)
        return value

    def clean_nombre(self):
        value = self.cleaned_data.get('nombre', '').strip()
        if not value:
            raise forms.ValidationError("El nombre es obligatorio.")
        return value

    def clean_apellido(self):
        value = self.cleaned_data.get('apellido', '').strip()
        if not value:
            raise forms.ValidationError("El apellido es obligatorio.")
        return value

    def clean_especialidad(self):
        value = self.cleaned_data.get('especialidad', '').strip()
        if not value:
            raise forms.ValidationError("La especialidad es obligatoria.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        pw = self.cleaned_data.get('contrasena', '').strip()
        if pw:
            instance.contrasena = make_password(pw)  # ✅ hashea la nueva contraseña
        elif instance.pk:
            instance.contrasena = Medico.objects.get(pk=instance.pk).contrasena
        if commit:
            instance.save()
        return instance


# ──────────────────────────────────────────────────────────────────────────────
# FORM: PACIENTE
# ──────────────────────────────────────────────────────────────────────────────

class PacienteForm(forms.ModelForm):
    contrasena = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label="Contraseña",
    )

    class Meta:
        model = Paciente
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_numero_doc(self):
        value = self.cleaned_data.get('numero_doc', '').strip()
        validar_numero_doc(value)
        return value

    def clean_telefono(self):
        value = self.cleaned_data.get('telefono', '').strip()
        validar_telefono(value)
        return value

    def clean_contrasena(self):
        value = self.cleaned_data.get('contrasena', '').strip()
        if value:
            validar_contrasena(value)
        return value

    def clean_nombre(self):
        value = self.cleaned_data.get('nombre', '').strip()
        if not value:
            raise forms.ValidationError("El nombre es obligatorio.")
        return value

    def clean_apellido(self):
        value = self.cleaned_data.get('apellido', '').strip()
        if not value:
            raise forms.ValidationError("El apellido es obligatorio.")
        return value

    def clean_direccion(self):
        value = self.cleaned_data.get('direccion', '').strip()
        if not value:
            raise forms.ValidationError("La dirección es obligatoria.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        pw = self.cleaned_data.get('contrasena', '').strip()
        if pw:
            instance.contrasena = make_password(pw)  # ✅ hashea la nueva contraseña
        elif instance.pk:
            instance.contrasena = Paciente.objects.get(pk=instance.pk).contrasena
        if commit:
            instance.save()
        return instance


# ──────────────────────────────────────────────────────────────────────────────
# FORM: AGENDAMIENTO
# ──────────────────────────────────────────────────────────────────────────────

class AgendamientoForm(forms.ModelForm):
    class Meta:
        model = Agendamiento
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora':  forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_cita(self):
        value = self.cleaned_data.get('cita', '').strip()
        if not value:
            raise forms.ValidationError("El tipo de cita es obligatorio.")
        return value


# ──────────────────────────────────────────────────────────────────────────────
# FORM: HISTORIAL CLÍNICO
# ──────────────────────────────────────────────────────────────────────────────

class HistorialForm(forms.ModelForm):
    class Meta:
        model = Historial_Clinico
        fields = '__all__'

    def clean_antecedentes(self):
        value = self.cleaned_data.get('antecedentes', '').strip()
        if not value:
            raise forms.ValidationError("Los antecedentes no pueden estar vacíos.")
        return value