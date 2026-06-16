from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
# Importación de todos tus modelos del proyecto Cita Ya
from citas.models import Administrador, Medico, Paciente, Agendamiento, Historial_Clinico 

class Command(BaseCommand):
    help = 'Automatización total: Carga y encriptación de semillas con PBKDF2 para Cita Ya'

    def handle(self, *args, **kwargs):
        # =====================================================================
        # 1. ADMINISTRADORES
        # =====================================================================
        self.stdout.write('Cargando administradores...')
        admins_data = [
            {'tipo_doc': 'CC', 'numero_doc': '1000000001', 'nombre': 'Carlos', 'apellido': 'Ramirez', 'genero': 'M', 'telefono': '3001000001', 'correo': 'carlos.ramirez@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '1000000002', 'nombre': 'Laura', 'apellido': 'Gomez', 'genero': 'F', 'telefono': '3001000002', 'correo': 'laura.gomez@citaya.com', 'estado': 1},
            {'tipo_doc': 'CE', 'numero_doc': '1000000003', 'nombre': 'Andres', 'apellido': 'Morales', 'genero': 'M', 'telefono': '3001000003', 'correo': 'andres.morales@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '1000000004', 'nombre': 'Valentina', 'apellido': 'Torres', 'genero': 'F', 'telefono': '3001000004', 'correo': 'valentina.torres@citaya.com', 'estado': 0},
            {'tipo_doc': 'CC', 'numero_doc': '1000000005', 'nombre': 'Miguel', 'apellido': 'Herrera', 'genero': 'M', 'telefono': '3001000005', 'correo': 'miguel.herrera@citaya.com', 'estado': 1},
        ]
        
        for data in admins_data:
            if not Administrador.objects.filter(numero_doc=data['numero_doc']).exists():
                data['contrasena'] = make_password('Admincitaya0*')
                Administrador.objects.create(**data)

        # =====================================================================
        # 2. MEDICOS
        # =====================================================================
        self.stdout.write('Cargando médicos...')
        medicos_data = [
            {'tipo_doc': 'CC', 'numero_doc': '2000000001', 'nombre': 'Sofia', 'apellido': 'Vargas', 'genero': 'F', 'especialidad': 'Medicina General', 'telefono': '3102000001', 'correo': 'sofia.vargas@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000002', 'nombre': 'Luis', 'apellido': 'Pena', 'genero': 'M', 'especialidad': 'Ortopedia', 'telefono': '3102000002', 'correo': 'luis.pena@citaya.com', 'estado': 1},
            {'tipo_doc': 'CE', 'numero_doc': '2000000003', 'nombre': 'Natalia', 'apellido': 'Castro', 'genero': 'F', 'especialidad': 'Psicologia', 'telefono': '3102000003', 'correo': 'natalia.castro@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000004', 'nombre': 'Roberto', 'apellido': 'Jimenez', 'genero': 'M', 'especialidad': 'Cardiologia', 'telefono': '3102000004', 'correo': 'roberto.jimenez@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000005', 'nombre': 'Camila', 'apellido': 'Ruiz', 'genero': 'F', 'especialidad': 'Pediatria', 'telefono': '3102000005', 'correo': 'camila.ruiz@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000006', 'nombre': 'Diego', 'apellido': 'Salinas', 'genero': 'M', 'especialidad': 'Dermatologia', 'telefono': '3102000006', 'correo': 'diego.salinas@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000007', 'nombre': 'Paola', 'apellido': 'Mendoza', 'genero': 'F', 'especialidad': 'Medicina General', 'telefono': '3102000007', 'correo': 'paola.mendoza@citaya.com', 'estado': 0},
            {'tipo_doc': 'CE', 'numero_doc': '2000000008', 'nombre': 'Felipe', 'apellido': 'Rojas', 'genero': 'M', 'especialidad': 'Ortopedia', 'telefono': '3102000008', 'correo': 'felipe.rojas@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000009', 'nombre': 'Isabel', 'apellido': 'Navarro', 'genero': 'F', 'especialidad': 'Psicologia', 'telefono': '3102000009', 'correo': 'isabel.navarro@citaya.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '2000000010', 'nombre': 'Julian', 'apellido': 'Rios', 'genero': 'M', 'especialidad': 'Cardiologia', 'telefono': '3102000010', 'correo': 'julian.rios@citaya.com', 'estado': 1},
        ]
        
        for data in medicos_data:
            if not Medico.objects.filter(numero_doc=data['numero_doc']).exists():
                data['contrasena'] = make_password('Admincitaya0*')
                Medico.objects.create(**data)

        # =====================================================================
        # 3. PACIENTES
        # =====================================================================
        self.stdout.write('Cargando pacientes...')
        pacientes_data = [
            {'tipo_doc': 'CC', 'numero_doc': '3000000001', 'nombre': 'Ana', 'apellido': 'Lopez', 'genero': 'F', 'fecha_nacimiento': '1990-03-15', 'tipo_sangre': 'O+', 'direccion': 'Cra 10 20-30 Bogota', 'telefono': '3203000001', 'correo': 'ana.lopez@gmail.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '3000000002', 'nombre': 'Juan', 'apellido': 'Martinez', 'genero': 'M', 'fecha_nacimiento': '1985-07-22', 'tipo_sangre': 'A+', 'direccion': 'Cl 50 15-40 Medellin', 'telefono': '3203000002', 'correo': 'juan.martinez@gmail.com', 'estado': 1},
            {'tipo_doc': 'TI', 'numero_doc': '3000000003', 'nombre': 'Valeria', 'apellido': 'Diaz', 'genero': 'F', 'fecha_nacimiento': '2005-01-08', 'tipo_sangre': 'B-', 'direccion': 'Av 30 5-10 Cali', 'telefono': '3203000003', 'correo': 'valeria.diaz@gmail.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '3000000004', 'nombre': 'Pedro', 'apellido': 'Gutierrez', 'genero': 'M', 'fecha_nacimiento': '1978-11-03', 'tipo_sangre': 'AB+', 'direccion': 'Cl 12 8-22 Barranquilla', 'telefono': '3203000004', 'correo': 'pedro.gutierrez@gmail.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '3000000005', 'nombre': 'Mariana', 'apellido': 'Herrera', 'genero': 'F', 'fecha_nacimiento': '1995-05-19', 'tipo_sangre': 'O-', 'direccion': 'Cra 7 100-50 Bogota', 'telefono': '3203000005', 'correo': 'mariana.herrera@gmail.com', 'estado': 1},
            {'tipo_doc': 'CE', 'numero_doc': '3000000006', 'nombre': 'Sebastian', 'apellido': 'Mora', 'genero': 'M', 'fecha_nacimiento': '1988-09-30', 'tipo_sangre': 'A-', 'direccion': 'Cl 80 20-15 Bogota', 'telefono': '3203000006', 'correo': 'sebastian.mora@gmail.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '3000000007', 'nombre': 'Luciana', 'apellido': 'Vega', 'genero': 'F', 'fecha_nacimiento': '2000-12-01', 'tipo_sangre': 'B+', 'direccion': 'Cra 15 30-60 Pereira', 'telefono': '3203000007', 'correo': 'luciana.vega@gmail.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '3000000008', 'nombre': 'Tomas', 'apellido': 'Pardo', 'genero': 'M', 'fecha_nacimiento': '1970-04-25', 'tipo_sangre': 'AB-', 'direccion': 'Cl 45 10-5 Manizales', 'telefono': '3203000008', 'correo': 'tomas.pardo@gmail.com', 'estado': 0},
            {'tipo_doc': 'TI', 'numero_doc': '3000000009', 'nombre': 'Isabela', 'apellido': 'Cano', 'genero': 'F', 'fecha_nacimiento': '2008-06-14', 'tipo_sangre': 'O+', 'direccion': 'Av 68 50-30 Bogota', 'telefono': '3203000009', 'correo': 'isabela.cano@gmail.com', 'estado': 1},
            {'tipo_doc': 'CC', 'numero_doc': '3000000010', 'nombre': 'Mateo', 'apellido': 'Salazar', 'genero': 'M', 'fecha_nacimiento': '1993-08-07', 'tipo_sangre': 'A+', 'direccion': 'Cra 50 25-10 Bucaramanga', 'telefono': '3203000010', 'correo': 'mateo.salazar@gmail.com', 'estado': 1},
        ]
        
        for data in pacientes_data:
            if not Paciente.objects.filter(numero_doc=data['numero_doc']).exists():
                data['contrasena'] = make_password('Admincitaya0*')
                Paciente.objects.create(**data)

        # =====================================================================
        # 4. AGENDAMIENTOS
        # =====================================================================
        self.stdout.write('Cargando agendamientos...')
        agendamientos_data = [
            {'cita': 'Medicina General', 'fecha': '2026-06-02', 'hora': '08:00:00', 'doc_paciente': '3000000001', 'doc_medico': '2000000001'},
            {'cita': 'Cardiologia',      'fecha': '2026-06-03', 'hora': '09:30:00', 'doc_paciente': '3000000002', 'doc_medico': '2000000004'},
            {'cita': 'Pediatria',        'fecha': '2026-06-04', 'hora': '10:00:00', 'doc_paciente': '3000000003', 'doc_medico': '2000000005'},
            {'cita': 'Dermatologia',     'fecha': '2026-06-05', 'hora': '11:00:00', 'doc_paciente': '3000000004', 'doc_medico': '2000000006'},
            {'cita': 'Psicologia',       'fecha': '2026-06-06', 'hora': '14:00:00', 'doc_paciente': '3000000005', 'doc_medico': '2000000003'},
            {'cita': 'Ortopedia',        'fecha': '2026-06-09', 'hora': '08:30:00', 'doc_paciente': '3000000006', 'doc_medico': '2000000002'},
            {'cita': 'Medicina General', 'fecha': '2026-06-10', 'hora': '15:00:00', 'doc_paciente': '3000000007', 'doc_medico': '2000000007'},
            {'cita': 'Psicologia',       'fecha': '2026-06-11', 'hora': '16:00:00', 'doc_paciente': '3000000009', 'doc_medico': '2000000009'},
            {'cita': 'Cardiologia',      'fecha': '2026-06-12', 'hora': '09:00:00', 'doc_paciente': '3000000010', 'doc_medico': '2000000010'},
            {'cita': 'Ortopedia',        'fecha': '2026-06-13', 'hora': '10:30:00', 'doc_paciente': '3000000001', 'doc_medico': '2000000008'},
        ]
        
        for item in agendamientos_data:
            # Traemos las instancias completas por medio de su cédula (numero_doc)
            paciente = Paciente.objects.get(numero_doc=item['doc_paciente'])
            medico = Medico.objects.get(numero_doc=item['doc_medico'])
            
            # Validación para evitar duplicados en la base de datos local o de nube
            if not Agendamiento.objects.filter(fecha=item['fecha'], hora=item['hora'], id_paciente_id=paciente.id_paciente).exists():
                Agendamiento.objects.create(
                    cita=item['cita'],
                    fecha=item['fecha'],
                    hora=item['hora'],
                    id_paciente_id=paciente.id_paciente,
                    id_medico_id=medico.id_medico
                )

        # =====================================================================
        # 5. HISTORIALES CLINICOS
        # =====================================================================
        self.stdout.write('Cargando historiales clínicos...')
        historiales_data = [
            {'fecha_creacion': '2026-05-01', 'antecedentes': 'Paciente con hipertension arterial controlada. Se recetan betabloqueantes.', 'doc_paciente': '3000000001', 'doc_medico': '2000000004'},
            {'fecha_creacion': '2026-05-02', 'antecedentes': 'Nina con asma leve. Se indica salbutamol en aerosol y control en 3 meses.', 'doc_paciente': '3000000003', 'doc_medico': '2000000005'},
            {'fecha_creacion': '2026-05-05', 'antecedentes': 'Dermatitis atopica en miembros superiores. Se prescribe hidrocortisona topica.', 'doc_paciente': '3000000004', 'doc_medico': '2000000006'},
            {'fecha_creacion': '2026-05-07', 'antecedentes': 'Cefalea tensional cronica. Se ajusta tratamiento con ibuprofeno y se solicita TAC.', 'doc_paciente': '3000000005', 'doc_medico': '2000000003'},
            {'fecha_creacion': '2026-05-08', 'antecedentes': 'Control anual. Paciente sano, glucemia y presion arterial en rangos normales.', 'doc_paciente': '3000000002', 'doc_medico': '2000000001'},
            {'fecha_creacion': '2026-05-09', 'antecedentes': 'Fractura consolidada de radio distal. Alta de ortopedia, rehabilitacion completada.', 'doc_paciente': '3000000006', 'doc_medico': '2000000002'},
            {'fecha_creacion': '2026-05-12', 'antecedentes': 'Miopia leve OD -1.25, OS -1.00. Se indica uso de lentes correctivos.', 'doc_paciente': '3000000007', 'doc_medico': '2000000001'},
            {'fecha_creacion': '2026-05-14', 'antecedentes': 'Trastorno de ansiedad generalizada. Se inicia terapia cognitivo-conductual.', 'doc_paciente': '3000000009', 'doc_medico': '2000000009'},
            {'fecha_creacion': '2026-05-15', 'antecedentes': 'Hipotiroidismo subclinico. Se solicita perfil tiroideo y se inicia levotiroxina.', 'doc_paciente': '3000000010', 'doc_medico': '2000000010'},
            {'fecha_creacion': '2026-05-16', 'antecedentes': 'Seguimiento post-consulta. Paciente refiere mejoria. Se mantiene tratamiento.', 'doc_paciente': '3000000001', 'doc_medico': '2000000001'},
        ]
        
        for item in historiales_data:
            paciente = Paciente.objects.get(numero_doc=item['doc_paciente'])
            medico = Medico.objects.get(numero_doc=item['doc_medico'])
            
            if not Historial_Clinico.objects.filter(id_paciente_id=paciente.id_paciente, id_medico_id=medico.id_medico, fecha_creacion=item['fecha_creacion']).exists():
                Historial_Clinico.objects.create(
                    fecha_creacion=item['fecha_creacion'],
                    antecedentes=item['antecedentes'],
                    id_paciente_id=paciente.id_paciente,
                    id_medico_id=medico.id_medico
                )

        self.stdout.write(self.style.SUCCESS('¡Todo el set de pruebas se inyectó melo y encriptado de forma automática!'))