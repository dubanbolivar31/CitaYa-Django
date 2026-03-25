from django.urls import path
from . import views
from .views import AdminListView, AdminCreateView, AdminUpdateView, AdminDeleteView, MedicoListView, MedicoCreateView, MedicoUpdateView, MedicoDeleteView, PacienteListView, PacienteCreateView, PacienteUpdateView, PacienteDeleteView, AgendamientoListView, AgendamientoCreateView, AgendamientoUpdateView, AgendamientoDeleteView, HistorialListView, HistorialCreateView, HistorialUpdateView, HistorialDeleteView


urlpatterns = [
    # =========================================================================
    #  RUTAS GENERALES Y AUTENTICACIÓN
    # =========================================================================
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_admin, name='logout_admin'),

    # =========================================================================
    #  DASHBOARDS PRINCIPALES
    # =========================================================================
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),

    # =========================================================================
    #  GESTIÓN DE PERFILES (APIs para Modales)
    # =========================================================================
    # Admin
    path('perfil/admin/json/', views.perfil_admin_json, name='perfil_admin_json'),
    path('perfil/admin/editar/', views.editar_perfil_admin, name='editar_perfil_admin'),
    
    # Paciente
    path('perfil/paciente/json/', views.perfil_paciente_json, name='perfil_paciente_json'),
    path('perfil/paciente/editar/', views.editar_perfil_paciente, name='editar_perfil_paciente'),

    # =========================================================================
    #  API DE PACIENTE (CITAS E HISTORIAL)
    # =========================================================================
    path('api/paciente/citas/', views.citas_paciente_json, name='citas_paciente_json'),
    path('api/paciente/citas/agendar/', views.agendar_cita_paciente, name='agendar_cita_paciente'),
    path('api/paciente/citas/reprogramar/<int:pk>/', views.reprogramar_cita_paciente, name='reprogramar_cita_paciente'),
    path('api/paciente/citas/cancelar/<int:pk>/', views.cancelar_cita_paciente, name='cancelar_cita_paciente'),
    path('api/paciente/historial/', views.historial_paciente_json, name='historial_paciente_json'),
    path('api/medicos-por-especialidad/', views.obtener_medicos_por_especialidad, name='medicos_por_especialidad'),
    path('api/disponibilidad-medico/', views.obtener_disponibilidad_medico, name='disponibilidad_medico'),

    # =========================================================================
    #  MÓDULOS ADMINISTRATIVOS (CRUDS)
    # =========================================================================
    
    # Administradores
    path('administradores/', AdminListView.as_view(), name='ver_administrador'),
    path('administradores/crear/', AdminCreateView.as_view(), name='crear_administrador'),
    path('administradores/editar/<int:pk>/', AdminUpdateView.as_view(), name='editar_administrador'),
    path('administradores/eliminar/<int:pk>/', AdminDeleteView.as_view(), name='eliminar_administrador'),

    # Médicos
    path('medicos/', MedicoListView.as_view(), name='ver_medicos'),
    path('medicos/crear/', MedicoCreateView.as_view(), name='crear_medicos'),
    path('medicos/editar/<int:pk>/', MedicoUpdateView.as_view(), name='editar_medicos'),
    path('medicos/eliminar/<int:pk>/', MedicoDeleteView.as_view(), name='eliminar_medicos'),

    # Pacientes
    path('pacientes/', PacienteListView.as_view(), name='ver_pacientes'),
    path('pacientes/crear/', PacienteCreateView.as_view(), name='crear_pacientes'),
    path('pacientes/editar/<int:pk>/', PacienteUpdateView.as_view(), name='editar_pacientes'),
    path('pacientes/eliminar/<int:pk>/', PacienteDeleteView.as_view(), name='eliminar_pacientes'),

    # Agendamientos
    path('agendamientos/', AgendamientoListView.as_view(), name='ver_agendamientos'),
    path('agendamientos/crear/', AgendamientoCreateView.as_view(), name='crear_agendamientos'),
    path('agendamientos/editar/<int:pk>/', AgendamientoUpdateView.as_view(), name='editar_agendamientos'),
    path('agendamientos/eliminar/<int:pk>/', AgendamientoDeleteView.as_view(), name='eliminar_agendamientos'),

    # Historial Clínico
    path('historiales/', HistorialListView.as_view(), name='ver_historiales'),
    path('historiales/crear/', HistorialCreateView.as_view(), name='crear_historiales'),
    path('historiales/editar/<int:pk>/', HistorialUpdateView.as_view(), name='editar_historiales'),
    path('historiales/eliminar/<int:pk>/', HistorialDeleteView.as_view(), name='eliminar_historiales'),
]