import re
from datetime import date
from dateutil.relativedelta import relativedelta

from django import forms
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from .models import Administrador, Medico, Paciente, Agendamiento, Historial_Clinico


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES — valores permitidos (única fuente de verdad)
# ══════════════════════════════════════════════════════════════════════════════

TIPOS_DOC = {
    'CC':  {'solo_digitos': True,  'min': 6,  'max': 10, 'exacto': None},
    'TI':  {'solo_digitos': True,  'min': 10, 'max': 10, 'exacto': 10},
    'CE':  {'solo_digitos': True,  'min': 6,  'max': 12, 'exacto': None},
    'PP':  {'solo_digitos': False, 'min': 5,  'max': 15, 'exacto': None},
}

GENEROS_VALIDOS   = {'M', 'F', 'OTRO'}
SANGRES_VALIDAS   = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'}
PATRON_NOMBRE     = re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ]+(\s[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ]+)*$')
PATRON_ALFANUM    = re.compile(r'^[a-zA-Z0-9]+$')
RE_CONTROL        = re.compile(r'[\x00-\x1F\x7F-\x9F\u200B-\u200D\uFEFF]')


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _limpiar(valor):
    """Elimina caracteres de control Unicode y espacios extremos."""
    return RE_CONTROL.sub('', (valor or '')).strip()


# ══════════════════════════════════════════════════════════════════════════════
# VALIDADORES REUTILIZABLES
# ══════════════════════════════════════════════════════════════════════════════

def validar_nombre_texto(value, etiqueta='Este campo'):
    """Solo letras latinas/españolas y espacios simples entre palabras, mín. 2 letras."""
    v = _limpiar(value)
    if not v:
        raise ValidationError(f'{etiqueta} es obligatorio.')
    if not PATRON_NOMBRE.match(v):
        raise ValidationError(f'{etiqueta} solo puede contener letras y espacios simples.')
    if len(v.replace(' ', '')) < 2:
        raise ValidationError(f'{etiqueta} debe tener al menos 2 letras.')
    return v


def validar_numero_doc(value, tipo_doc):
    """
    Valida el número de documento según el tipo:
      CC  → 6-10 dígitos
      TI  → exactamente 10 dígitos
      CE  → 6-12 dígitos
      PP  → 5-15 caracteres alfanuméricos
    """
    v   = _limpiar(value)
    cfg = TIPOS_DOC.get(tipo_doc)

    if not v:
        raise ValidationError('El número de documento es obligatorio.')
    if not cfg:
        raise ValidationError('Tipo de documento no reconocido.')

    if cfg['solo_digitos']:
        if not v.isdigit():
            raise ValidationError('El número de documento solo puede contener dígitos numéricos.')
        if cfg['exacto'] and len(v) != cfg['exacto']:
            raise ValidationError(
                f'La {_nombre_tipo(tipo_doc)} debe tener exactamente {cfg["exacto"]} dígitos.'
            )
        elif not cfg['exacto'] and not (cfg['min'] <= len(v) <= cfg['max']):
            raise ValidationError(
                f'La {_nombre_tipo(tipo_doc)} debe tener entre {cfg["min"]} y {cfg["max"]} dígitos.'
            )
    else:
        if not PATRON_ALFANUM.match(v):
            raise ValidationError('El pasaporte solo puede contener letras y números, sin espacios ni símbolos.')
        if not (cfg['min'] <= len(v) <= cfg['max']):
            raise ValidationError(
                f'El pasaporte debe tener entre {cfg["min"]} y {cfg["max"]} caracteres.'
            )
    return v


def _nombre_tipo(tipo_doc):
    nombres = {'CC': 'Cédula de Ciudadanía', 'TI': 'Tarjeta de Identidad',
               'CE': 'Cédula de Extranjería', 'PP': 'Pasaporte'}
    return nombres.get(tipo_doc, 'documento')


def validar_telefono(value):
    """10 dígitos, debe empezar en 3 (celular colombiano)."""
    v = _limpiar(value).replace(' ', '')
    if not v:
        raise ValidationError('El teléfono es obligatorio.')
    if not v.isdigit():
        raise ValidationError('El teléfono solo puede contener dígitos numéricos.')
    if len(v) != 10:
        raise ValidationError('El teléfono debe tener exactamente 10 dígitos.')
    if v[0] != '3':
        raise ValidationError('El teléfono debe ser un celular colombiano (empieza con 3).')
    return v


def validar_contrasena(value):
    """
    Mínimo 8 caracteres, máximo 128.
    Al menos: 1 mayúscula, 1 minúscula, 1 dígito, 1 carácter especial.
    """
    errores = []
    if len(value) < 8:
        errores.append('mínimo 8 caracteres')
    if len(value) > 128:
        errores.append('máximo 128 caracteres')
    if not re.search(r'[A-Z]', value):
        errores.append('al menos 1 mayúscula')
    if not re.search(r'[a-z]', value):
        errores.append('al menos 1 minúscula')
    if not re.search(r'[0-9]', value):
        errores.append('al menos 1 número')
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>/?`~\\|]', value):
        errores.append('al menos 1 carácter especial (!@#$%^&*...)')
    if errores:
        raise ValidationError(f'La contraseña necesita: {", ".join(errores)}.')


def validar_direccion(value):
    v = _limpiar(value)
    if not v:
        raise ValidationError('La dirección es obligatoria.')
    if len(v) < 5:
        raise ValidationError('La dirección debe tener al menos 5 caracteres.')
    if re.search(r'<[^>]*>|javascript:', v, re.IGNORECASE):
        raise ValidationError('La dirección contiene caracteres no permitidos.')
    return v


def validar_fecha_nacimiento(value):
    """Entre 1 mes y 90 años atrás."""
    if not value:
        raise ValidationError('La fecha de nacimiento es obligatoria.')
    hoy    = date.today()
    min_f  = hoy - relativedelta(months=1)
    max_f  = hoy - relativedelta(years=90)
    if value > min_f:
        raise ValidationError('El paciente debe tener al menos 1 mes de nacido.')
    if value < max_f:
        raise ValidationError('La fecha excede el rango máximo de 90 años.')
    return value


# ══════════════════════════════════════════════════════════════════════════════
# MIXIN — unicidad de correo, teléfono y número de documento al crear y editar
# ══════════════════════════════════════════════════════════════════════════════

class UniqueFieldsMixin:
    """
    Verifica unicidad de correo, teléfono y número de documento
    excluyendo la instancia actual en caso de edición.
    Se debe definir `unique_model` en la subclase.
    """
    unique_model = None   # debe apuntarse al modelo correcto en cada Form

    def _check_unique(self, campo, valor, mensaje):
        qs = self.unique_model.objects.filter(**{campo: valor})
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(mensaje)
        return valor

    def clean_correo(self):
        valor = _limpiar(self.cleaned_data.get('correo', '')).lower()
        if not valor:
            raise ValidationError('El correo es obligatorio.')
        return self._check_unique(
            'correo__iexact', valor,
            'Ese correo electrónico ya está registrado por otro usuario.'
        )

    def clean_telefono(self):
        valor = validar_telefono(self.cleaned_data.get('telefono', ''))
        return self._check_unique(
            'telefono', valor,
            'Ese número de teléfono ya está registrado por otro usuario.'
        )


# ══════════════════════════════════════════════════════════════════════════════
# FORM: ADMINISTRADOR
# ══════════════════════════════════════════════════════════════════════════════

class AdministradorForm(UniqueFieldsMixin, forms.ModelForm):
    unique_model = Administrador

    contrasena = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label='Contraseña',
        help_text='Mín. 8 caracteres, mayúscula, minúscula, número y símbolo. Déjalo en blanco para no cambiarla.',
    )

    class Meta:
        model  = Administrador
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_tipo_doc(self):
        v = _limpiar(self.cleaned_data.get('tipo_doc', ''))
        if v not in TIPOS_DOC:
            raise ValidationError('Tipo de documento no válido.')
        return v

    def clean_numero_doc(self):
        tipo = _limpiar(self.data.get('tipo_doc', ''))  # leer directamente del POST
        v    = _limpiar(self.cleaned_data.get('numero_doc', ''))
        v    = validar_numero_doc(v, tipo)
        # Unicidad
        qs = Administrador.objects.filter(numero_doc=v)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ese número de documento ya está registrado.')
        return v

    def clean_nombre(self):
        return validar_nombre_texto(self.cleaned_data.get('nombre', ''), 'El nombre')

    def clean_apellido(self):
        return validar_nombre_texto(self.cleaned_data.get('apellido', ''), 'El apellido')

    def clean_genero(self):
        v = _limpiar(self.cleaned_data.get('genero', ''))
        if v not in GENEROS_VALIDOS:
            raise ValidationError('Selecciona un género válido.')
        return v

    def clean_contrasena(self):
        value = self.cleaned_data.get('contrasena', '').strip()
        if value:
            validar_contrasena(value)
        elif not self.instance.pk:
            # Creación: contraseña obligatoria
            raise ValidationError('La contraseña es obligatoria al crear un administrador.')
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        pw = self.cleaned_data.get('contrasena', '').strip()
        if pw:
            instance.contrasena = make_password(pw)
        elif instance.pk:
            instance.contrasena = Administrador.objects.get(pk=instance.pk).contrasena
        if commit:
            instance.save()
        return instance


# ══════════════════════════════════════════════════════════════════════════════
# FORM: MÉDICO
# ══════════════════════════════════════════════════════════════════════════════

class MedicoForm(UniqueFieldsMixin, forms.ModelForm):
    unique_model = Medico

    contrasena = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label='Contraseña',
        help_text='Mín. 8 caracteres, mayúscula, minúscula, número y símbolo. Déjalo en blanco para no cambiarla.',
    )

    class Meta:
        model  = Medico
        fields = '__all__'

    def clean_tipo_doc(self):
        v = _limpiar(self.cleaned_data.get('tipo_doc', ''))
        if v not in TIPOS_DOC:
            raise ValidationError('Tipo de documento no válido.')
        return v

    def clean_numero_doc(self):
        tipo = _limpiar(self.data.get('tipo_doc', ''))
        v    = _limpiar(self.cleaned_data.get('numero_doc', ''))
        v    = validar_numero_doc(v, tipo)
        qs   = Medico.objects.filter(numero_doc=v)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ese número de documento ya está registrado.')
        return v

    def clean_nombre(self):
        return validar_nombre_texto(self.cleaned_data.get('nombre', ''), 'El nombre')

    def clean_apellido(self):
        return validar_nombre_texto(self.cleaned_data.get('apellido', ''), 'El apellido')

    def clean_genero(self):
        v = _limpiar(self.cleaned_data.get('genero', ''))
        if v not in GENEROS_VALIDOS:
            raise ValidationError('Selecciona un género válido.')
        return v

    def clean_especialidad(self):
        v = _limpiar(self.cleaned_data.get('especialidad', ''))
        if not v:
            raise ValidationError('La especialidad es obligatoria.')
        if len(v) < 3:
            raise ValidationError('La especialidad debe tener al menos 3 caracteres.')
        if re.search(r'[<>{}[\]|]', v):
            raise ValidationError('La especialidad contiene caracteres no permitidos.')
        return v

    def clean_contrasena(self):
        value = self.cleaned_data.get('contrasena', '').strip()
        if value:
            validar_contrasena(value)
        elif not self.instance.pk:
            raise ValidationError('La contraseña es obligatoria al crear un médico.')
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        pw = self.cleaned_data.get('contrasena', '').strip()
        if pw:
            instance.contrasena = make_password(pw)
        elif instance.pk:
            instance.contrasena = Medico.objects.get(pk=instance.pk).contrasena
        if commit:
            instance.save()
        return instance


# ══════════════════════════════════════════════════════════════════════════════
# FORM: PACIENTE
# ══════════════════════════════════════════════════════════════════════════════

class PacienteForm(UniqueFieldsMixin, forms.ModelForm):
    unique_model = Paciente

    contrasena = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label='Contraseña',
        help_text='Mín. 8 caracteres, mayúscula, minúscula, número y símbolo. Déjalo en blanco para no cambiarla.',
    )

    class Meta:
        model  = Paciente
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_tipo_doc(self):
        v = _limpiar(self.cleaned_data.get('tipo_doc', ''))
        if v not in TIPOS_DOC:
            raise ValidationError('Tipo de documento no válido.')
        return v

    def clean_numero_doc(self):
        tipo = _limpiar(self.data.get('tipo_doc', ''))
        v    = _limpiar(self.cleaned_data.get('numero_doc', ''))
        v    = validar_numero_doc(v, tipo)
        qs   = Paciente.objects.filter(numero_doc=v)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ese número de documento ya está registrado.')
        return v

    def clean_nombre(self):
        return validar_nombre_texto(self.cleaned_data.get('nombre', ''), 'El nombre')

    def clean_apellido(self):
        return validar_nombre_texto(self.cleaned_data.get('apellido', ''), 'El apellido')

    def clean_genero(self):
        v = _limpiar(self.cleaned_data.get('genero', ''))
        if v not in GENEROS_VALIDOS:
            raise ValidationError('Selecciona un género válido.')
        return v

    def clean_fecha_nacimiento(self):
        return validar_fecha_nacimiento(self.cleaned_data.get('fecha_nacimiento'))

    def clean_tipo_sangre(self):
        v = _limpiar(self.cleaned_data.get('tipo_sangre', ''))
        if v not in SANGRES_VALIDAS:
            raise ValidationError('Selecciona un tipo de sangre válido.')
        return v

    def clean_direccion(self):
        return validar_direccion(self.cleaned_data.get('direccion', ''))

    def clean_contrasena(self):
        value = self.cleaned_data.get('contrasena', '').strip()
        if value:
            validar_contrasena(value)
        elif not self.instance.pk:
            raise ValidationError('La contraseña es obligatoria al crear un paciente.')
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        pw = self.cleaned_data.get('contrasena', '').strip()
        if pw:
            instance.contrasena = make_password(pw)
        elif instance.pk:
            instance.contrasena = Paciente.objects.get(pk=instance.pk).contrasena
        if commit:
            instance.save()
        return instance


# ══════════════════════════════════════════════════════════════════════════════
# FORM: AGENDAMIENTO
# ══════════════════════════════════════════════════════════════════════════════

class AgendamientoForm(forms.ModelForm):

    TIPOS_CITA = [
        ('', '— Seleccionar tipo —'),
        ('Medicina General',      'Medicina General'),
        ('Ortopedia',             'Ortopedia'),
        ('Psicología',            'Psicología'),
        ('Cardiología',           'Cardiología'),
        ('Pediatría',             'Pediatría'),
        ('Dermatología',          'Dermatología'),
    ]

    # Sobreescribimos el widget de cita para usar el select con las especialidades
    cita = forms.ChoiceField(
        choices=TIPOS_CITA,
        label='Tipo de Cita / Especialidad',
    )

    class Meta:
        model  = Agendamiento
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora':  forms.TimeInput(attrs={'type': 'time', 'step': '1800'}),  # step 30 min
        }

    # ── Tipo de cita ──────────────────────────────────────────────────────────
    def clean_cita(self):
        v = _limpiar(self.cleaned_data.get('cita', ''))
        if not v:
            raise ValidationError('El tipo de cita es obligatorio.')
        return v

    # ── Fecha ─────────────────────────────────────────────────────────────────
    def clean_fecha(self):
        from datetime import date
        fecha = self.cleaned_data.get('fecha')
        if not fecha:
            raise ValidationError('La fecha es obligatoria.')
        if fecha < date.today():
            raise ValidationError('No puedes agendar una cita en el pasado.')
        return fecha

    # ── Hora ──────────────────────────────────────────────────────────────────
    def clean_hora(self):
        from datetime import datetime, date, time as dtime, timedelta
        hora = self.cleaned_data.get('hora')
        if not hora:
            raise ValidationError('La hora es obligatoria.')

        # Debe ser en intervalo de 30 minutos exactos (00 o 30)
        if hora.minute not in (0, 30) or hora.second != 0:
            raise ValidationError('La hora debe ser en intervalos de 30 minutos (ej: 08:00, 08:30, 09:00…).')

        # Rango horario permitido: 06:00 – 18:00
        if hora < dtime(6, 0) or hora >= dtime(18, 0):
            raise ValidationError('El horario de atención es de 06:00 a 18:00.')

        return hora

    # ── Paciente ──────────────────────────────────────────────────────────────
    def clean_id_paciente(self):
        v = self.cleaned_data.get('id_paciente')
        if not v:
            raise ValidationError('El paciente es obligatorio.')
        return v

    # ── Médico ────────────────────────────────────────────────────────────────
    def clean_id_medico(self):
        v = self.cleaned_data.get('id_medico')
        if not v:
            raise ValidationError('El médico es obligatorio.')
        return v

    # ── Validaciones cruzadas (fecha + hora + médico + paciente) ──────────────
    def clean(self):
        from datetime import datetime, date, timedelta

        cleaned = super().clean()
        fecha      = cleaned.get('fecha')
        hora       = cleaned.get('hora')
        medico     = cleaned.get('id_medico')
        paciente   = cleaned.get('id_paciente')

        # Si algún campo individual falló, no seguir (evita AttributeError)
        if not all([fecha, hora, medico, paciente]):
            return cleaned

        ahora = datetime.now()

        # ── Mínimo 2 horas de anticipación si la cita es hoy ─────────────────
        if fecha == date.today():
            momento_cita  = datetime.combine(fecha, hora)
            minimo_desde  = ahora + timedelta(hours=2)
            if momento_cita < minimo_desde:
                raise ValidationError(
                    'Las citas deben agendarse con al menos 2 horas de anticipación. '
                    f'El primer horario disponible hoy es a partir de las '
                    f'{minimo_desde.strftime("%H:%M")}.'
                )

        # ── El médico no puede tener otra cita a la misma fecha/hora ─────────
        qs_medico = Agendamiento.objects.filter(id_medico=medico, fecha=fecha, hora=hora)
        if self.instance and self.instance.pk:
            qs_medico = qs_medico.exclude(pk=self.instance.pk)
        if qs_medico.exists():
            raise ValidationError(
                f'El médico ya tiene una cita agendada el {fecha.strftime("%d/%m/%Y")} '
                f'a las {hora.strftime("%H:%M")}. Selecciona otro horario.'
            )

        # ── El paciente no puede tener otra cita a la misma fecha/hora ───────
        qs_paciente = Agendamiento.objects.filter(id_paciente=paciente, fecha=fecha, hora=hora)
        if self.instance and self.instance.pk:
            qs_paciente = qs_paciente.exclude(pk=self.instance.pk)
        if qs_paciente.exists():
            raise ValidationError(
                f'El paciente ya tiene una cita agendada el {fecha.strftime("%d/%m/%Y")} '
                f'a las {hora.strftime("%H:%M")}. Selecciona otro horario.'
            )

        return cleaned


# ══════════════════════════════════════════════════════════════════════════════
# FORM: HISTORIAL CLÍNICO
# ══════════════════════════════════════════════════════════════════════════════

class HistorialForm(forms.ModelForm):
    class Meta:
        model  = Historial_Clinico
        fields = '__all__'

    def clean_antecedentes(self):
        v = _limpiar(self.cleaned_data.get('antecedentes', ''))
        if not v:
            raise ValidationError('Los antecedentes no pueden estar vacíos.')
        if len(v) < 10:
            raise ValidationError('Los antecedentes deben tener al menos 10 caracteres.')
        if re.search(r'<script|javascript:', v, re.IGNORECASE):
            raise ValidationError('Los antecedentes contienen contenido no permitido.')
        return v

    def clean_id_paciente(self):
        v = self.cleaned_data.get('id_paciente')
        if not v:
            raise ValidationError('El paciente es obligatorio.')
        return v

    def clean_id_medico(self):
        v = self.cleaned_data.get('id_medico')
        if not v:
            raise ValidationError('El médico es obligatorio.')
        return v