import json
from datetime import date
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.contrib.auth.mixins import AccessMixin
from datetime import datetime, timedelta
from django.db.models import Q

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

# ── SCHEDULER ─────────────────────────────────────────────────────────────
scheduler = BackgroundScheduler()
scheduler.start()

def llamada_twilio_tarea(nombre, especialidad, fecha, hora):
    account_sid = ''
    auth_token  = ''
    client = Client(account_sid, auth_token)
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
            to='+573146867513',
            from_='+18128979180'
        )
        print(f"📞 Llamada enviada a {nombre}")
    except Exception as e:
        print(f"❌ Error en Twilio: {e}")


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

        user_admin = Administrador.objects.filter(numero_doc=numero_doc, contrasena=password).first()
        if user_admin:
            request.session['usuario_id'] = user_admin.id_admin
            request.session['rol']        = 'admin'
            request.session['nombre']     = f"{user_admin.nombre} {user_admin.apellido}"
            return redirect('dashboard_admin')

        user_medico = Medico.objects.filter(numero_doc=numero_doc, contrasena=password).first()
        if user_medico:
            request.session['usuario_id'] = user_medico.id_medico
            request.session['rol']        = 'medico'
            request.session['nombre']     = f"{user_medico.nombre} {user_medico.apellido}"
            return redirect('dashboard_medico')

        user_paciente = Paciente.objects.filter(numero_doc=numero_doc, contrasena=password).first()
        if user_paciente:
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
                direccion=direccion, contrasena=contrasena, estado=True
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
        'total_medicos':    Medico.objects.count(),
        'total_pacientes':  Paciente.objects.count(),
        'total_citas':      Agendamiento.objects.count(),
        'total_historiales':Historial_Clinico.objects.count(),
        'nombre':           request.session.get('nombre'),
    }
    return render(request, 'dashboard/administrador/inicio_admin.html', context)


@never_cache
def dashboard_medico(request):
    if request.session.get('rol') != 'medico':
        return redirect('login')

    medico_id    = request.session.get('usuario_id')
    hoy          = date.today()
    todas_citas  = Agendamiento.objects.filter(id_medico=medico_id).select_related('id_paciente')
    proximas_citas = todas_citas.filter(fecha__gte=hoy).order_by('fecha', 'hora')[:5]
    historiales  = Historial_Clinico.objects.filter(id_medico=medico_id).select_related('id_paciente').order_by('-fecha_creacion')[:5]
    pacientes_ids = todas_citas.values_list('id_paciente', flat=True).distinct()
    pacientes    = Paciente.objects.filter(id_paciente__in=pacientes_ids)

    context = {
        'nombre':           request.session.get('nombre'),
        'total_citas':      todas_citas.count(),
        'citas_proximas':   proximas_citas.count(),
        'total_historiales':Historial_Clinico.objects.filter(id_medico=medico_id).count(),
        'total_pacientes':  len(set(pacientes_ids)),
        'proximas_citas':   proximas_citas,
        'historiales':      historiales,
        'pacientes':        pacientes,
    }
    return render(request, 'dashboard/medico/inicio_medico.html', context)


@never_cache
def dashboard_paciente(request):
    if request.session.get('rol') != 'paciente':
        return redirect('login')

    paciente_id = request.session.get('usuario_id')
    hoy  = date.today()
    ahora = datetime.now()
    todas_citas = Agendamiento.objects.filter(id_paciente=paciente_id).select_related('id_medico')

    proximas_citas = todas_citas.filter(
        Q(fecha__gt=hoy) | Q(fecha=hoy, hora__gt=ahora.time())
    ).order_by('fecha', 'hora')[:5]

    historiales = Historial_Clinico.objects.filter(
        id_paciente=paciente_id
    ).select_related('id_medico').order_by('-fecha_creacion')[:5]

    medicos_ids = todas_citas.values_list('id_medico', flat=True).distinct()
    medicos_disponibles = Medico.objects.filter(estado=True).order_by('especialidad', 'nombre')

    context = {
        'nombre':             request.session.get('nombre'),
        'total_citas':        todas_citas.count(),
        'citas_proximas':     todas_citas.filter(
            Q(fecha__gt=hoy) | Q(fecha=hoy, hora__gt=ahora.time())
        ).count(),
        'total_historiales':  Historial_Clinico.objects.filter(id_paciente=paciente_id).count(),
        'total_medicos':      len(set(medicos_ids)),
        'proximas_citas':     proximas_citas,
        'historiales':        historiales,
        'medicos_disponibles':medicos_disponibles,
    }
    return render(request, 'dashboard/paciente/inicio_paciente.html', context)


# =========================================================================
# APIs DE PACIENTE
# =========================================================================

def citas_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    paciente_id = request.session.get('usuario_id')
    ahora = datetime.now()
    citas = Agendamiento.objects.filter(id_paciente=paciente_id).select_related('id_medico').order_by('-fecha', '-hora')

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
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)

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

        paciente  = get_object_or_404(Paciente, pk=paciente_id)
        medico    = get_object_or_404(Medico, pk=medico_id)
        nueva_cita = Agendamiento.objects.create(
            cita=cita_tipo, fecha=fecha_str, hora=hora_str,
            id_paciente=paciente, id_medico=medico,
        )

        try:
            enviar_confirmacion_cita(paciente, nueva_cita)
        except Exception as e:
            print(f"Error de correo: {e}")

        momento_llamada  = datetime.now() + timedelta(seconds=30)
        fecha_para_voz   = fecha_cita.strftime('%d de %B')
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
        data           = json.loads(request.body)
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
    inicio = datetime.strptime("06:00", "%H:%M")
    fin    = datetime.strptime("18:00", "%H:%M")

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
        'nombre': admin.nombre, 'apellido': admin.apellido,
        'tipo_doc': admin.tipo_doc, 'numero_doc': admin.numero_doc,
        'genero': admin.genero, 'telefono': admin.telefono,
        'correo': admin.correo, 'estado': admin.estado,
    })


@require_POST
def editar_perfil_admin(request):
    if request.session.get('rol') != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    admin = get_object_or_404(Administrador, pk=request.session['usuario_id'])
    try:
        data = json.loads(request.body)
        admin.nombre    = data.get('nombre',   admin.nombre)
        admin.apellido  = data.get('apellido', admin.apellido)
        admin.genero    = data.get('genero',   admin.genero)
        admin.telefono  = data.get('telefono', admin.telefono)
        admin.correo    = data.get('correo',   admin.correo)
        pw = data.get('contrasena', '').strip()
        if pw:
            admin.contrasena = pw
        admin.save()
        request.session['nombre'] = f"{admin.nombre} {admin.apellido}"
        return JsonResponse({'ok': True, 'nombre': request.session['nombre']})
    except:
        return JsonResponse({'error': 'Error al procesar datos'}, status=400)


def perfil_paciente_json(request):
    if request.session.get('rol') != 'paciente':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    paciente = get_object_or_404(Paciente, pk=request.session['usuario_id'])
    return JsonResponse({
        'nombre': paciente.nombre, 'apellido': paciente.apellido,
        'tipo_doc': paciente.tipo_doc, 'numero_doc': paciente.numero_doc,
        'genero': paciente.genero, 'fecha_nacimiento': str(paciente.fecha_nacimiento),
        'tipo_sangre': paciente.tipo_sangre, 'direccion': paciente.direccion,
        'telefono': paciente.telefono, 'correo': paciente.correo,
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
        pw = data.get('contrasena', '').strip()
        if pw:
            paciente.contrasena = pw
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
        'nombre': paciente.nombre, 'apellido': paciente.apellido,
        'tipo_doc': paciente.tipo_doc, 'numero_doc': paciente.numero_doc,
        'genero': paciente.genero, 'fecha_nacimiento': str(paciente.fecha_nacimiento),
        'tipo_sangre': paciente.tipo_sangre, 'telefono': paciente.telefono,
        'correo': paciente.correo, 'direccion': paciente.direccion,
        'estado': paciente.estado,
    })


def historial_paciente_medico_json(request, pk):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    medico_id = request.session.get('usuario_id')
    paciente  = get_object_or_404(Paciente, pk=pk)
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
        hoy = date.today()

        if Historial_Clinico.objects.filter(id_medico=medico, id_paciente=paciente, fecha_creacion=hoy).exists():
            return JsonResponse({'error': 'Ya registraste un historial para este paciente hoy.'}, status=400)

        historial = Historial_Clinico.objects.create(
            antecedentes=antecedentes, id_paciente=paciente, id_medico=medico,
        )
        return JsonResponse({
            'ok': True,
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
        'nombre': medico.nombre, 'apellido': medico.apellido,
        'tipo_doc': medico.tipo_doc, 'numero_doc': medico.numero_doc,
        'genero': medico.genero, 'especialidad': medico.especialidad,
        'telefono': medico.telefono, 'correo': medico.correo,
        'estado': medico.estado,
    })


@require_POST
def editar_perfil_medico(request):
    if request.session.get('rol') != 'medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    medico = get_object_or_404(Medico, pk=request.session['usuario_id'])
    try:
        data = json.loads(request.body)
        medico.nombre   = data.get('nombre',   medico.nombre)
        medico.apellido = data.get('apellido', medico.apellido)
        medico.telefono = data.get('telefono', medico.telefono)
        medico.correo   = data.get('correo',   medico.correo)
        pw = data.get('contrasena', '').strip()
        if pw:
            medico.contrasena = pw
        medico.save()
        request.session['nombre'] = f"{medico.nombre} {medico.apellido}"
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =========================================================================
# HELPER: aplica filtro multicriterio con Q objects
# =========================================================================

def _aplicar_filtro(queryset, q_term, *campos):
    """
    Filtra queryset con OR entre todos los campos dados y el término q_term.
    Retorna (queryset_filtrado, q_term) — q_term puede ser '' si no hubo búsqueda.
    """
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
        qs = super().get_queryset()
        q  = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(apellido__icontains=q) |
                Q(numero_doc__icontains=q) |
                Q(correo__icontains=q) |
                Q(telefono__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


def reporte_administradores(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    q      = request.GET.get('q', '').strip()
    tipo   = request.GET.get('tipo', 'pdf')  # 'pdf' o 'excel'
    qs     = Administrador.objects.all()
    qs, _  = _aplicar_filtro(qs, q, 'nombre', 'apellido', 'numero_doc', 'correo', 'telefono')

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
    fields        = '__all__'
    template_name = 'administradores/crear_administrador.html'
    success_url   = reverse_lazy('ver_administrador')

class AdminUpdateView(AdminRequiredMixin, UpdateView):
    model         = Administrador
    fields        = '__all__'
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
        qs = super().get_queryset()
        q  = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(apellido__icontains=q) |
                Q(numero_doc__icontains=q) |
                Q(correo__icontains=q) |
                Q(especialidad__icontains=q) |
                Q(telefono__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


def reporte_medicos(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    q     = request.GET.get('q', '').strip()
    tipo  = request.GET.get('tipo', 'pdf')
    qs    = Medico.objects.all()
    qs, _ = _aplicar_filtro(qs, q, 'nombre', 'apellido', 'numero_doc', 'correo', 'especialidad', 'telefono')

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
    fields        = '__all__'
    template_name = 'medicos/crear_medicos.html'
    success_url   = reverse_lazy('ver_medicos')

class MedicoUpdateView(AdminRequiredMixin, UpdateView):
    model         = Medico
    fields        = '__all__'
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
        qs = super().get_queryset()
        q  = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(apellido__icontains=q) |
                Q(numero_doc__icontains=q) |
                Q(correo__icontains=q) |
                Q(telefono__icontains=q) |
                Q(tipo_sangre__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


def reporte_pacientes(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    q     = request.GET.get('q', '').strip()
    tipo  = request.GET.get('tipo', 'pdf')
    qs    = Paciente.objects.all()
    qs, _ = _aplicar_filtro(qs, q, 'nombre', 'apellido', 'numero_doc', 'correo', 'telefono', 'tipo_sangre')

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
    fields        = '__all__'
    template_name = 'pacientes/crear_pacientes.html'
    success_url   = reverse_lazy('ver_pacientes')

class PacienteUpdateView(AdminRequiredMixin, UpdateView):
    model         = Paciente
    fields        = '__all__'
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
        qs = super().get_queryset().select_related('id_paciente', 'id_medico')
        q  = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(cita__icontains=q) |
                Q(id_paciente__nombre__icontains=q) |
                Q(id_paciente__apellido__icontains=q) |
                Q(id_paciente__numero_doc__icontains=q) |
                Q(id_medico__nombre__icontains=q) |
                Q(id_medico__apellido__icontains=q) |
                Q(id_medico__especialidad__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


def reporte_agendamientos(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    q    = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'pdf')
    qs   = Agendamiento.objects.select_related('id_paciente', 'id_medico').all()

    if q:
        qs = qs.filter(
            Q(cita__icontains=q) |
            Q(id_paciente__nombre__icontains=q) |
            Q(id_paciente__apellido__icontains=q) |
            Q(id_paciente__numero_doc__icontains=q) |
            Q(id_medico__nombre__icontains=q) |
            Q(id_medico__apellido__icontains=q)
        )

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
    fields        = '__all__'
    template_name = 'agendamientos/crear_agendamientos.html'
    success_url   = reverse_lazy('ver_agendamientos')

class AgendamientoUpdateView(AdminRequiredMixin, UpdateView):
    model         = Agendamiento
    fields        = '__all__'
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
        qs = super().get_queryset().select_related('id_paciente', 'id_medico')
        q  = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(antecedentes__icontains=q) |
                Q(id_paciente__nombre__icontains=q) |
                Q(id_paciente__apellido__icontains=q) |
                Q(id_paciente__numero_doc__icontains=q) |
                Q(id_medico__nombre__icontains=q) |
                Q(id_medico__apellido__icontains=q) |
                Q(id_medico__especialidad__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


def reporte_historiales(request):
    if request.session.get('rol') != 'admin':
        return redirect('login')

    q    = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'pdf')
    qs   = Historial_Clinico.objects.select_related('id_paciente', 'id_medico').all()

    if q:
        qs = qs.filter(
            Q(antecedentes__icontains=q) |
            Q(id_paciente__nombre__icontains=q) |
            Q(id_paciente__apellido__icontains=q) |
            Q(id_paciente__numero_doc__icontains=q) |
            Q(id_medico__nombre__icontains=q) |
            Q(id_medico__apellido__icontains=q)
        )

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
    fields        = '__all__'
    template_name = 'historial_clinico/crear_historiales.html'
    success_url   = reverse_lazy('ver_historiales')

class HistorialUpdateView(AdminRequiredMixin, UpdateView):
    model         = Historial_Clinico
    fields        = '__all__'
    template_name = 'historial_clinico/editar_historiales.html'
    success_url   = reverse_lazy('ver_historiales')

class HistorialDeleteView(AdminRequiredMixin, DeleteView):
    model         = Historial_Clinico
    template_name = 'historial_clinico/eliminar_historiales.html'
    success_url   = reverse_lazy('ver_historiales')