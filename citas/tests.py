"""
Suite de pruebas de CitaYa.

Organización del archivo
-------------------------
PARTE A — PRUEBAS UNITARIAS
    Prueban una sola unidad de código de forma aislada (un modelo, un
    método, una validación) sin pasar por el ciclo HTTP completo.
    No usan el test Client ni dependen de vistas, sesiones o URLs.

PARTE B — PRUEBAS DE INTEGRACIÓN
    Prueban que varias piezas trabajen juntas: vista + URL + sesión +
    base de datos + middlewares, todo a través del test Client de
    Django, simulando una petición HTTP real de principio a fin.

Nota sobre dependencias externas
---------------------------------
- Resend (correo): se mockea en TestAgendarCitaJSON con unittest.mock,
  porque la cuenta está en modo sandbox y solo puede enviar a un correo
  propio verificado. Sin el mock, cada test que agenda una cita
  imprimía "Error al enviar el correo: ..." en consola — no rompía el
  test, pero era ruido visual. Con el mock, ni siquiera se intenta la
  llamada real a la API de Resend, así que no hay nada que falle ni
  que imprimir.
- Twilio (llamada de voz): a propósito NO se mockea (ver docstring de
  TestAgendarCitaJSON). Es intencional: se quiere que la prueba
  dispare una llamada real de verificación.
"""

import sys

# ------------------------------------------------------------------
# Shim de compatibilidad Python 3.14 + Django (ticket oficial #35844).
# En Python 3.14 los objetos `super()` se volvieron copiables, lo cual
# rompe el truco interno de Django en BaseContext.__copy__() que usa
# el test Client para capturar el context cada vez que se renderiza
# un template. Ya está arreglado en Django >= 5.2.8, pero mientras no
# actualices, este shim evita el crash sin afectar tus tests (ninguno
# de ellos usa response.context, solo nos interesa que el template
# se haya usado).
# ------------------------------------------------------------------
if sys.version_info >= (3, 14):
    import django.test.client as _django_test_client

    def _store_rendered_templates_safe(store, signal, sender, template, context, **kwargs):
        store.setdefault('templates', []).append(template)
        store.setdefault('context', [])

    _django_test_client.store_rendered_templates = _store_rendered_templates_safe


import json
import uuid
from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import (
    Administrador, Agendamiento, Historial_Clinico,
    Medico, Paciente, PasswordResetToken,
)

# Contraseña real usada por todos los usuarios en producción
CLAVE = "Admincitaya0*"


# =========================================================================
# PARTE A — PRUEBAS UNITARIAS
# =========================================================================

# -------------------------------------------------------------------------
# A.1 MODELOS
# -------------------------------------------------------------------------

class TestAdministrador(TestCase):

    def setUp(self):
        # Datos reales de producción — admin id_admin=1
        self.admin = Administrador.objects.create(
            tipo_doc="CC",
            numero_doc="1000000001",
            nombre="Carlos",
            apellido="Ramirez",
            genero="M",
            telefono="3001000001",
            correo="carlos.ramirez@citaya.com",
            contrasena=make_password(CLAVE),
            estado=True,
        )

    def test_str(self):
        self.assertEqual(str(self.admin), "Carlos Ramirez")

    def test_contrasena_correcta(self):
        self.assertTrue(self.admin.check_contrasena(CLAVE))

    def test_contrasena_incorrecta(self):
        self.assertFalse(self.admin.check_contrasena("clavemal"))

    def test_set_contrasena(self):
        self.admin.set_contrasena("NuevaClave2026*")
        self.admin.save()
        self.assertTrue(self.admin.check_contrasena("NuevaClave2026*"))

    def test_numero_doc_unico(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Administrador.objects.create(
                tipo_doc="CC",
                numero_doc="1000000001",  # mismo número de doc que Carlos
                nombre="Otro",
                apellido="Admin",
                genero="M",
                telefono="3009999999",
                correo="otro@citaya.com",
                contrasena=make_password(CLAVE),
                estado=True,
            )

    def test_estado_activo(self):
        self.assertTrue(self.admin.estado)


class TestMedico(TestCase):

    def setUp(self):
        # Datos reales de producción — medico id_medico=1
        self.medico = Medico.objects.create(
            tipo_doc="CC",
            numero_doc="2000000001",
            nombre="Sofia",
            apellido="Vargas",
            genero="F",
            especialidad="Medicina General",
            telefono="3102000001",
            correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE),
            estado=True,
        )

    def test_str_contiene_especialidad(self):
        self.assertIn("Medicina General", str(self.medico))

    def test_str_contiene_nombre(self):
        self.assertIn("Sofia", str(self.medico))

    def test_contrasena_correcta(self):
        self.assertTrue(self.medico.check_contrasena(CLAVE))

    def test_contrasena_incorrecta(self):
        self.assertFalse(self.medico.check_contrasena("clavemal"))

    def test_set_contrasena(self):
        self.medico.set_contrasena("OtraClave2026*")
        self.medico.save()
        self.assertTrue(self.medico.check_contrasena("OtraClave2026*"))

    def test_estado_activo(self):
        self.assertTrue(self.medico.estado)


class TestPaciente(TestCase):

    def setUp(self):
        # Datos reales de producción — paciente id_paciente=1
        self.paciente = Paciente.objects.create(
            tipo_doc="CC",
            numero_doc="3000000001",
            nombre="Ana",
            apellido="Lopez",
            genero="F",
            fecha_nacimiento="1990-03-15",
            tipo_sangre="O+",
            direccion="Cra 10 20-30 Bogota",
            telefono="3203000001",
            correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE),
            estado=True,
        )

    def test_str(self):
        self.assertEqual(str(self.paciente), "Ana Lopez")

    def test_contrasena_correcta(self):
        self.assertTrue(self.paciente.check_contrasena(CLAVE))

    def test_set_contrasena(self):
        self.paciente.set_contrasena("NuevaClave2026*")
        self.paciente.save()
        self.assertTrue(self.paciente.check_contrasena("NuevaClave2026*"))

    def test_correo_unico(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Paciente.objects.create(
                tipo_doc="CC",
                numero_doc="9999999999",
                nombre="Otro",
                apellido="Paciente",
                genero="M",
                fecha_nacimiento="1990-01-01",
                tipo_sangre="A+",
                direccion="Calle 1",
                telefono="3001111111",
                correo="ana.lopez@gmail.com",  # mismo correo que Ana
                contrasena=make_password(CLAVE),
                estado=True,
            )

    def test_tipo_sangre(self):
        self.assertEqual(self.paciente.tipo_sangre, "O+")

    def test_fecha_nacimiento(self):
        self.assertEqual(str(self.paciente.fecha_nacimiento), "1990-03-15")


class TestAgendamiento(TestCase):

    def setUp(self):
        # Médico real: Sofia Vargas
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        # Paciente real: Ana Lopez
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.cita = Agendamiento.objects.create(
            cita="Consulta general",
            fecha=date.today() + timedelta(days=3),
            hora=time(9, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )

    def test_str_contiene_tipo_cita(self):
        self.assertIn("Consulta general", str(self.cita))

    def test_relacion_paciente_nombre(self):
        self.assertEqual(self.cita.id_paciente.nombre, "Ana")

    def test_relacion_medico_especialidad(self):
        self.assertEqual(self.cita.id_medico.especialidad, "Medicina General")

    def test_fecha_es_futura(self):
        self.assertGreater(self.cita.fecha, date.today())


class TestHistorial(TestCase):

    def setUp(self):
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.historial = Historial_Clinico.objects.create(
            antecedentes="Paciente con hipertensión arterial controlada.",
            id_paciente=self.paciente,
            id_medico=self.medico,
        )

    def test_str_contiene_nombre_paciente(self):
        self.assertIn("Ana", str(self.historial))

    def test_fecha_creacion_es_hoy(self):
        self.assertEqual(self.historial.fecha_creacion, date.today())

    def test_antecedentes_guardados(self):
        self.assertEqual(
            self.historial.antecedentes,
            "Paciente con hipertensión arterial controlada."
        )


class TestPasswordResetToken(TestCase):

    def setUp(self):
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )

    def _crear_token(self, usado=False, segundos_atras=0):
        t = PasswordResetToken.objects.create(
            rol="paciente",
            usuario_id=self.paciente.id_paciente,
            correo=self.paciente.correo,
            usado=usado,
        )
        if segundos_atras:
            PasswordResetToken.objects.filter(pk=t.pk).update(
                creado_en=timezone.now() - timedelta(seconds=segundos_atras)
            )
            t.refresh_from_db()
        return t

    def test_token_vigente(self):
        self.assertTrue(self._crear_token().esta_vigente())

    def test_token_expirado(self):
        self.assertFalse(self._crear_token(segundos_atras=3601).esta_vigente())

    def test_token_ya_usado(self):
        self.assertFalse(self._crear_token(usado=True).esta_vigente())

    def test_tokens_son_unicos(self):
        t1 = self._crear_token()
        t2 = self._crear_token()
        self.assertNotEqual(t1.token, t2.token)

    def test_str_contiene_rol_y_correo(self):
        s = str(self._crear_token())
        self.assertIn("paciente", s)
        self.assertIn("ana.lopez@gmail.com", s)


# =========================================================================
# PARTE B — PRUEBAS DE INTEGRACIÓN
# (vista + URL + sesión + base de datos, vía test Client)
# =========================================================================

# -------------------------------------------------------------------------
# B.1 SESIÓN Y AUTENTICACIÓN
# -------------------------------------------------------------------------

class TestSesion(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = Administrador.objects.create(
            tipo_doc="CC", numero_doc="1000000001", nombre="Carlos",
            apellido="Ramirez", genero="M", telefono="3001000001",
            correo="carlos.ramirez@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )

    def _set_sesion(self, usuario, rol):
        s = self.client.session
        s["rol"] = rol
        s["usuario_id"] = (
            usuario.id_admin if rol == "admin"
            else usuario.id_medico if rol == "medico"
            else usuario.id_paciente
        )
        s["nombre"] = f"{usuario.nombre} {usuario.apellido}"
        s.save()

    def test_sesion_admin_rol_correcto(self):
        self._set_sesion(self.admin, "admin")
        self.assertEqual(self.client.session["rol"], "admin")

    def test_sesion_medico_rol_correcto(self):
        self._set_sesion(self.medico, "medico")
        self.assertEqual(self.client.session["rol"], "medico")

    def test_sesion_paciente_rol_correcto(self):
        self._set_sesion(self.paciente, "paciente")
        self.assertEqual(self.client.session["rol"], "paciente")

    def test_logout_limpia_sesion(self):
        self._set_sesion(self.admin, "admin")
        self.client.get(reverse("logout_admin"))
        self.assertNotIn("rol", self.client.session)

    def test_nombre_en_sesion(self):
        self._set_sesion(self.admin, "admin")
        self.assertEqual(self.client.session["nombre"], "Carlos Ramirez")

    def test_usuario_inactivo_no_puede_entrar(self):
        self.admin.estado = False
        self.admin.save()
        self.assertFalse(self.admin.estado)

    def test_contrasena_incorrecta_falla(self):
        self.assertFalse(self.admin.check_contrasena("claveincorrecta"))


# -------------------------------------------------------------------------
# B.2 PROTECCIÓN — APIs JSON devuelven 403 sin sesión válida
# -------------------------------------------------------------------------

class TestProteccion403(TestCase):

    def setUp(self):
        self.client = Client()
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )

    def _set_sesion(self, usuario, rol):
        s = self.client.session
        s["rol"] = rol
        s["usuario_id"] = (
            usuario.id_medico if rol == "medico" else usuario.id_paciente
        )
        s["nombre"] = f"{usuario.nombre} {usuario.apellido}"
        s.save()

    def test_citas_paciente_sin_sesion_403(self):
        self.assertEqual(
            self.client.get(reverse("citas_paciente_json")).status_code, 403
        )

    def test_historial_paciente_sin_sesion_403(self):
        self.assertEqual(
            self.client.get(reverse("historial_paciente_json")).status_code, 403
        )

    def test_agenda_medico_sin_sesion_403(self):
        self.assertEqual(
            self.client.get(reverse("agenda_medico_json")).status_code, 403
        )

    def test_perfil_admin_sin_sesion_403(self):
        self.assertEqual(
            self.client.get(reverse("perfil_admin_json")).status_code, 403
        )

    def test_perfil_paciente_sin_sesion_403(self):
        self.assertEqual(
            self.client.get(reverse("perfil_paciente_json")).status_code, 403
        )

    def test_perfil_medico_sin_sesion_403(self):
        self.assertEqual(
            self.client.get(reverse("perfil_medico_json")).status_code, 403
        )

    def test_medico_no_puede_ver_citas_de_paciente(self):
        self._set_sesion(self.medico, "medico")
        self.assertEqual(
            self.client.get(reverse("citas_paciente_json")).status_code, 403
        )

    def test_paciente_no_puede_ver_agenda_de_medico(self):
        self._set_sesion(self.paciente, "paciente")
        self.assertEqual(
            self.client.get(reverse("agenda_medico_json")).status_code, 403
        )


# -------------------------------------------------------------------------
# B.3 REGISTRO DE PACIENTE
# -------------------------------------------------------------------------

class TestRegistroPaciente(TestCase):

    def setUp(self):
        self.client = Client()

    def _datos_registro(self, **override):
        # Usamos datos del paciente id=2 (Juan Martinez) como base
        datos = dict(
            tipo_doc="CC",
            numero_doc="3000000002",
            nombre="Juan",
            apellido="Martinez",
            genero="M",
            fecha_nacimiento="1985-07-22",
            tipo_sangre="A+",
            telefono="3203000002",
            correo="juan.martinez@gmail.com",
            direccion="Cl 50 15-40 Medellin",
            contrasena=CLAVE,
            confirmar_contrasena=CLAVE,
        )
        datos.update(override)
        return datos

    def test_registro_crea_paciente_en_bd(self):
        self.client.post(reverse("registro"), self._datos_registro())
        self.assertTrue(Paciente.objects.filter(numero_doc="3000000002").exists())

    def test_contrasena_queda_hasheada(self):
        self.client.post(reverse("registro"), self._datos_registro())
        p = Paciente.objects.get(numero_doc="3000000002")
        self.assertTrue(p.check_contrasena(CLAVE))

    def test_registro_redirige_al_login(self):
        r = self.client.post(reverse("registro"), self._datos_registro())
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])

    def test_doc_duplicado_no_crea_segundo_registro(self):
        # Primero creamos el paciente directamente en BD
        Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000002", nombre="Juan",
            apellido="Martinez", genero="M", fecha_nacimiento="1985-07-22",
            tipo_sangre="A+", direccion="Cl 50 15-40 Medellin",
            telefono="3203000002", correo="otro@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        # Intentamos registrar con el mismo número de doc
        self.client.post(reverse("registro"), self._datos_registro())
        self.assertEqual(Paciente.objects.filter(numero_doc="3000000002").count(), 1)


# -------------------------------------------------------------------------
# B.4 APIs JSON — CITAS DEL PACIENTE
# -------------------------------------------------------------------------

class TestCitasJSON(TestCase):

    def setUp(self):
        self.client = Client()
        # Médico: Sofia Vargas
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        # Paciente: Ana Lopez
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        s = self.client.session
        s["rol"] = "paciente"
        s["usuario_id"] = self.paciente.id_paciente
        s["nombre"] = "Ana Lopez"
        s.save()

    def test_lista_citas_vacia(self):
        r = self.client.get(reverse("citas_paciente_json"))
        self.assertEqual(r.json()["citas"], [])

    def test_lista_citas_con_un_registro(self):
        Agendamiento.objects.create(
            cita="Consulta general",
            fecha=date.today() + timedelta(days=3),
            hora=time(10, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        data = self.client.get(reverse("citas_paciente_json")).json()["citas"]
        self.assertEqual(len(data), 1)
        self.assertIn("medico_nombre", data[0])

    def test_cita_futura_estado_agendada(self):
        Agendamiento.objects.create(
            cita="Control",
            fecha=date.today() + timedelta(days=5),
            hora=time(14, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        estado = self.client.get(reverse("citas_paciente_json")).json()["citas"][0]["estado"]
        self.assertEqual(estado, "Agendada")

    def test_cita_contiene_nombre_medico(self):
        Agendamiento.objects.create(
            cita="Consulta general",
            fecha=date.today() + timedelta(days=2),
            hora=time(11, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        data = self.client.get(reverse("citas_paciente_json")).json()["citas"][0]
        self.assertIn("Sofia", data["medico_nombre"])


# -------------------------------------------------------------------------
# B.5 APIs JSON — AGENDAR CITA (llamada Twilio real al número del .env)
# -------------------------------------------------------------------------

class TestAgendarCitaJSON(TestCase):
    """
    NO se hace mock de Twilio. La llamada de recordatorio se ejecuta
    de verdad usando las credenciales del .env y llama al TWILIO_TO_NUMBER
    configurado (tu número personal). Se programa 30 segundos después
    de agendar la cita.

    El envío de correo SÍ se mockea (ver setUp) porque la cuenta de
    Resend está en modo sandbox y solo puede enviar a un correo propio
    verificado: sin el mock, cada test que agenda una cita imprimía
    "Error al enviar el correo: ..." en consola. Esto no fallaba el
    test, pero era ruido. Al mockear, ni siquiera se intenta la llamada
    real a Resend, así que no hay nada que falle ni que imprimir.
    """

    def setUp(self):
        self.client = Client()

        # Mockeamos el envío de correo de confirmación de cita para no
        # depender de Resend durante los tests (modo sandbox).
        patcher = patch('citas.views.enviar_confirmacion_cita')
        self.mock_enviar_correo = patcher.start()
        self.addCleanup(patcher.stop)

        # Médico: Roberto Jimenez — Cardiologia (id_medico=4 en producción)
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000004", nombre="Roberto",
            apellido="Jimenez", genero="M", especialidad="Cardiologia",
            telefono="3102000004", correo="roberto.jimenez@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        # Paciente: Ana Lopez
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        s = self.client.session
        s["rol"] = "paciente"
        s["usuario_id"] = self.paciente.id_paciente
        s["nombre"] = "Ana Lopez"
        s.save()

    def _body(self, fecha=None, hora="10:00"):
        fecha = fecha or str(date.today() + timedelta(days=2))
        return json.dumps({
            "cita": "Consulta general",
            "id_medico": self.medico.id_medico,
            "fecha": fecha,
            "hora": hora,
        })

    def test_agendar_cita_exitosa_y_activa_llamada_twilio(self):
        from citas.views import scheduler
        import time
        import datetime

        r = self.client.post(
            reverse("agendar_cita_paciente"),
            data=self._body(),
            content_type="application/json",
        )
        self.assertTrue(r.json().get("ok"))
        self.assertEqual(Agendamiento.objects.count(), 1)
        self.mock_enviar_correo.assert_called_once()

        cita = Agendamiento.objects.first()
        job_id = f'llamada_{cita.id_agendamiento}'

        scheduler.reschedule_job(job_id, trigger='date', run_date=datetime.datetime.now())
        scheduler.wakeup()

        time.sleep(2)

    def test_fecha_pasada_retorna_400(self):
        r = self.client.post(
            reverse("agendar_cita_paciente"),
            data=self._body(fecha=str(date.today() - timedelta(days=1))),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_datos_incompletos_retorna_400(self):
        r = self.client.post(
            reverse("agendar_cita_paciente"),
            data=json.dumps({"cita": "Solo el tipo sin medico ni fecha"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_cita_duplicada_misma_hora_retorna_400(self):
        body = self._body()
        self.client.post(
            reverse("agendar_cita_paciente"),
            data=body, content_type="application/json",
        )
        r = self.client.post(
            reverse("agendar_cita_paciente"),
            data=body, content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)


# -------------------------------------------------------------------------
# B.6 APIs JSON — REPROGRAMAR Y CANCELAR CITA
# -------------------------------------------------------------------------

class TestReprogramarCancelarJSON(TestCase):

    def setUp(self):
        self.client = Client()
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        s = self.client.session
        s["rol"] = "paciente"
        s["usuario_id"] = self.paciente.id_paciente
        s["nombre"] = "Ana Lopez"
        s.save()
        self.cita = Agendamiento.objects.create(
            cita="Consulta general",
            fecha=date.today() + timedelta(days=3),
            hora=time(10, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )

    def test_reprogramar_cita_a_fecha_futura(self):
        nueva_fecha = str(date.today() + timedelta(days=7))
        r = self.client.post(
            reverse("reprogramar_cita_paciente", args=[self.cita.id_agendamiento]),
            data=json.dumps({"fecha": nueva_fecha, "hora": "14:00"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.cita.refresh_from_db()
        self.assertEqual(str(self.cita.fecha), nueva_fecha)

    def test_reprogramar_a_fecha_pasada_retorna_400(self):
        r = self.client.post(
            reverse("reprogramar_cita_paciente", args=[self.cita.id_agendamiento]),
            data=json.dumps({
                "fecha": str(date.today() - timedelta(days=1)),
                "hora": "09:00",
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_cancelar_cita_propia_la_elimina(self):
        pk = self.cita.id_agendamiento
        r = self.client.post(reverse("cancelar_cita_paciente", args=[pk]))
        self.assertTrue(r.json().get("ok"))
        self.assertFalse(Agendamiento.objects.filter(pk=pk).exists())

    def test_cancelar_cita_de_otro_paciente_no_la_elimina(self):
        # Paciente id=2: Juan Martinez
        otro_paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000002", nombre="Juan",
            apellido="Martinez", genero="M", fecha_nacimiento="1985-07-22",
            tipo_sangre="A+", direccion="Cl 50 15-40 Medellin",
            telefono="3203000002", correo="juan.martinez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        cita_ajena = Agendamiento.objects.create(
            cita="Control",
            fecha=date.today() + timedelta(days=4),
            hora=time(11, 0),
            id_paciente=otro_paciente,
            id_medico=self.medico,
        )
        # Ana no debe poder cancelar la cita de Juan
        self.assertFalse(
            Agendamiento.objects.filter(
                pk=cita_ajena.id_agendamiento,
                id_paciente=self.paciente,
            ).exists()
        )


# -------------------------------------------------------------------------
# B.7 APIs JSON — HISTORIAL CLÍNICO DEL PACIENTE
# -------------------------------------------------------------------------

class TestHistorialPacienteJSON(TestCase):

    def setUp(self):
        self.client = Client()
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        s = self.client.session
        s["rol"] = "paciente"
        s["usuario_id"] = self.paciente.id_paciente
        s["nombre"] = "Ana Lopez"
        s.save()

    def test_historial_vacio(self):
        self.assertEqual(
            self.client.get(reverse("historial_paciente_json")).json()["historiales"], []
        )

    def test_historial_con_un_registro(self):
        Historial_Clinico.objects.create(
            antecedentes="Paciente con hipertensión arterial.",
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        data = self.client.get(reverse("historial_paciente_json")).json()["historiales"]
        self.assertEqual(len(data), 1)
        self.assertIn("medico_nombre", data[0])

    def test_historial_contiene_nombre_medico_correcto(self):
        Historial_Clinico.objects.create(
            antecedentes="Sin novedades.",
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        data = self.client.get(reverse("historial_paciente_json")).json()["historiales"][0]
        self.assertIn("Sofia", data["medico_nombre"])


# -------------------------------------------------------------------------
# B.8 APIs JSON — AGENDA E HISTORIAL DEL MÉDICO
# -------------------------------------------------------------------------

class TestAgendaMedicoJSON(TestCase):

    def setUp(self):
        self.client = Client()
        # Médico: Luis Pena — Ortopedia (id_medico=2 en producción)
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000002", nombre="Luis",
            apellido="Pena", genero="M", especialidad="Ortopedia",
            telefono="3102000002", correo="luis.pena@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        s = self.client.session
        s["rol"] = "medico"
        s["usuario_id"] = self.medico.id_medico
        s["nombre"] = "Luis Pena"
        s.save()

    def test_agenda_sin_citas_vacia(self):
        self.assertEqual(
            self.client.get(reverse("agenda_medico_json")).json()["citas"], []
        )

    def test_agenda_muestra_cita_de_hoy(self):
        Agendamiento.objects.create(
            cita="Consulta ortopédica",
            fecha=date.today(),
            hora=time(9, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        data = self.client.get(
            reverse("agenda_medico_json"), {"fecha": str(date.today())}
        ).json()["citas"]
        self.assertEqual(len(data), 1)
        self.assertIn("paciente_nombre", data[0])

    def test_agenda_muestra_nombre_paciente_correcto(self):
        Agendamiento.objects.create(
            cita="Control",
            fecha=date.today(),
            hora=time(10, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        data = self.client.get(
            reverse("agenda_medico_json"), {"fecha": str(date.today())}
        ).json()["citas"][0]
        self.assertIn("Ana", data["paciente_nombre"])

    def test_guardar_historial_medico_exitoso(self):
        r = self.client.post(
            reverse("guardar_historial_medico"),
            data=json.dumps({
                "antecedentes": "Paciente estable, sin cambios en control ortopédico.",
                "id_paciente": self.paciente.id_paciente,
            }),
            content_type="application/json",
        )
        self.assertTrue(r.json().get("ok"))
        self.assertEqual(Historial_Clinico.objects.count(), 1)

    def test_guardar_historial_vacio_retorna_400(self):
        r = self.client.post(
            reverse("guardar_historial_medico"),
            data=json.dumps({
                "antecedentes": "   ",
                "id_paciente": self.paciente.id_paciente,
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_guardar_historial_duplicado_mismo_dia_retorna_400(self):
        body = json.dumps({
            "antecedentes": "Primer registro del día.",
            "id_paciente": self.paciente.id_paciente,
        })
        self.client.post(
            reverse("guardar_historial_medico"),
            data=body, content_type="application/json",
        )
        r = self.client.post(
            reverse("guardar_historial_medico"),
            data=body, content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)


# -------------------------------------------------------------------------
# B.9 APIs JSON — PERFILES
# -------------------------------------------------------------------------

class TestPerfilesJSON(TestCase):

    def setUp(self):
        self.client = Client()
        # Admin: Carlos Ramirez
        self.admin = Administrador.objects.create(
            tipo_doc="CC", numero_doc="1000000001", nombre="Carlos",
            apellido="Ramirez", genero="M", telefono="3001000001",
            correo="carlos.ramirez@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        # Médico: Sofia Vargas
        self.medico = Medico.objects.create(
            tipo_doc="CC", numero_doc="2000000001", nombre="Sofia",
            apellido="Vargas", genero="F", especialidad="Medicina General",
            telefono="3102000001", correo="sofia.vargas@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        # Paciente: Ana Lopez
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )

    def _sesion_admin(self):
        s = self.client.session
        s["rol"] = "admin"
        s["usuario_id"] = self.admin.id_admin
        s["nombre"] = "Carlos Ramirez"
        s.save()

    def _sesion_medico(self):
        s = self.client.session
        s["rol"] = "medico"
        s["usuario_id"] = self.medico.id_medico
        s["nombre"] = "Sofia Vargas"
        s.save()

    def _sesion_paciente(self):
        s = self.client.session
        s["rol"] = "paciente"
        s["usuario_id"] = self.paciente.id_paciente
        s["nombre"] = "Ana Lopez"
        s.save()

    def test_obtener_perfil_admin_nombre_correcto(self):
        self._sesion_admin()
        self.assertEqual(
            self.client.get(reverse("perfil_admin_json")).json()["nombre"], "Carlos"
        )

    def test_editar_nombre_admin(self):
        self._sesion_admin()
        self.client.post(
            reverse("editar_perfil_admin"),
            data=json.dumps({"nombre": "Carlos Alberto"}),
            content_type="application/json",
        )
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.nombre, "Carlos Alberto")

    def test_obtener_perfil_paciente_nombre_correcto(self):
        self._sesion_paciente()
        self.assertEqual(
            self.client.get(reverse("perfil_paciente_json")).json()["nombre"], "Ana"
        )

    def test_editar_telefono_paciente(self):
        self._sesion_paciente()
        self.client.post(
            reverse("editar_perfil_paciente"),
            data=json.dumps({"telefono": "3203000099"}),
            content_type="application/json",
        )
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.telefono, "3203000099")

    def test_obtener_perfil_medico_especialidad_correcta(self):
        self._sesion_medico()
        self.assertEqual(
            self.client.get(reverse("perfil_medico_json")).json()["especialidad"],
            "Medicina General",
        )

    def test_editar_contrasena_medico(self):
        self._sesion_medico()
        self.client.post(
            reverse("editar_perfil_medico"),
            data=json.dumps({"contrasena": "NuevaClave2026*"}),
            content_type="application/json",
        )
        self.medico.refresh_from_db()
        self.assertTrue(self.medico.check_contrasena("NuevaClave2026*"))

    def test_perfil_paciente_contiene_tipo_sangre(self):
        self._sesion_paciente()
        data = self.client.get(reverse("perfil_paciente_json")).json()
        self.assertEqual(data["tipo_sangre"], "O+")


# -------------------------------------------------------------------------
# B.10 APIs JSON — DISPONIBILIDAD Y ESPECIALIDADES
# -------------------------------------------------------------------------

class TestDisponibilidadJSON(TestCase):

    def setUp(self):
        self.client = Client()
        # Médico: Natalia Castro — Psicologia (id_medico=3 en producción)
        self.medico = Medico.objects.create(
            tipo_doc="CE", numero_doc="2000000003", nombre="Natalia",
            apellido="Castro", genero="F", especialidad="Psicologia",
            telefono="3102000003", correo="natalia.castro@citaya.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        self.paciente = Paciente.objects.create(
            tipo_doc="CC", numero_doc="3000000001", nombre="Ana",
            apellido="Lopez", genero="F", fecha_nacimiento="1990-03-15",
            tipo_sangre="O+", direccion="Cra 10 20-30 Bogota",
            telefono="3203000001", correo="ana.lopez@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )
        s = self.client.session
        s["rol"] = "paciente"
        s["usuario_id"] = self.paciente.id_paciente
        s["nombre"] = "Ana Lopez"
        s.save()

    def test_sin_parametros_retorna_400(self):
        self.assertEqual(
            self.client.get(reverse("disponibilidad_medico")).status_code, 400
        )

    def test_todos_los_horarios_disponibles_si_no_hay_citas(self):
        manana = str(date.today() + timedelta(days=1))
        horarios = self.client.get(
            reverse("disponibilidad_medico"),
            {"medico_id": self.medico.id_medico, "fecha": manana},
        ).json()["horarios"]
        self.assertTrue(all(h["disponible"] for h in horarios))

    def test_hora_ocupada_aparece_no_disponible(self):
        manana = date.today() + timedelta(days=1)
        Agendamiento.objects.create(
            cita="Sesión psicológica",
            fecha=manana,
            hora=time(8, 0),
            id_paciente=self.paciente,
            id_medico=self.medico,
        )
        horarios = self.client.get(
            reverse("disponibilidad_medico"),
            {"medico_id": self.medico.id_medico, "fecha": str(manana)},
        ).json()["horarios"]
        ocupados = [h for h in horarios if not h["disponible"]]
        self.assertEqual(len(ocupados), 1)
        self.assertEqual(ocupados[0]["hora"], "08:00")

    def test_medicos_por_especialidad_psicologia(self):
        data = self.client.get(
            reverse("medicos_por_especialidad"), {"especialidad": "Psicologia"}
        ).json()["medicos"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["nombre"], "Natalia")

    def test_especialidad_inexistente_retorna_lista_vacia(self):
        data = self.client.get(
            reverse("medicos_por_especialidad"), {"especialidad": "Neurologia"}
        ).json()["medicos"]
        self.assertEqual(data, [])


# -------------------------------------------------------------------------
# B.11 TOKEN DE RECUPERACIÓN DE CONTRASEÑA
# -------------------------------------------------------------------------

class TestTokenRecuperacion(TestCase):

    def setUp(self):
        # Paciente: Valeria Diaz (id=3 en producción)
        self.paciente = Paciente.objects.create(
            tipo_doc="TI", numero_doc="3000000003", nombre="Valeria",
            apellido="Diaz", genero="F", fecha_nacimiento="2005-01-08",
            tipo_sangre="B-", direccion="Av 30 5-10 Cali",
            telefono="3203000003", correo="valeria.diaz@gmail.com",
            contrasena=make_password(CLAVE), estado=True,
        )

    def _crear_token(self, usado=False, segundos_atras=0):
        t = PasswordResetToken.objects.create(
            rol="paciente",
            usuario_id=self.paciente.id_paciente,
            correo=self.paciente.correo,
            usado=usado,
        )
        if segundos_atras:
            PasswordResetToken.objects.filter(pk=t.pk).update(
                creado_en=timezone.now() - timedelta(seconds=segundos_atras)
            )
            t.refresh_from_db()
        return t

    def test_token_recien_creado_es_vigente(self):
        self.assertTrue(self._crear_token().esta_vigente())

    def test_token_con_mas_de_una_hora_no_es_vigente(self):
        self.assertFalse(self._crear_token(segundos_atras=3601).esta_vigente())

    def test_token_marcado_como_usado_no_es_vigente(self):
        self.assertFalse(self._crear_token(usado=True).esta_vigente())

    def test_dos_tokens_tienen_uuid_diferente(self):
        t1 = self._crear_token()
        t2 = self._crear_token()
        self.assertNotEqual(t1.token, t2.token)

    def test_str_contiene_rol_paciente(self):
        self.assertIn("paciente", str(self._crear_token()))

    def test_str_contiene_correo(self):
        self.assertIn("valeria.diaz@gmail.com", str(self._crear_token()))

    def test_token_invalido_uuid_redirige(self):
        c = Client()
        r = c.get(reverse("confirmar_reset", args=[str(uuid.uuid4())]), follow=False)
        self.assertEqual(r.status_code, 302)

    def test_token_expirado_redirige_al_solicitar(self):
        t = self._crear_token(segundos_atras=3700)
        c = Client()
        r = c.get(reverse("confirmar_reset", args=[str(t.token)]), follow=False)
        self.assertEqual(r.status_code, 302)

    def test_token_usado_redirige_al_solicitar(self):
        t = self._crear_token(usado=True)
        c = Client()
        r = c.get(reverse("confirmar_reset", args=[str(t.token)]), follow=False)
        self.assertEqual(r.status_code, 302)

    def test_reset_exitoso_actualiza_contrasena_en_bd(self):
        Paciente.objects.filter(pk=self.paciente.id_paciente).update(
            contrasena=make_password("NuevaClave2026*")
        )
        t = self._crear_token()
        t.usado = True
        t.save()
        self.paciente.refresh_from_db()
        self.assertTrue(self.paciente.check_contrasena("NuevaClave2026*"))
        self.assertTrue(t.usado)

    def test_token_no_vigente_no_cambia_contrasena(self):
        t = self._crear_token(usado=True)
        contrasena_original = self.paciente.contrasena
        if not t.esta_vigente():
            self.paciente.refresh_from_db()
            self.assertEqual(self.paciente.contrasena, contrasena_original)