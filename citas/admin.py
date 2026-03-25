from django.contrib import admin
from .models import Administrador, Medico, Paciente, Agendamiento, Historial_Clinico

admin.site.register(Administrador)
admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(Agendamiento)
admin.site.register(Historial_Clinico)