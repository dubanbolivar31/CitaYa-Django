from django.urls import path
from . import views
from .views import (
    AdminListView, AdminCreateView, AdminUpdateView, AdminDeleteView,
    MedicoListView, MedicoCreateView, MedicoUpdateView, MedicoDeleteView,
    PacienteListView, PacienteCreateView, PacienteUpdateView, PacienteDeleteView,
    AgendamientoListView, AgendamientoCreateView, AgendamientoUpdateView, AgendamientoDeleteView,
    HistorialListView, HistorialCreateView, HistorialUpdateView, HistorialDeleteView,
)

urlpatterns = [

    # =========================================================================
    #  RUTAS GENERALES Y AUTENTICACIÓN
    # =========================================================================
    path('',         views.index,        name='index'),
    path('login/',   views.login,        name='login'),
    path('registro/',views.registro,     name='registro'),
    path('logout/',  views.logout_admin, name='logout_admin'),

    # =========================================================================
    #  DASHBOARDS PRINCIPALES
    # =========================================================================
    path('dashboard/admin/',    views.dashboard_admin,    name='dashboard_admin'),
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/medico/',   views.dashboard_medico,   name='dashboard_medico'),

    # =========================================================================
    #  API MÉDICO
    # =========================================================================
    path('api/medico/agenda/',             views.agenda_medico_json,             name='agenda_medico_json'),
    path('api/medico/paciente/<int:pk>/',  views.paciente_medico_json,           name='paciente_medico_json'),
    path('api/medico/historial/<int:pk>/', views.historial_paciente_medico_json, name='historial_paciente_medico_json'),
    path('api/medico/historial/guardar/',  views.guardar_historial_medico,       name='guardar_historial_medico'),

    # ── PERFIL MÉDICO ──────────────────────────────────────────────────
    path('perfil/medico/json/',   views.perfil_medico_json,   name='perfil_medico_json'),
    path('perfil/medico/editar/', views.editar_perfil_medico, name='editar_perfil_medico'),

    # =========================================================================
    #  GESTIÓN DE PERFILES (APIs para Modales)
    # =========================================================================
    path('perfil/admin/json/',      views.perfil_admin_json,      name='perfil_admin_json'),
    path('perfil/admin/editar/',    views.editar_perfil_admin,    name='editar_perfil_admin'),
    path('perfil/paciente/json/',   views.perfil_paciente_json,   name='perfil_paciente_json'),
    path('perfil/paciente/editar/', views.editar_perfil_paciente, name='editar_perfil_paciente'),

    # =========================================================================
    #  API DE PACIENTE (SISTEMA DE CITAS)
    # =========================================================================
    path('api/paciente/citas/',                        views.citas_paciente_json,           name='citas_paciente_json'),
    path('api/paciente/historial/',                    views.historial_paciente_json,        name='historial_paciente_json'),
    path('api/medicos-por-especialidad/',              views.obtener_medicos_por_especialidad,name='medicos_por_especialidad'),
    path('api/disponibilidad-medico/',                 views.obtener_disponibilidad_medico,  name='disponibilidad_medico'),
    path('api/paciente/citas/agendar/',                views.agendar_cita_paciente,          name='agendar_cita_paciente'),
    path('api/paciente/citas/reprogramar/<int:pk>/',   views.reprogramar_cita_paciente,      name='reprogramar_cita_paciente'),
    path('api/paciente/citas/cancelar/<int:pk>/',      views.cancelar_cita_paciente,         name='cancelar_cita_paciente'),

    # =========================================================================
    #  MÓDULOS ADMINISTRATIVOS — ADMINISTRADORES
    # =========================================================================
    path('administradores/',                         AdminListView.as_view(),   name='ver_administrador'),
    path('administradores/crear/',                   AdminCreateView.as_view(), name='crear_administrador'),
    path('administradores/editar/<int:pk>/',         AdminUpdateView.as_view(), name='editar_administrador'),
    path('administradores/eliminar/<int:pk>/',       AdminDeleteView.as_view(), name='eliminar_administrador'),
    # 📊 Reporte — ?tipo=pdf|excel  &  ?q=termino
    path('administradores/reporte/',                 views.reporte_administradores, name='reporte_administradores'),

    # =========================================================================
    #  MÓDULOS ADMINISTRATIVOS — MÉDICOS
    # =========================================================================
    path('medicos/',                   MedicoListView.as_view(),   name='ver_medicos'),
    path('medicos/crear/',             MedicoCreateView.as_view(), name='crear_medicos'),
    path('medicos/editar/<int:pk>/',   MedicoUpdateView.as_view(), name='editar_medicos'),
    path('medicos/eliminar/<int:pk>/', MedicoDeleteView.as_view(), name='eliminar_medicos'),
    # 📊 Reporte
    path('medicos/reporte/',           views.reporte_medicos,      name='reporte_medicos'),

    # =========================================================================
    #  MÓDULOS ADMINISTRATIVOS — PACIENTES
    # =========================================================================
    path('pacientes/',                   PacienteListView.as_view(),   name='ver_pacientes'),
    path('pacientes/crear/',             PacienteCreateView.as_view(), name='crear_pacientes'),
    path('pacientes/editar/<int:pk>/',   PacienteUpdateView.as_view(), name='editar_pacientes'),
    path('pacientes/eliminar/<int:pk>/', PacienteDeleteView.as_view(), name='eliminar_pacientes'),
    # 📊 Reporte
    path('pacientes/reporte/',           views.reporte_pacientes,      name='reporte_pacientes'),

    # =========================================================================
    #  MÓDULOS ADMINISTRATIVOS — AGENDAMIENTOS
    # =========================================================================
    path('agendamientos/',                   AgendamientoListView.as_view(),   name='ver_agendamientos'),
    path('agendamientos/crear/',             AgendamientoCreateView.as_view(), name='crear_agendamientos'),
    path('agendamientos/editar/<int:pk>/',   AgendamientoUpdateView.as_view(), name='editar_agendamientos'),
    path('agendamientos/eliminar/<int:pk>/', AgendamientoDeleteView.as_view(), name='eliminar_agendamientos'),
    # 📊 Reporte
    path('agendamientos/reporte/',           views.reporte_agendamientos,      name='reporte_agendamientos'),

    # =========================================================================
    #  MÓDULOS ADMINISTRATIVOS — HISTORIAL CLÍNICO
    # =========================================================================
    path('historiales/',                   HistorialListView.as_view(),   name='ver_historiales'),
    path('historiales/crear/',             HistorialCreateView.as_view(), name='crear_historiales'),
    path('historiales/editar/<int:pk>/',   HistorialUpdateView.as_view(), name='editar_historiales'),
    path('historiales/eliminar/<int:pk>/', HistorialDeleteView.as_view(), name='eliminar_historiales'),
    # 📊 Reporte
    path('historiales/reporte/',           views.reporte_historiales,     name='reporte_historiales'),
]