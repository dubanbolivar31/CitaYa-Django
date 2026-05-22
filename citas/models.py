import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class Administrador(models.Model):
    id_admin   = models.AutoField(primary_key=True)
    tipo_doc   = models.CharField(max_length=20)
    numero_doc = models.CharField(max_length=20, unique=True)
    nombre     = models.CharField(max_length=100)
    apellido   = models.CharField(max_length=100)
    genero     = models.CharField(max_length=10)
    telefono   = models.CharField(max_length=15)
    correo     = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)
    estado     = models.BooleanField(default=True)

    def set_contrasena(self, raw_password):
        self.contrasena = make_password(raw_password)

    def check_contrasena(self, raw_password):
        return check_password(raw_password, self.contrasena)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Medico(models.Model):
    id_medico    = models.AutoField(primary_key=True)
    tipo_doc     = models.CharField(max_length=20)
    numero_doc   = models.CharField(max_length=20, unique=True)
    nombre       = models.CharField(max_length=100)
    apellido     = models.CharField(max_length=100)
    genero       = models.CharField(max_length=10)
    especialidad = models.CharField(max_length=100)
    telefono     = models.CharField(max_length=15)
    correo       = models.EmailField(unique=True)
    contrasena   = models.CharField(max_length=255)
    estado       = models.BooleanField(default=True)

    def set_contrasena(self, raw_password):
        self.contrasena = make_password(raw_password)

    def check_contrasena(self, raw_password):
        return check_password(raw_password, self.contrasena)

    def __str__(self):
        return f"Dr. {self.nombre} {self.apellido} - {self.especialidad}"


class Paciente(models.Model):
    id_paciente      = models.AutoField(primary_key=True)
    tipo_doc         = models.CharField(max_length=20)
    numero_doc       = models.CharField(max_length=20, unique=True)
    nombre           = models.CharField(max_length=100)
    apellido         = models.CharField(max_length=100)
    genero           = models.CharField(max_length=10)
    fecha_nacimiento = models.DateField()
    tipo_sangre      = models.CharField(max_length=5)
    direccion        = models.CharField(max_length=200)
    telefono         = models.CharField(max_length=15)
    correo           = models.EmailField(unique=True)
    contrasena       = models.CharField(max_length=255) 
    estado           = models.BooleanField(default=True)

    def set_contrasena(self, raw_password):
        self.contrasena = make_password(raw_password)

    def check_contrasena(self, raw_password):
        return check_password(raw_password, self.contrasena)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    

class Agendamiento(models.Model):
    id_agendamiento = models.AutoField(primary_key=True)
    cita = models.CharField(max_length=100)
    fecha = models.DateField()
    hora = models.TimeField()
    
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    id_medico = models.ForeignKey(Medico, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.cita} - {self.fecha}"
    

class Historial_Clinico(models.Model):
    id_historial = models.AutoField(primary_key=True)
    fecha_creacion = models.DateField(auto_now_add=True)
    antecedentes = models.TextField()

    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    id_medico = models.ForeignKey(Medico, on_delete=models.CASCADE)

    def __str__(self):
        return f"Historial de {self.id_paciente.nombre} - {self.fecha_creacion}"


# *** RECUPERAR CONTRASEÑA ***

class PasswordResetToken(models.Model):
    ROL_CHOICES = [
        ('admin',    'Administrador'),
        ('medico',   'Médico'),
        ('paciente', 'Paciente'),
    ]

    id_token   = models.AutoField(primary_key=True)
    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    rol        = models.CharField(max_length=10, choices=ROL_CHOICES)
    usuario_id = models.IntegerField()
    correo     = models.EmailField()
    creado_en  = models.DateTimeField(auto_now_add=True)
    usado      = models.BooleanField(default=False)

    def esta_vigente(self):
        return not self.usado and (timezone.now() - self.creado_en).total_seconds() < 3600  # ✅ fix bug

    def __str__(self):
        return f"{self.rol} | {self.correo} | {'✓' if self.usado else '⏳'}"