import json
import os
import uuid
from django.utils import timezone
from .models import PasswordResetToken
from dotenv import load_dotenv
from datetime import date
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.contrib.auth.mixins import AccessMixin
from datetime import datetime, timedelta
from django.db.models import Q

from .forms import (
    AdministradorForm, MedicoForm, PacienteForm,
    AgendamientoForm, HistorialForm,
)
from .utils import (
    enviar_confirmacion_cita,
    generar_pdf_administradores, generar_excel_administradores,
    generar_pdf_medicos,         generar_excel_medicos,
    generar_pdf_pacientes,       generar_excel_pacientes,
    generar_pdf_agendamientos,   generar_excel_agendamientos,
    generar_pdf_historial,       generar_excel_historial,
)
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client

from .models import Administrador, Agendamiento, Historial_Clinico, Medico, Paciente

load_dotenv()

# ── SCHEDULER ─────────────────────────────────────────────────────────────
scheduler = BackgroundScheduler()
scheduler.start()

def llamada_twilio_tarea(nombre, especialidad, fecha, hora):
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    if not sid or not token:
        return   
    client = Client(sid, token)
    try:
        client.calls.create(
            twiml=f'''
                <Response>
                    <Say language="es-MX" voice="alice">
                        Hola {nombre}. Te hablamos de Cita Ya.
                        Recordatorio de tu cita de {especialidad} para el {fecha} a las {hora}.
                        En caso de no poder asistir por favor entra a citaya.com y reprogramala.
                        ¡Gracias por usar cita ya!.
                    </Say>
                </Response>
            ''',
            to = os.getenv('TWILIO_TO_NUMBER'),
            from_ = os.getenv('TWILIO_FROM_NUMBER')
        )
        print(f"📞 Llamada enviada a {nombre}")
    except Exception as e:
        print(f"❌ Error en Twilio: {e}")


# =========================================================================
# HELPER INTERNO — aplica filtro de estado de forma segura
# =========================================================================

def _filtrar_estado(qs, estado_str):
    """Aplica filtro de estado solo si el valor es '0' o '1'."""
    if estado_str in ('0', '1'):
        qs = qs.filter(estado=(estado_str == '1'))
    return qs


# =========================================================================
# MIXINS
# =========================================================================

class AdminRequiredMixin(AccessMixin):
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
    request.session.flush()
    return redirect('login')

def login(request):
    if request.method == 'POST':
        numero_doc = request.POST.get('numerodoc')
        password   = request.POST.get('contrasena')

        # ── Administrador ──────────────────────────────────────────────────
        user_admin = Administrador.objects.filter(numero_doc=numero_doc).first()
        if user_admin and user_admin.check_contrasena(password):
            if not user_admin.estado:
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
                return render(request, 'Inicio_Sesion-Registro/login.html')
            request.session['usuario_id'] = user_admin.id_admin
            request.session['rol']        = 'admin'
            request.session['nombre']     = f"{user_admin.nombre} {user_admin.apellido}"
            return redirect('dashboard_admin')

        # ── Médico ─────────────────────────────────────────────────────────
        user_medico = Medico.objects.filter(numero_doc=numero_doc).first()
        if user_medico and user_medico.check_contrasena(password):
            if not user_medico.estado:
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
                return render(request, 'Inicio_Sesion-Registro/login.html')
            request.session['usuario_id'] = user_medico.id_medico
            request.session['rol']        = 'medico'
            request.session['nombre']     = f"{user_medico.nombre} {user_medico.apellido}"
            return redirect('dashboard_medico')

        # ── Paciente ───────────────────────────────────────────────────────
        user_paciente = Paciente.objects.filter(numero_doc=numero_doc).first()
        if user_paciente and user_paciente.check_contrasena(password):
            if not user_paciente.estado:
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
                return render(request, 'Inicio_Sesion-Registro/login.html')
            request.session['usuario_id'] = user_paciente.id_paciente
            request.session['rol']        = 'paciente'
            request.session['nombre']     = f"{user_paciente.nombre} {user_paciente.apellido}"
            return redirect('dashboard_paciente')

        messages.error(request, 'Documento o contraseña incorrectos.')

    return render(request, 'Inicio_Sesion-Registro/login.html')


def registro(request):
    if request.method == 'POST':
        try:
            tipo_doc         = request.POST.get('tipo_doc')
            numero_doc       = request.POST.get('numero_doc')
            nombre           = request.POST.get('nombre')
            apellido         = request.POST.get('apellido')
            genero           = request.POST.get('genero')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            tipo_sangre      = request.POST.get('tipo_sangre')
            telefono         = request.POST.get('telefono')
            correo           = request.POST.get('correo')
            direccion        = request.POST.get('direccion')
            contrasena       = request.POST.get('contrasena')

            if Paciente.objects.filter(numero_doc=numero_doc).exists():
                messages.error(request, 'Ya existe un usuario con ese documento.')
                return redirect('registro')

            Paciente.objects.create(
                tipo_doc=tipo_doc, numero_doc=numero_doc, nombre=nombre,
                apellido=apellido, genero=genero, fecha_nacimiento=fecha_nacimiento,
                tipo_sangre=tipo_sangre, telefono=telefono, correo=correo,
                direccion=direccion,
                contrasena=make_password(contrasena),  # ✅ hashea la contraseña
                estado=True
            )
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('registro')

    return render(request, 'Inicio_Sesion-Registro/registrar.html')


# =========================================================================
# DASHBOARDS
# =========================================================================

@never_cache
def dashboard_admin(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    context = {
        'total_medicos':     Medico.objects.count(),
        'total_pacientes':   Paciente.objects.count(),
        'total_citas':       Agendamiento.objects.count(),
        'total_historiales': Historial_Clinico.objects.count(),
        'nombre':            request.session.get('nombre'),
    }
    return render(request, 'dashboard/administrador/inicio_admin.html', context)


@never_cache
def dashboard_medico(request):
    if request.session.get('rol') != 'medico':
        return redirect('login')

    medico_id      = request.session.get('usuario_id')
    hoy            = date.today()
    todas_citas    = Agendamiento.objects.filter(id_medico=medico_id).select_related('id_paciente')
    proximas_citas = todas_citas.filter(fecha__gte=hoy).order_by('fecha', 'hora')[:5]
    historiales    = Historial_Clinico.objects.filter(id_medico=medico_id).select_related('id_paciente').order_by('-fecha_creacion')[:5]
    pacientes_ids  = todas_citas.values_list('id_paciente', flat=True).distinct()
    pacientes      = Paciente.objects.filter(id_paciente__in=pacientes_ids)

    context = {
        'nombre':            request.session.get('nombre'),
        'total_citas':       todas_citas.count(),
        'citas_proximas':    proximas_citas.count(),
        'total_historiales': Historial_Clinico.objects.filter(id_medico=medico_id).count(),
        'total_pacientes':   len(set(pacientes_ids)),
        'proximas_citas':    proximas_citas,
        'historiales':       historiales,
        'pacientes':         pacientes,
    }
    return render(request, 'dashboard/medico/inicio_medico.html', context)


@never_cache
def dashboard_paciente(request):
    if request.session.get('rol') != 'paciente':
        return redirect('login')

    paciente_id = request.session.get('usuario_id')
    hoy         = date.today()
    ahora       = datetime.now()
    todas_citas = Agendamiento.objects.filter(id_paciente=paciente_id).select_related('id_medico')

    proximas_citas = todas_citas.filter(
        Q(fecha__gt=hoy) | Q(fecha=hoy, hora__gt=ahora.time())
    ).order_by('fecha', 'hora')[:5]

    historiales = Historial_Clinico.objects.filter(
        id_paciente=paciente_id
    ).select_related('id_medico').order_by('-fecha_creacion')[:5]

    medicos_ids         = todas_citas.values_list('id_medico', flat=True).distinct()
    medicos_disponibles = Medico.objects.filter(estado=True).order_by('especialidad', 'nombre')

    context = {
        'nombre':              request.session.get('nombre'),
        'total_citas':         todas_citas.count(),
        'citas_proximas':      todas_citas.filter(
            Q(fecha__gt=hoy) | Q(fecha=hoy, hora__gt=ahora.time())
        ).count(),
        'total_historiales':   Historial_Clinico.objects.filter(id_paciente=paciente_id).count(),
        'total_medicos':       len(set(medicos_ids)),
        'proximas_citas':      proximas_citas,
        'historiales':         historiales,
        'medicos_disponibles': medicos_disponibles,
    }
    return render(request, 'dashboard/paciente/inicio_paciente.html', context)


# =========================================================================
# APIs DE PACIENTE
# =========================================================================

def citas_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    paciente_id = request.session.get('usuario_id')
    ahora       = datetime.now()
    citas       = Agendamiento.objects.filter(id_paciente=paciente_id).select_related('id_medico').order_by('-fecha', '-hora')

    data = []
    for c in citas:
        momento_cita = datetime.combine(c.fecha, c.hora)
        estado_cita  = "Cita Cumplida" if momento_cita < ahora else "Agendada"
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


@require_POST
def agendar_cita_paciente(request):
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if not sid or not token:
        return JsonResponse({'error': 'Error de autenticación'}, status=403)
    try:
        data      = json.loads(request.body)
        cita_tipo = data.get('cita')
        medico_id = data.get('id_medico')
        fecha_str = data.get('fecha')
        hora_str  = data.get('hora')

        if not all([cita_tipo, medico_id, fecha_str, hora_str]):
            return JsonResponse({'error': 'Faltan datos en el formulario.'}, status=400)

        ahora      = datetime.now()
        fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_cita  = datetime.strptime(hora_str, '%H:%M').time()

        if fecha_cita < ahora.date():
            return JsonResponse({'error': 'No puedes agendar en el pasado.'}, status=400)
        if fecha_cita == ahora.date() and hora_cita <= ahora.time():
            return JsonResponse({'error': 'La hora ya pasó.'}, status=400)

        paciente_id = request.session['usuario_id']
        if Agendamiento.objects.filter(id_paciente_id=paciente_id, fecha=fecha_str, hora=hora_str).exists():
            return JsonResponse({'error': 'Ya tienes una cita a esta hora.'}, status=400)

        paciente   = get_object_or_404(Paciente, pk=paciente_id)
        medico     = get_object_or_404(Medico, pk=medico_id)
        nueva_cita = Agendamiento.objects.create(
            cita=cita_tipo, fecha=fecha_str, hora=hora_str,
            id_paciente=paciente, id_medico=medico,
        )

        try:
            enviar_confirmacion_cita(paciente, nueva_cita)
        except Exception as e:
            print(f"Error de correo: {e}")

        momento_llamada = datetime.now() + timedelta(seconds=30)
        fecha_para_voz  = fecha_cita.strftime('%d de %B')
        scheduler.add_job(
            llamada_twilio_tarea, trigger='date', run_date=momento_llamada,
            args=[paciente.nombre, cita_tipo, fecha_para_voz, hora_str],
            id=f'llamada_{nueva_cita.id_agendamiento}', replace_existing=True
        )
        return JsonResponse({'ok': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def reprogramar_cita_paciente(request, pk):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    cita = get_object_or_404(Agendamiento, pk=pk, id_paciente=request.session['usuario_id'])
    try:
        data            = json.loads(request.body)
        nueva_fecha_str = data.get('fecha')
        nueva_hora_str  = data.get('hora')

        ahora   = datetime.now()
        f_nueva = datetime.strptime(nueva_fecha_str, '%Y-%m-%d').date()
        h_nueva = datetime.strptime(nueva_hora_str, '%H:%M').time()

        if f_nueva < ahora.date():
            return JsonResponse({'error': 'No puedes reprogramar a una fecha pasada.'}, status=400)
        if f_nueva == ahora.date() and h_nueva <= ahora.time():
            return JsonResponse({'error': 'Horario no disponible (ya vencido).'}, status=400)

        paciente_id = request.session['usuario_id']
        if Agendamiento.objects.filter(id_paciente_id=paciente_id, fecha=nueva_fecha_str, hora=nueva_hora_str).exclude(pk=pk).exists():
            return JsonResponse({'error': 'Ya tienes otra cita a esa misma hora.'}, status=400)

        cita.fecha = nueva_fecha_str
        cita.hora  = nueva_hora_str
        cita.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def cancelar_cita_paciente(request, pk):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    cita = get_object_or_404(Agendamiento, pk=pk, id_paciente=request.session['usuario_id'])
    cita.delete()
    return JsonResponse({'ok': True})


def historial_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    paciente_id = request.session.get('usuario_id')
    historiales = Historial_Clinico.objects.filter(id_paciente=paciente_id).select_related('id_medico').order_by('-fecha_creacion')

    data = [{
        'id':             h.id_historial,
        'fecha_creacion': h.fecha_creacion.strftime('%d/%m/%Y'),
        'antecedentes':   h.antecedentes,
        'medico_nombre':  f"{h.id_medico.nombre} {h.id_medico.apellido}",
        'especialidad':   h.id_medico.especialidad,
    } for h in historiales]
    return JsonResponse({'historiales': data})


def obtener_medicos_por_especialidad(request):
    especialidad = request.GET.get('especialidad')
    medicos = Medico.objects.filter(especialidad=especialidad, estado=True).values('id_medico', 'nombre', 'apellido')
    return JsonResponse({'medicos': list(medicos)})


def obtener_disponibilidad_medico(request):
    medico_id = request.GET.get('medico_id')
    fecha_str = request.GET.get('fecha')

    if not medico_id or not fecha_str:
        return JsonResponse({'error': 'Faltan datos'}, status=400)

    citas_ocupadas = Agendamiento.objects.filter(id_medico_id=medico_id, fecha=fecha_str).values_list('hora', flat=True)
    horas_ocupadas = [h.strftime('%H:%M') for h in citas_ocupadas]

    horarios = []
    inicio   = datetime.strptime("06:00", "%H:%M")
    fin      = datetime.strptime("18:00", "%H:%M")

    while inicio < fin:
        hora_slot = inicio.strftime("%H:%M")
        horarios.append({'hora': hora_slot, 'disponible': hora_slot not in horas_ocupadas})
        inicio += timedelta(minutes=30)

    return JsonResponse({'horarios': horarios})


# =========================================================================
# PERFILES (APIs JSON)
# =========================================================================

def perfil_admin_json(request):
    if request.session.get('rol') != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    admin = get_object_or_404(Administrador, pk=request.session['usuario_id'])
    return JsonResponse({
        'nombre':     admin.nombre,
        'apellido':   admin.apellido,
        'tipo_doc':   admin.tipo_doc,
        'numero_doc': admin.numero_doc,
        'genero':     admin.genero,
        'telefono':   admin.telefono,
        'correo':     admin.correo,
        'estado':     admin.estado,
    })


@require_POST
def editar_perfil_admin(request):
    if request.session.get('rol') != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    admin = get_object_or_404(Administrador, pk=request.session['usuario_id'])
    try:
        data           = json.loads(request.body)
        admin.nombre   = data.get('nombre',   admin.nombre)
        admin.apellido = data.get('apellido', admin.apellido)
        admin.genero   = data.get('genero',   admin.genero)
        admin.telefono = data.get('telefono', admin.telefono)
        admin.correo   = data.get('correo',   admin.correo)
        pw = data.get('contrasena', '').strip()
        if pw:
            admin.set_contrasena(pw)  # ✅ hashea la nueva contraseña
        admin.save()
        request.session['nombre'] = f"{admin.nombre} {admin.apellido}"
        return JsonResponse({'ok': True, 'nombre': request.session['nombre']})
    except Exception:
        return JsonResponse({'error': 'Error al procesar datos'}, status=400)


def perfil_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    paciente = get_object_or_404(Paciente, pk=request.session['usuario_id'])
    return JsonResponse({
        'nombre':           paciente.nombre,
        'apellido':         paciente.apellido,
        'tipo_doc':         paciente.tipo_doc,
        'numero_doc':       paciente.numero_doc,
        'genero':           paciente.genero,
        'fecha_nacimiento': str(paciente.fecha_nacimiento),
        'tipo_sangre':      paciente.tipo_sangre,
        'direccion':        paciente.direccion,
        'telefono':         paciente.telefono,
        'correo':           paciente.correo,
        'estado':           paciente.estado,
    })


@require_POST
def editar_perfil_paciente(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    paciente = get_object_or_404(Paciente, pk=request.session['usuario_id'])
    try:
        data               = json.loads(request.body)
        paciente.nombre    = data.get('nombre',    paciente.nombre)
        paciente.apellido  = data.get('apellido',  paciente.apellido)
        paciente.telefono  = data.get('telefono',  paciente.telefono)
        paciente.correo    = data.get('correo',    paciente.correo)
        paciente.direccion = data.get('direccion', paciente.direccion)
        pw = data.get('contrasena', '').strip()
        if pw:
            paciente.set_contrasena(pw)  # ✅ hashea la nueva contraseña
        paciente.save()
        request.session['nombre'] = f"{paciente.nombre} {paciente.apellido}"
        return JsonResponse({'ok': True, 'nombre': request.session['nombre']})
    except Exception:
        return JsonResponse({'error': 'Error al procesar datos'}, status=400)


# =========================================================================
# APIs MÉDICO
# =========================================================================

def agenda_medico_json(request):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    session_id = request.session.get('usuario_id')
    fecha_str  = request.GET.get('fecha', str(date.today()))

    try:
        fecha_obj        = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        medico_instancia = get_object_or_404(Medico, id_medico=session_id)
    except ValueError:
        return JsonResponse({'error': 'Fecha inválida'}, status=400)

    citas = (
        Agendamiento.objects
        .filter(id_medico=medico_instancia, fecha=fecha_obj)
        .select_related('id_paciente')
        .order_by('hora')
    )
    historiales_hoy = set(
        Historial_Clinico.objects
        .filter(id_medico=medico_instancia, fecha_creacion=fecha_obj)
        .values_list('id_paciente_id', flat=True)
    )

    data = [{
        'id_agendamiento': c.id_agendamiento,
        'hora':            c.hora.strftime('%H:%M'),
        'tipo_cita':       c.cita,
        'id_paciente':     c.id_paciente.id_paciente,
        'paciente_nombre': f"{c.id_paciente.nombre} {c.id_paciente.apellido}",
        'paciente_doc':    c.id_paciente.numero_doc,
        'cumplida':        (c.id_paciente.id_paciente in historiales_hoy),
    } for c in citas]
    return JsonResponse({'citas': data})


def paciente_medico_json(request, pk):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    paciente = get_object_or_404(Paciente, pk=pk)
    return JsonResponse({
        'nombre':           paciente.nombre,
        'apellido':         paciente.apellido,
        'tipo_doc':         paciente.tipo_doc,
        'numero_doc':       paciente.numero_doc,
        'genero':           paciente.genero,
        'fecha_nacimiento': str(paciente.fecha_nacimiento),
        'tipo_sangre':      paciente.tipo_sangre,
        'telefono':         paciente.telefono,
        'correo':           paciente.correo,
        'direccion':        paciente.direccion,
        'estado':           paciente.estado,
    })


def historial_paciente_medico_json(request, pk):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    medico_id   = request.session.get('usuario_id')
    paciente    = get_object_or_404(Paciente, pk=pk)
    historiales = (
        Historial_Clinico.objects.filter(id_paciente=paciente)
        .select_related('id_medico').order_by('-fecha_creacion')
    )
    data = [{
        'id_historial':    h.id_historial,
        'fecha_creacion':  h.fecha_creacion.strftime('%d/%m/%Y'),
        'antecedentes':    h.antecedentes,
        'medico_nombre':   f"{h.id_medico.nombre} {h.id_medico.apellido}",
        'especialidad':    h.id_medico.especialidad,
        'paciente_nombre': f"{paciente.nombre} {paciente.apellido}",
        'es_propio':       (h.id_medico.id_medico == medico_id),
    } for h in historiales]
    return JsonResponse({'historiales': data})


@require_POST
def guardar_historial_medico(request):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    medico_id = request.session.get('usuario_id')
    try:
        data         = json.loads(request.body)
        antecedentes = data.get('antecedentes', '').strip()
        paciente_id  = data.get('id_paciente')

        if not antecedentes:
            return JsonResponse({'error': 'Las notas no pueden estar vacías.'}, status=400)
        if not paciente_id:
            return JsonResponse({'error': 'Paciente no especificado.'}, status=400)

        paciente = get_object_or_404(Paciente, pk=paciente_id)
        medico   = get_object_or_404(Medico, pk=medico_id)
        hoy      = date.today()

        if Historial_Clinico.objects.filter(id_medico=medico, id_paciente=paciente, fecha_creacion=hoy).exists():
            return JsonResponse({'error': 'Ya registraste un historial para este paciente hoy.'}, status=400)

        historial = Historial_Clinico.objects.create(
            antecedentes=antecedentes, id_paciente=paciente, id_medico=medico,
        )
        return JsonResponse({
            'ok':              True,
            'paciente_nombre': f"{paciente.nombre} {paciente.apellido}",
            'id_historial':    historial.id_historial,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def perfil_medico_json(request):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    medico = get_object_or_404(Medico, pk=request.session['usuario_id'])
    return JsonResponse({
        'nombre':       medico.nombre,
        'apellido':     medico.apellido,
        'tipo_doc':     medico.tipo_doc,
        'numero_doc':   medico.numero_doc,
        'genero':       medico.genero,
        'especialidad': medico.especialidad,
        'telefono':     medico.telefono,
        'correo':       medico.correo,
        'estado':       medico.estado,
    })


@require_POST
def editar_perfil_medico(request):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    medico = get_object_or_404(Medico, pk=request.session['usuario_id'])
    try:
        data            = json.loads(request.body)
        medico.nombre   = data.get('nombre',   medico.nombre)
        medico.apellido = data.get('apellido', medico.apellido)
        medico.telefono = data.get('telefono', medico.telefono)
        medico.correo   = data.get('correo',   medico.correo)
        pw = data.get('contrasena', '').strip()
        if pw:
            medico.set_contrasena(pw)  # ✅ hashea la nueva contraseña
        medico.save()
        request.session['nombre'] = f"{medico.nombre} {medico.apellido}"
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =========================================================================
# HELPER: aplica filtro multicriterio con Q objects
# =========================================================================

def _aplicar_filtro(queryset, q_term, *campos):
    if not q_term:
        return queryset, ''
    condicion = Q()
    for campo in campos:
        condicion |= Q(**{f"{campo}__icontains": q_term})
    return queryset.filter(condicion), q_term


# =========================================================================
# CRUDS PROTEGIDOS — ADMINISTRADORES
# =========================================================================

class AdminListView(AdminRequiredMixin, ListView):
    model               = Administrador
    template_name       = 'administradores/ver_administrador.html'
    context_object_name = 'admins'

    def get_queryset(self):
        qs       = super().get_queryset()
        q        = self.request.GET.get('q', '').strip()
        genero   = self.request.GET.get('genero', '').strip()
        estado   = self.request.GET.get('estado', '').strip()
        tipo_doc = self.request.GET.get('tipo_doc', '').strip()

        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(apellido__icontains=q) |
                Q(numero_doc__icontains=q) | Q(correo__icontains=q) |
                Q(telefono__icontains=q)
            )
        if genero:
            qs = qs.filter(genero=genero)
        qs = _filtrar_estado(qs, estado)
        if tipo_doc:
            qs = qs.filter(tipo_doc=tipo_doc)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q']           = self.request.GET.get('q', '')
        ctx['genero']      = self.request.GET.get('genero', '')
        ctx['estado']      = self.request.GET.get('estado', '')
        ctx['tipo_doc']    = self.request.GET.get('tipo_doc', '')
        ctx['hay_filtros'] = any([ctx['q'], ctx['genero'], ctx['estado'], ctx['tipo_doc']])
        return ctx


def reporte_administradores(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    q        = request.GET.get('q', '').strip()
    genero   = request.GET.get('genero', '').strip()
    estado   = request.GET.get('estado', '').strip()
    tipo_doc = request.GET.get('tipo_doc', '').strip()
    tipo     = request.GET.get('tipo', 'pdf')

    qs = Administrador.objects.all()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) |
            Q(numero_doc__icontains=q) | Q(correo__icontains=q) |
            Q(telefono__icontains=q)
        )
    if genero:
        qs = qs.filter(genero=genero)
    qs = _filtrar_estado(qs, estado)
    if tipo_doc:
        qs = qs.filter(tipo_doc=tipo_doc)

    if tipo == 'excel':
        data     = generar_excel_administradores(qs)
        response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="administradores.xlsx"'
    else:
        data     = generar_pdf_administradores(qs)
        response = HttpResponse(data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="administradores.pdf"'
    return response


class AdminCreateView(AdminRequiredMixin, CreateView):
    model         = Administrador
    form_class    = AdministradorForm
    template_name = 'administradores/crear_administrador.html'
    success_url   = reverse_lazy('ver_administrador')

class AdminUpdateView(AdminRequiredMixin, UpdateView):
    model         = Administrador
    form_class    = AdministradorForm
    template_name = 'administradores/editar_administrador.html'
    success_url   = reverse_lazy('ver_administrador')

class AdminDeleteView(AdminRequiredMixin, DeleteView):
    model         = Administrador
    template_name = 'administradores/eliminar_administrador.html'
    success_url   = reverse_lazy('ver_administrador')


# =========================================================================
# CRUDS PROTEGIDOS — MÉDICOS
# =========================================================================

class MedicoListView(AdminRequiredMixin, ListView):
    model               = Medico
    template_name       = 'medicos/ver_medicos.html'
    context_object_name = 'medicos'

    def get_queryset(self):
        qs           = super().get_queryset()
        q            = self.request.GET.get('q', '').strip()
        genero       = self.request.GET.get('genero', '').strip()
        estado       = self.request.GET.get('estado', '').strip()
        tipo_doc     = self.request.GET.get('tipo_doc', '').strip()
        especialidad = self.request.GET.get('especialidad', '').strip()

        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(apellido__icontains=q) |
                Q(numero_doc__icontains=q) | Q(correo__icontains=q) |
                Q(especialidad__icontains=q) | Q(telefono__icontains=q)
            )
        if genero:
            qs = qs.filter(genero=genero)
        qs = _filtrar_estado(qs, estado)
        if tipo_doc:
            qs = qs.filter(tipo_doc=tipo_doc)
        if especialidad:
            qs = qs.filter(especialidad=especialidad)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q']            = self.request.GET.get('q', '')
        ctx['genero']       = self.request.GET.get('genero', '')
        ctx['estado']       = self.request.GET.get('estado', '')
        ctx['tipo_doc']     = self.request.GET.get('tipo_doc', '')
        ctx['especialidad'] = self.request.GET.get('especialidad', '')
        ctx['especialidades'] = Medico.objects.values_list('especialidad', flat=True).distinct().order_by('especialidad')
        ctx['hay_filtros']  = any([ctx['q'], ctx['genero'], ctx['estado'], ctx['tipo_doc'], ctx['especialidad']])
        return ctx


def reporte_medicos(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    q            = request.GET.get('q', '').strip()
    genero       = request.GET.get('genero', '').strip()
    estado       = request.GET.get('estado', '').strip()
    tipo_doc     = request.GET.get('tipo_doc', '').strip()
    especialidad = request.GET.get('especialidad', '').strip()
    tipo         = request.GET.get('tipo', 'pdf')

    qs = Medico.objects.all()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) |
            Q(numero_doc__icontains=q) | Q(correo__icontains=q) |
            Q(especialidad__icontains=q) | Q(telefono__icontains=q)
        )
    if genero:
        qs = qs.filter(genero=genero)
    qs = _filtrar_estado(qs, estado)
    if tipo_doc:
        qs = qs.filter(tipo_doc=tipo_doc)
    if especialidad:
        qs = qs.filter(especialidad=especialidad)

    if tipo == 'excel':
        data     = generar_excel_medicos(qs)
        response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="medicos.xlsx"'
    else:
        data     = generar_pdf_medicos(qs)
        response = HttpResponse(data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="medicos.pdf"'
    return response


class MedicoCreateView(AdminRequiredMixin, CreateView):
    model         = Medico
    form_class    = MedicoForm
    template_name = 'medicos/crear_medicos.html'
    success_url   = reverse_lazy('ver_medicos')

class MedicoUpdateView(AdminRequiredMixin, UpdateView):
    model         = Medico
    form_class    = MedicoForm
    template_name = 'medicos/editar_medicos.html'
    success_url   = reverse_lazy('ver_medicos')

class MedicoDeleteView(AdminRequiredMixin, DeleteView):
    model         = Medico
    template_name = 'medicos/eliminar_medicos.html'
    success_url   = reverse_lazy('ver_medicos')


# =========================================================================
# CRUDS PROTEGIDOS — PACIENTES
# =========================================================================

class PacienteListView(AdminRequiredMixin, ListView):
    model               = Paciente
    template_name       = 'pacientes/ver_pacientes.html'
    context_object_name = 'pacientes'

    def get_queryset(self):
        qs          = super().get_queryset()
        q           = self.request.GET.get('q', '').strip()
        genero      = self.request.GET.get('genero', '').strip()
        estado      = self.request.GET.get('estado', '').strip()
        tipo_doc    = self.request.GET.get('tipo_doc', '').strip()
        tipo_sangre = self.request.GET.get('tipo_sangre', '').strip()

        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(apellido__icontains=q) |
                Q(numero_doc__icontains=q) | Q(correo__icontains=q) |
                Q(telefono__icontains=q) | Q(tipo_sangre__icontains=q)
            )
        if genero:
            qs = qs.filter(genero=genero)
        qs = _filtrar_estado(qs, estado)
        if tipo_doc:
            qs = qs.filter(tipo_doc=tipo_doc)
        if tipo_sangre:
            qs = qs.filter(tipo_sangre=tipo_sangre)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q']           = self.request.GET.get('q', '')
        ctx['genero']      = self.request.GET.get('genero', '')
        ctx['estado']      = self.request.GET.get('estado', '')
        ctx['tipo_doc']    = self.request.GET.get('tipo_doc', '')
        ctx['tipo_sangre'] = self.request.GET.get('tipo_sangre', '')
        ctx['hay_filtros'] = any([ctx['q'], ctx['genero'], ctx['estado'], ctx['tipo_doc'], ctx['tipo_sangre']])
        return ctx


def reporte_pacientes(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    q           = request.GET.get('q', '').strip()
    genero      = request.GET.get('genero', '').strip()
    estado      = request.GET.get('estado', '').strip()
    tipo_doc    = request.GET.get('tipo_doc', '').strip()
    tipo_sangre = request.GET.get('tipo_sangre', '').strip()
    tipo        = request.GET.get('tipo', 'pdf')

    qs = Paciente.objects.all()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) |
            Q(numero_doc__icontains=q) | Q(correo__icontains=q) |
            Q(telefono__icontains=q) | Q(tipo_sangre__icontains=q)
        )
    if genero:
        qs = qs.filter(genero=genero)
    qs = _filtrar_estado(qs, estado)
    if tipo_doc:
        qs = qs.filter(tipo_doc=tipo_doc)
    if tipo_sangre:
        qs = qs.filter(tipo_sangre=tipo_sangre)

    if tipo == 'excel':
        data     = generar_excel_pacientes(qs)
        response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="pacientes.xlsx"'
    else:
        data     = generar_pdf_pacientes(qs)
        response = HttpResponse(data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="pacientes.pdf"'
    return response


class PacienteCreateView(AdminRequiredMixin, CreateView):
    model         = Paciente
    form_class    = PacienteForm
    template_name = 'pacientes/crear_pacientes.html'
    success_url   = reverse_lazy('ver_pacientes')

class PacienteUpdateView(AdminRequiredMixin, UpdateView):
    model         = Paciente
    form_class    = PacienteForm
    template_name = 'pacientes/editar_pacientes.html'
    success_url   = reverse_lazy('ver_pacientes')

class PacienteDeleteView(AdminRequiredMixin, DeleteView):
    model         = Paciente
    template_name = 'pacientes/eliminar_pacientes.html'
    success_url   = reverse_lazy('ver_pacientes')


# =========================================================================
# CRUDS PROTEGIDOS — AGENDAMIENTOS
# =========================================================================

class AgendamientoListView(AdminRequiredMixin, ListView):
    model               = Agendamiento
    template_name       = 'agendamientos/ver_agendamientos.html'
    context_object_name = 'citas'

    def get_queryset(self):
        qs          = super().get_queryset().select_related('id_paciente', 'id_medico')
        q           = self.request.GET.get('q', '').strip()
        fecha_desde = self.request.GET.get('fecha_desde', '').strip()
        fecha_hasta = self.request.GET.get('fecha_hasta', '').strip()
        tipo_cita   = self.request.GET.get('tipo_cita', '').strip()

        if q:
            qs = qs.filter(
                Q(cita__icontains=q) |
                Q(id_paciente__nombre__icontains=q) | Q(id_paciente__apellido__icontains=q) |
                Q(id_paciente__numero_doc__icontains=q) |
                Q(id_medico__nombre__icontains=q) | Q(id_medico__apellido__icontains=q) |
                Q(id_medico__especialidad__icontains=q)
            )
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if tipo_cita:
            qs = qs.filter(cita=tipo_cita)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q']           = self.request.GET.get('q', '')
        ctx['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        ctx['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        ctx['tipo_cita']   = self.request.GET.get('tipo_cita', '')
        ctx['tipos_cita']  = Agendamiento.objects.values_list('cita', flat=True).distinct().order_by('cita')
        ctx['hay_filtros'] = any([ctx['q'], ctx['fecha_desde'], ctx['fecha_hasta'], ctx['tipo_cita']])
        return ctx


def reporte_agendamientos(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    q           = request.GET.get('q', '').strip()
    tipo_cita   = request.GET.get('tipo_cita', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    tipo        = request.GET.get('tipo', 'pdf')

    qs = Agendamiento.objects.select_related('id_paciente', 'id_medico').all()
    if q:
        qs = qs.filter(
            Q(cita__icontains=q) |
            Q(id_paciente__nombre__icontains=q) | Q(id_paciente__apellido__icontains=q) |
            Q(id_paciente__numero_doc__icontains=q) |
            Q(id_medico__nombre__icontains=q) | Q(id_medico__apellido__icontains=q)
        )
    if tipo_cita:
        qs = qs.filter(cita=tipo_cita)
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    if tipo == 'excel':
        data     = generar_excel_agendamientos(qs)
        response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="agendamientos.xlsx"'
    else:
        data     = generar_pdf_agendamientos(qs)
        response = HttpResponse(data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="agendamientos.pdf"'
    return response


class AgendamientoCreateView(AdminRequiredMixin, CreateView):
    model         = Agendamiento
    form_class    = AgendamientoForm
    template_name = 'agendamientos/crear_agendamientos.html'
    success_url   = reverse_lazy('ver_agendamientos')

class AgendamientoUpdateView(AdminRequiredMixin, UpdateView):
    model         = Agendamiento
    form_class    = AgendamientoForm
    template_name = 'agendamientos/editar_agendamientos.html'
    success_url   = reverse_lazy('ver_agendamientos')

class AgendamientoDeleteView(AdminRequiredMixin, DeleteView):
    model         = Agendamiento
    template_name = 'agendamientos/eliminar_agendamientos.html'
    success_url   = reverse_lazy('ver_agendamientos')


# =========================================================================
# CRUDS PROTEGIDOS — HISTORIAL CLÍNICO
# =========================================================================

class HistorialListView(AdminRequiredMixin, ListView):
    model               = Historial_Clinico
    template_name       = 'historial_clinico/ver_historiales.html'
    context_object_name = 'historiales'

    def get_queryset(self):
        qs           = super().get_queryset().select_related('id_paciente', 'id_medico')
        q            = self.request.GET.get('q', '').strip()
        fecha_desde  = self.request.GET.get('fecha_desde', '').strip()
        fecha_hasta  = self.request.GET.get('fecha_hasta', '').strip()
        especialidad = self.request.GET.get('especialidad', '').strip()

        if q:
            qs = qs.filter(
                Q(antecedentes__icontains=q) |
                Q(id_paciente__nombre__icontains=q) | Q(id_paciente__apellido__icontains=q) |
                Q(id_paciente__numero_doc__icontains=q) |
                Q(id_medico__nombre__icontains=q) | Q(id_medico__apellido__icontains=q) |
                Q(id_medico__especialidad__icontains=q)
            )
        if fecha_desde:
            qs = qs.filter(fecha_creacion__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_creacion__lte=fecha_hasta)
        if especialidad:
            qs = qs.filter(id_medico__especialidad=especialidad)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q']            = self.request.GET.get('q', '')
        ctx['fecha_desde']  = self.request.GET.get('fecha_desde', '')
        ctx['fecha_hasta']  = self.request.GET.get('fecha_hasta', '')
        ctx['especialidad'] = self.request.GET.get('especialidad', '')
        ctx['especialidades'] = Medico.objects.values_list('especialidad', flat=True).distinct().order_by('especialidad')
        ctx['hay_filtros']  = any([ctx['q'], ctx['fecha_desde'], ctx['fecha_hasta'], ctx['especialidad']])
        return ctx


def reporte_historiales(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')
    q            = request.GET.get('q', '').strip()
    especialidad = request.GET.get('especialidad', '').strip()
    fecha_desde  = request.GET.get('fecha_desde', '').strip()
    fecha_hasta  = request.GET.get('fecha_hasta', '').strip()
    tipo         = request.GET.get('tipo', 'pdf')

    qs = Historial_Clinico.objects.select_related('id_paciente', 'id_medico').all()
    if q:
        qs = qs.filter(
            Q(antecedentes__icontains=q) |
            Q(id_paciente__nombre__icontains=q) | Q(id_paciente__apellido__icontains=q) |
            Q(id_paciente__numero_doc__icontains=q) |
            Q(id_medico__nombre__icontains=q) | Q(id_medico__apellido__icontains=q)
        )
    if especialidad:
        qs = qs.filter(id_medico__especialidad=especialidad)
    if fecha_desde:
        qs = qs.filter(fecha_creacion__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_creacion__lte=fecha_hasta)

    if tipo == 'excel':
        data     = generar_excel_historial(qs)
        response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="historiales.xlsx"'
    else:
        data     = generar_pdf_historial(qs)
        response = HttpResponse(data, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="historiales.pdf"'
    return response


class HistorialCreateView(AdminRequiredMixin, CreateView):
    model         = Historial_Clinico
    form_class    = HistorialForm
    template_name = 'historial_clinico/crear_historiales.html'
    success_url   = reverse_lazy('ver_historiales')

class HistorialUpdateView(AdminRequiredMixin, UpdateView):
    model         = Historial_Clinico
    form_class    = HistorialForm
    template_name = 'historial_clinico/editar_historiales.html'
    success_url   = reverse_lazy('ver_historiales')

class HistorialDeleteView(AdminRequiredMixin, DeleteView):
    model         = Historial_Clinico
    template_name = 'historial_clinico/eliminar_historiales.html'
    success_url   = reverse_lazy('ver_historiales')


import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password
from .models import Medico

def importar_medicos(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(archivo)

            # Columnas requeridas
            columnas_requeridas = ['TIPO_DOC', 'NUMERO_DOC', 'NOMBRE', 'APELLIDO',
                                   'GENERO', 'ESPECIALIDAD', 'TELEFONO', 'CORREO']
            for col in columnas_requeridas:
                if col not in df.columns:
                    messages.error(request, f"El archivo no tiene la columna requerida: {col}")
                    return redirect('dashboard_admin')

            password_segura = "Admincitaya0*"
            creados    = 0
            duplicados = []  # Lista de mensajes de error por fila

            for index, fila in df.iterrows():
                numero_doc = str(fila['NUMERO_DOC']).strip()
                correo     = str(fila['CORREO']).strip()
                nombre     = str(fila['NOMBRE']).strip()
                apellido   = str(fila['APELLIDO']).strip()

                # Verificar duplicado por número de documento
                if Medico.objects.filter(numero_doc=numero_doc).exists():
                    duplicados.append(
                        f"Fila {index + 2}: {nombre} {apellido} — "
                        f"el documento '{numero_doc}' ya está registrado."
                    )
                    continue  # Saltar este registro

                # Verificar duplicado por correo
                if Medico.objects.filter(correo=correo).exists():
                    duplicados.append(
                        f"Fila {index + 2}: {nombre} {apellido} — "
                        f"el correo '{correo}' ya está registrado."
                    )
                    continue  # Saltar este registro

                # Si no hay duplicado, crear el médico
                Medico.objects.create(
                    tipo_doc     = str(fila['TIPO_DOC']).strip(),
                    numero_doc   = numero_doc,
                    nombre       = nombre,
                    apellido     = apellido,
                    genero       = str(fila['GENERO']).strip(),
                    especialidad = str(fila['ESPECIALIDAD']).strip(),
                    telefono     = str(fila['TELEFONO']).strip(),
                    correo       = correo,
                    contrasena   = make_password(password_segura),
                    estado       = True,
                )
                creados += 1

            # Mensajes de resultado
            if creados > 0:
                messages.success(
                    request,
                    f"✔ {creados} médico(s) importado(s) correctamente. "
                    f"Clave temporal: {password_segura}"
                )
            if duplicados:
                for msg in duplicados:
                    messages.warning(request, f"⚠ Duplicado omitido — {msg}")
            if creados == 0 and not duplicados:
                messages.info(request, "El archivo no contenía registros válidos.")

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {e}")

    return redirect('dashboard_admin')

# =========================================================================
# RECUPERACIÓN DE CONTRASEÑA
# =========================================================================
from django.contrib.auth.hashers import make_password

def _enviar_correo_reset(destinatario, nombre, reset_url):
    import resend
    from django.template.loader import render_to_string
    from django.conf import settings

    html = render_to_string('emails/reset_password.html', {
        'nombre':    nombre,
        'correo':    destinatario,
        'reset_url': reset_url,
    })

    resend.Emails.send({
        "from":    settings.SUPPORT_FROM_EMAIL,
        "to":      [destinatario],
        "subject": "CitaYa — Recupera tu contraseña",
        "html":    html,
    })


def solicitar_reset(request):
    """Paso 1 — el usuario escribe su correo."""
    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()

        # Buscar en los tres modelos
        usuario = None
        rol     = None

        obj = Administrador.objects.filter(correo__iexact=correo).first()
        if obj:
            usuario, rol = obj, 'admin'

        if not usuario:
            obj = Medico.objects.filter(correo__iexact=correo).first()
            if obj:
                usuario, rol = obj, 'medico'

        if not usuario:
            obj = Paciente.objects.filter(correo__iexact=correo).first()
            if obj:
                usuario, rol = obj, 'paciente'

        if usuario:
            # Invalida tokens anteriores de ese correo
            PasswordResetToken.objects.filter(correo__iexact=correo, usado=False).update(usado=True)

            token_obj = PasswordResetToken.objects.create(
                rol        = rol,
                usuario_id = getattr(usuario, f'id_{rol}') if rol != 'admin' else usuario.id_admin,
                correo     = correo,
            )

            reset_url = request.build_absolute_uri(
                f'/recuperar/confirmar/{token_obj.token}/'
            )

            try:
                nombre = f"{usuario.nombre} {usuario.apellido}"
                _enviar_correo_reset(correo, nombre, reset_url)
            except Exception as e:
                print(f"Error enviando correo reset: {e}")
                messages.error(request, 'No se pudo enviar el correo. Intenta más tarde.')
                return render(request, 'Inicio_Sesion-Registro/recuperar_solicitud.html')

        # Siempre mostramos el mismo mensaje (seguridad — no revelar si el correo existe)
        messages.success(request, 'Si ese correo está registrado, recibirás un enlace en breve.')
        return redirect('solicitar_reset')

    return render(request, 'Inicio_Sesion-Registro/recuperar_solicitud.html')


def confirmar_reset(request, token):
    """Paso 2 — el usuario llega desde el enlace del correo."""
    token_obj = PasswordResetToken.objects.filter(token=token).first()

    if not token_obj or not token_obj.esta_vigente():
        messages.error(request, 'El enlace no es válido o ya expiró.')
        return redirect('solicitar_reset')

    if request.method == 'POST':
        pw1 = request.POST.get('contrasena', '')
        pw2 = request.POST.get('contrasena2', '')

        if len(pw1) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'Inicio_Sesion-Registro/recuperar_confirmar.html', {'token': token})

        if pw1 != pw2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'Inicio_Sesion-Registro/recuperar_confirmar.html', {'token': token})

        # Actualizar contraseña según el rol
        nueva = make_password(pw1)
        if token_obj.rol == 'admin':
            Administrador.objects.filter(id_admin=token_obj.usuario_id).update(contrasena=nueva)
        elif token_obj.rol == 'medico':
            Medico.objects.filter(id_medico=token_obj.usuario_id).update(contrasena=nueva)
        else:
            Paciente.objects.filter(id_paciente=token_obj.usuario_id).update(contrasena=nueva)

        token_obj.usado = True
        token_obj.save()

        messages.success(request, '¡Contraseña actualizada! Ya puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'Inicio_Sesion-Registro/recuperar_confirmar.html', {'token': token})