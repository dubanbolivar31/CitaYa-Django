import json
from datetime import date
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.contrib.auth.mixins import AccessMixin
from datetime import datetime, timedelta

from .models import Administrador, Agendamiento, Historial_Clinico, Medico, Paciente

# =========================================================================
# MIXINS DE SEGURIDAD (PROTECCIÓN DE RUTAS)
# =========================================================================

class AdminRequiredMixin(AccessMixin):
    """Verifica que el usuario sea Admin. Si no, lo manda al login."""
    def dispatch(self, request, *args, **kwargs):
        if request.session.get('rol') != 'admin':
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

# =========================================================================
# VISTAS GENERALES Y AUTENTICACIÓN
# =========================================================================

def index(request):
    return render(request, 'index.html')


def logout_admin(request):
    request.session.flush()  # Borra TODA la sesión
    return redirect('login')

def login(request):
    if request.method == 'POST':
        numero_doc = request.POST.get('numerodoc')
        password = request.POST.get('contrasena')

        # 1. Buscar en Administradores
        user_admin = Administrador.objects.filter(numero_doc=numero_doc, contrasena=password).first()
        if user_admin:
            request.session['usuario_id'] = user_admin.id_admin
            request.session['rol'] = 'admin'
            request.session['nombre'] = f"{user_admin.nombre} {user_admin.apellido}"
            return redirect('dashboard_admin')

        # 2. Buscar en Médicos
        user_medico = Medico.objects.filter(numero_doc=numero_doc, contrasena=password).first()
        if user_medico:
            request.session['usuario_id'] = user_medico.id_medico
            request.session['rol'] = 'medico'
            request.session['nombre'] = f"{user_medico.nombre} {user_medico.apellido}"
            return redirect('dashboard_medico')

        # 3. Buscar en Pacientes
        user_paciente = Paciente.objects.filter(numero_doc=numero_doc, contrasena=password).first()
        if user_paciente:
            request.session['usuario_id'] = user_paciente.id_paciente
            request.session['rol'] = 'paciente'
            request.session['nombre'] = f"{user_paciente.nombre} {user_paciente.apellido}"
            return redirect('dashboard_paciente')
        
          # <-- Redirigir al nuevo dashboard

        messages.error(request, 'Documento o contraseña incorrectos.')
    
    return render(request, 'Inicio_Sesion-Registro/login.html')

def registro(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            tipo_doc = request.POST.get('tipo_doc')
            numero_doc = request.POST.get('numero_doc')
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            genero = request.POST.get('genero')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            tipo_sangre = request.POST.get('tipo_sangre')
            telefono = request.POST.get('telefono')
            correo = request.POST.get('correo')
            direccion = request.POST.get('direccion')
            contrasena = request.POST.get('contrasena')

            # Validar si ya existe
            if Paciente.objects.filter(numero_doc=numero_doc).exists():
                messages.error(request, 'Ya existe un usuario con ese documento.')
                return redirect('registro')

            # Crear paciente
            Paciente.objects.create(
                tipo_doc=tipo_doc,
                numero_doc=numero_doc,
                nombre=nombre,
                apellido=apellido,
                genero=genero,
                fecha_nacimiento=fecha_nacimiento,
                tipo_sangre=tipo_sangre,
                telefono=telefono,
                correo=correo,
                direccion=direccion,
                contrasena=contrasena,
                estado=True
            )

            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('registro')

    return render(request, 'Inicio_Sesion-Registro/registrar.html')

# =========================================================================
# DASHBOARDS (VISTAS PRINCIPALES)
# =========================================================================

@never_cache
def dashboard_admin(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    
    context = {
        'total_medicos': Medico.objects.count(),
        'total_pacientes': Paciente.objects.count(),
        'total_citas': Agendamiento.objects.count(),
        'total_historiales': Historial_Clinico.objects.count(),
        'nombre': request.session.get('nombre')
    }
    return render(request, 'dashboard/administrador/inicio_admin.html', context)

# ── DASHBOARD MEDICO ───────────────────────────
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from datetime import date

@never_cache
def dashboard_medico(request):
    if request.session.get('rol') != 'medico':
        return redirect('login')

    medico_id = request.session.get('usuario_id')
    hoy = date.today()

    # 📅 Todas las citas del médico
    todas_citas = Agendamiento.objects.filter(
        id_medico=medico_id
    ).select_related('id_paciente')

    # ⏳ Próximas citas
    proximas_citas = todas_citas.filter(
        fecha__gte=hoy
    ).order_by('fecha', 'hora')[:5]

    # 📋 Historial clínico (de pacientes del médico)
    historiales = Historial_Clinico.objects.filter(
        id_medico=medico_id
    ).select_related('id_paciente').order_by('-fecha_creacion')[:5]

    # 👥 Pacientes únicos
    pacientes_ids = todas_citas.values_list('id_paciente', flat=True).distinct()

    # 👤 Lista de pacientes
    pacientes = Paciente.objects.filter(
        id_paciente__in=pacientes_ids
    )

    context = {
        'nombre': request.session.get('nombre'),

        # 📊 métricas
        'total_citas': todas_citas.count(),
        'citas_proximas': proximas_citas.count(),
        'total_historiales': Historial_Clinico.objects.filter(id_medico=medico_id).count(),
        'total_pacientes': len(set(pacientes_ids)),

        # 📋 datos
        'proximas_citas': proximas_citas,
        'historiales': historiales,
        'pacientes': pacientes,
    }

    return render(request, 'dashboard/medico/inicio_medico.html', context)
# ── DASHBOARD PACIENTE ───────────────────────────
@never_cache
def dashboard_paciente(request):
    if request.session.get('rol') != 'paciente':
        return redirect('login')
 
    paciente_id = request.session.get('usuario_id')
    hoy = date.today()
 
    todas_citas   = Agendamiento.objects.filter(id_paciente=paciente_id).select_related('id_medico')
    proximas_citas = todas_citas.filter(fecha__gte=hoy).order_by('fecha', 'hora')[:5]
    historiales   = Historial_Clinico.objects.filter(
        id_paciente=paciente_id
    ).select_related('id_medico').order_by('-fecha_creacion')[:5]
    medicos_ids   = todas_citas.values_list('id_medico', flat=True).distinct()
    medicos_disponibles = Medico.objects.filter(estado=True).order_by('especialidad', 'nombre')
 
    context = {
        'nombre':              request.session.get('nombre'),
        'total_citas':         todas_citas.count(),
        'citas_proximas':      proximas_citas.count(),
        'total_historiales':   Historial_Clinico.objects.filter(id_paciente=paciente_id).count(),
        'total_medicos':       len(set(medicos_ids)),
        'proximas_citas':      proximas_citas,
        'historiales':         historiales,
        'medicos_disponibles': medicos_disponibles,   # <-- necesario para el select del modal
    }
    return render(request, 'dashboard/paciente/inicio_paciente.html', context)
 
 
# ── API: LISTAR TODAS LAS CITAS ───────────────────────────────────────────

def citas_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
 
    paciente_id = request.session.get('usuario_id')
    # Usamos datetime.now() para comparar fecha y hora exacta
    ahora = datetime.now() 
    
    citas = Agendamiento.objects.filter(
        id_paciente=paciente_id
    ).select_related('id_medico').order_by('-fecha', '-hora')
 
    data = []
    for c in citas:
        # Combinamos fecha y hora del modelo para la comparación
        momento_cita = datetime.combine(c.fecha, c.hora)

        if momento_cita < ahora:
            estado_cita = "Cita Cumplida"
        else:
            estado_cita = "Agendada"

        data.append({
            'id':            c.id_agendamiento,
            'cita':          c.cita,
            'fecha':         str(c.fecha),
            'hora':          c.hora.strftime('%H:%M'),
            'medico_nombre': f"{c.id_medico.nombre} {c.id_medico.apellido}",
            'especialidad':  c.id_medico.especialidad,
            'estado':        estado_cita, 
        })
 
    return JsonResponse({'citas': data})
 
# ── API: AGENDAR CITA ─────────────────────────────────────────────────────
@require_POST
def agendar_cita_paciente(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        cita_tipo = data.get('cita', '').strip()
        medico_id = data.get('id_medico')
        fecha_str = data.get('fecha')  # '2026-03-25'
        hora_str  = data.get('hora')   # '08:00'

        if not all([cita_tipo, medico_id, fecha_str, hora_str]):
            return JsonResponse({'error': 'Todos los campos son obligatorios.'}, status=400)

        # --- VALIDACIÓN DE FECHA Y HORA PASADA ---
        ahora = datetime.now()
        fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_cita = datetime.strptime(hora_str, '%H:%M').time()

        # 1. Si la fecha es de ayer o antes
        if fecha_cita < ahora.date():
            return JsonResponse({'error': 'La fecha no puede ser en el pasado.'}, status=400)
        
        # 2. Si la fecha es HOY, validar que la hora no haya pasado
        if fecha_cita == ahora.date() and hora_cita <= ahora.time():
            return JsonResponse({'error': 'Horario no disponible (ya vencido).'}, status=400)
        # ------------------------------------------

        paciente_id = request.session['usuario_id']

        # Validación choque de horario (la que ya tenías)
        choque_horario = Agendamiento.objects.filter(
            id_paciente_id=paciente_id,
            fecha=fecha_str,
            hora=hora_str
        ).exists()

        if choque_horario:
            return JsonResponse({'error': f'Ya tienes una cita programada para esa hora.'}, status=400)

        paciente = get_object_or_404(Paciente, pk=paciente_id)
        medico   = get_object_or_404(Medico, pk=medico_id)

        Agendamiento.objects.create(
            cita=cita_tipo,
            fecha=fecha_str,
            hora=hora_str,
            id_paciente=paciente,
            id_medico=medico,
        )
        return JsonResponse({'ok': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

 
# ── API: REPROGRAMAR CITA ─────────────────────────────────────────────────
@require_POST
def reprogramar_cita_paciente(request, pk):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    cita = get_object_or_404(Agendamiento, pk=pk, id_paciente=request.session['usuario_id'])

    try:
        data = json.loads(request.body)
        nueva_fecha_str = data.get('fecha')
        nueva_hora_str  = data.get('hora')
        
        # --- VALIDACIÓN DE TIEMPO REAL ---
        ahora = datetime.now()
        f_nueva = datetime.strptime(nueva_fecha_str, '%Y-%m-%d').date()
        h_nueva = datetime.strptime(nueva_hora_str, '%H:%M').time()

        if f_nueva < ahora.date():
            return JsonResponse({'error': 'No puedes reprogramar a una fecha pasada.'}, status=400)
        
        if f_nueva == ahora.date() and h_nueva <= ahora.time():
            return JsonResponse({'error': 'Horario no disponible (ya vencido).'}, status=400)
        # ---------------------------------

        paciente_id = request.session['usuario_id']

        choque_paciente = Agendamiento.objects.filter(
            id_paciente_id=paciente_id,
            fecha=nueva_fecha_str,
            hora=nueva_hora_str
        ).exclude(pk=pk).exists()

        if choque_paciente:
            return JsonResponse({'error': 'Ya tienes otra cita a esa misma hora.'}, status=400)

        cita.fecha = nueva_fecha_str
        cita.hora  = nueva_hora_str
        cita.save()
        
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
 
# ── API: CANCELAR CITA ────────────────────────────────────────────────────
@require_POST
def cancelar_cita_paciente(request, pk):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
 
    cita = get_object_or_404(
        Agendamiento,
        pk=pk,
        id_paciente=request.session['usuario_id']
    )
    cita.delete()
    return JsonResponse({'ok': True})
 
 
# ── API: HISTORIAL CLÍNICO ────────────────────────────────────────────────
def historial_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
 
    paciente_id = request.session.get('usuario_id')
    historiales = Historial_Clinico.objects.filter(
        id_paciente=paciente_id
    ).select_related('id_medico').order_by('-fecha_creacion')
 
    data = [{
        'id':            h.id_historial,
        'fecha_creacion': h.fecha_creacion.strftime('%d/%m/%Y'),
        'antecedentes':  h.antecedentes,
        'medico_nombre': f"{h.id_medico.nombre} {h.id_medico.apellido}",
        'especialidad':  h.id_medico.especialidad,
    } for h in historiales]
 
    return JsonResponse({'historiales': data})

# API para filtrar médicos por especialidad
def obtener_medicos_por_especialidad(request):
    especialidad = request.GET.get('especialidad')
    medicos = Medico.objects.filter(especialidad=especialidad, estado=True).values('id_medico', 'nombre', 'apellido')
    return JsonResponse({'medicos': list(medicos)})

# API para calcular disponibilidad de horarios
def obtener_disponibilidad_medico(request):
    medico_id = request.GET.get('medico_id')
    fecha_str = request.GET.get('fecha')
    
    if not medico_id or not fecha_str:
        return JsonResponse({'error': 'Faltan datos'}, status=400)

    # 1. Obtener citas ya agendadas para ese médico en esa fecha
    citas_ocupadas = Agendamiento.objects.filter(
        id_medico_id=medico_id, 
        fecha=fecha_str
    ).values_list('hora', flat=True)
    
    # Convertir a lista de strings "HH:MM" para comparar fácil
    horas_ocupadas = [h.strftime('%H:%M') for h in citas_ocupadas]

    # 2. Generar slots de 30 min (06:00 a 18:00)
    horarios = []
    inicio = datetime.strptime("06:00", "%H:%M")
    fin = datetime.strptime("18:00", "%H:%M")
    
    while inicio < fin:
        hora_slot = inicio.strftime("%H:%M")
        horarios.append({
            'hora': hora_slot,
            'disponible': hora_slot not in horas_ocupadas
        })
        inicio += timedelta(minutes=30)

    return JsonResponse({'horarios': horarios})
 

# =========================================================================
# 👤 GESTIÓN DE PERFILES (APIS JSON)
# =========================================================================

# --- Perfil Admin ---
def perfil_admin_json(request):
    if request.session.get('rol') != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    admin = get_object_or_404(Administrador, pk=request.session['usuario_id'])
    return JsonResponse({
        'nombre': admin.nombre,
        'apellido': admin.apellido,
        'tipo_doc': admin.tipo_doc,
        'numero_doc': admin.numero_doc,
        'genero': admin.genero,
        'telefono': admin.telefono,
        'correo': admin.correo,
        'estado': admin.estado,
    })

@require_POST
def editar_perfil_admin(request):
    if request.session.get('rol') != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    admin = get_object_or_404(Administrador, pk=request.session['usuario_id'])
    try:
        data = json.loads(request.body)
        admin.nombre = data.get('nombre', admin.nombre)
        admin.apellido = data.get('apellido', admin.apellido)
        admin.genero = data.get('genero', admin.genero)
        admin.telefono = data.get('telefono', admin.telefono)
        admin.correo = data.get('correo', admin.correo)
        
        pass_nueva = data.get('contrasena', '').strip()
        if pass_nueva: admin.contrasena = pass_nueva
        
        admin.save()
        request.session['nombre'] = f"{admin.nombre} {admin.apellido}"
        return JsonResponse({'ok': True, 'nombre': request.session['nombre']})
    except:
        return JsonResponse({'error': 'Error al procesar datos'}, status=400)

# --- Perfil Paciente ---
def perfil_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    paciente = get_object_or_404(Paciente, pk=request.session['usuario_id'])
    return JsonResponse({
        'nombre': paciente.nombre,
        'apellido': paciente.apellido,
        'tipo_doc': paciente.tipo_doc,
        'numero_doc': paciente.numero_doc,
        'genero': paciente.genero,
        'fecha_nacimiento': str(paciente.fecha_nacimiento),
        'tipo_sangre': paciente.tipo_sangre,
        'direccion': paciente.direccion,
        'telefono': paciente.telefono,
        'correo': paciente.correo,
        'estado': paciente.estado,
    })

@require_POST
def editar_perfil_paciente(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    paciente = get_object_or_404(Paciente, pk=request.session['usuario_id'])
    try:
        data = json.loads(request.body)
        paciente.nombre    = data.get('nombre',    paciente.nombre)
        paciente.apellido  = data.get('apellido',  paciente.apellido)
        paciente.telefono  = data.get('telefono',  paciente.telefono)
        paciente.correo    = data.get('correo',    paciente.correo)
        paciente.direccion = data.get('direccion', paciente.direccion)

        pass_nueva = data.get('contrasena', '').strip()
        if pass_nueva:
            paciente.contrasena = pass_nueva

        paciente.save()
        request.session['nombre'] = f"{paciente.nombre} {paciente.apellido}"
        return JsonResponse({'ok': True, 'nombre': request.session['nombre']})
    except Exception:
        return JsonResponse({'error': 'Error al procesar datos'}, status=400)

# =========================================================================
# ⚙️ CRUDS PROTEGIDOS (SOLO ADMIN)
# =========================================================================

# --- ADMINISTRADORES ---
class AdminListView(AdminRequiredMixin, ListView):
    model = Administrador
    template_name = 'administradores/ver_administrador.html'
    context_object_name = 'admins'

class AdminCreateView(AdminRequiredMixin, CreateView):
    model = Administrador
    fields = '__all__'
    template_name = 'administradores/crear_administrador.html'
    success_url = reverse_lazy('ver_administrador')

class AdminUpdateView(AdminRequiredMixin, UpdateView):
    model = Administrador
    fields = '__all__'
    template_name = 'administradores/editar_administrador.html'
    success_url = reverse_lazy('ver_administrador')

class AdminDeleteView(AdminRequiredMixin, DeleteView):
    model = Administrador
    template_name = 'administradores/eliminar_administrador.html'
    success_url = reverse_lazy('ver_administrador')

# --- MÉDICOS ---
class MedicoListView(AdminRequiredMixin, ListView):
    model = Medico
    template_name = 'medicos/ver_medicos.html'
    context_object_name = 'medicos'

class MedicoCreateView(AdminRequiredMixin, CreateView):
    model = Medico
    fields = '__all__'
    template_name = 'medicos/crear_medicos.html'
    success_url = reverse_lazy('ver_medicos')

class MedicoUpdateView(AdminRequiredMixin, UpdateView):
    model = Medico
    fields = '__all__'
    template_name = 'medicos/editar_medicos.html'
    success_url = reverse_lazy('ver_medicos')

class MedicoDeleteView(AdminRequiredMixin, DeleteView):
    model = Medico
    template_name = 'medicos/eliminar_medicos.html'
    success_url = reverse_lazy('ver_medicos')

# --- PACIENTES ---
class PacienteListView(AdminRequiredMixin, ListView):
    model = Paciente
    template_name = 'pacientes/ver_pacientes.html'
    context_object_name = 'pacientes'

class PacienteCreateView(AdminRequiredMixin, CreateView):
    model = Paciente
    fields = '__all__'
    template_name = 'pacientes/crear_pacientes.html'
    success_url = reverse_lazy('ver_pacientes')

class PacienteUpdateView(AdminRequiredMixin, UpdateView):
    model = Paciente
    fields = '__all__'
    template_name = 'pacientes/editar_pacientes.html'
    success_url = reverse_lazy('ver_pacientes')

class PacienteDeleteView(AdminRequiredMixin, DeleteView):
    model = Paciente
    template_name = 'pacientes/eliminar_pacientes.html'
    success_url = reverse_lazy('ver_pacientes')

# --- AGENDAMIENTOS ---
class AgendamientoListView(AdminRequiredMixin, ListView):
    model = Agendamiento
    template_name = 'agendamientos/ver_agendamientos.html'
    context_object_name = 'citas'

class AgendamientoCreateView(AdminRequiredMixin, CreateView):
    model = Agendamiento
    fields = '__all__'
    template_name = 'agendamientos/crear_agendamientos.html'
    success_url = reverse_lazy('ver_agendamientos')

class AgendamientoUpdateView(AdminRequiredMixin, UpdateView):
    model = Agendamiento
    fields = '__all__'
    template_name = 'agendamientos/editar_agendamientos.html'
    success_url = reverse_lazy('ver_agendamientos')

class AgendamientoDeleteView(AdminRequiredMixin, DeleteView):
    model = Agendamiento
    template_name = 'agendamientos/eliminar_agendamientos.html'
    success_url = reverse_lazy('ver_agendamientos')

# --- HISTORIAL CLÍNICO ---
class HistorialListView(AdminRequiredMixin, ListView):
    model = Historial_Clinico
    template_name = 'historial_clinico/ver_historiales.html'
    context_object_name = 'historiales'

class HistorialCreateView(AdminRequiredMixin, CreateView):
    model = Historial_Clinico
    fields = '__all__'
    template_name = 'historial_clinico/crear_historiales.html'
    success_url = reverse_lazy('ver_historiales')

class HistorialUpdateView(AdminRequiredMixin, UpdateView):
    model = Historial_Clinico
    fields = '__all__'
    template_name = 'historial_clinico/editar_historiales.html'
    success_url = reverse_lazy('ver_historiales')

class HistorialDeleteView(AdminRequiredMixin, DeleteView):
    model = Historial_Clinico
    template_name = 'historial_clinico/eliminar_historiales.html'
    success_url = reverse_lazy('ver_historiales')