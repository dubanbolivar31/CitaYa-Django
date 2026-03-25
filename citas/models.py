from django.db import models

class Administrador(models.Model):
    id_admin = models.AutoField(primary_key=True)
    tipo_doc = models.CharField(max_length=20)
    numero_doc = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    genero = models.CharField(max_length=10)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    

class Medico(models.Model):
    id_medico = models.AutoField(primary_key=True)
    tipo_doc = models.CharField(max_length=20)
    numero_doc = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    genero = models.CharField(max_length=10)
    especialidad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.nombre} {self.apellido} - {self.especialidad}"
    
class Paciente(models.Model):
    id_paciente = models.AutoField(primary_key=True)
    tipo_doc = models.CharField(max_length=20)
    numero_doc = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    genero = models.CharField(max_length=10)
    fecha_nacimiento = models.DateField()
    tipo_sangre = models.CharField(max_length=5)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    

class Agendamiento(models.Model):
    id_agendamiento = models.AutoField(primary_key=True)
    cita = models.CharField(max_length=100) # Ej: "Consulta General"
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