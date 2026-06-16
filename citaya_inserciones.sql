-- ==========================
-- CITAYA - DATOS DE PRUEBA
-- ==========================

-- 1. ADMINISTRADORES
INSERT INTO citas_administrador (tipo_doc, numero_doc, nombre, apellido, genero, telefono, correo, contrasena, estado) VALUES
('CC', '1000000001', 'Carlos',    'Ramirez',  'M', '3001000001', 'carlos.ramirez@citaya.com',   'Admincitaya0*', 1),
('CC', '1000000002', 'Laura',     'Gomez',    'F', '3001000002', 'laura.gomez@citaya.com',      'Admincitaya0*', 1),
('CE', '1000000003', 'Andres',    'Morales',  'M', '3001000003', 'andres.morales@citaya.com',   'Admincitaya0*', 1),
('CC', '1000000004', 'Valentina', 'Torres',   'F', '3001000004', 'valentina.torres@citaya.com', 'Admincitaya0*', 0),
('CC', '1000000005', 'Miguel',    'Herrera',  'M', '3001000005', 'miguel.herrera@citaya.com',   'Admincitaya0*', 1);

-- 2. MEDICOS
INSERT INTO citas_medico (tipo_doc, numero_doc, nombre, apellido, genero, especialidad, telefono, correo, contrasena, estado) VALUES
('CC', '2000000001', 'Sofia',   'Vargas',   'F', 'Medicina General', '3102000001', 'sofia.vargas@citaya.com',    'Admincitaya0*', 1),
('CC', '2000000002', 'Luis',    'Pena',     'M', 'Ortopedia',        '3102000002', 'luis.pena@citaya.com',       'Admincitaya0*', 1),
('CE', '2000000003', 'Natalia', 'Castro',   'F', 'Psicologia',       '3102000003', 'natalia.castro@citaya.com',  'Admincitaya0*', 1),
('CC', '2000000004', 'Roberto', 'Jimenez',  'M', 'Cardiologia',      '3102000004', 'roberto.jimenez@citaya.com', 'Admincitaya0*', 1),
('CC', '2000000005', 'Camila',  'Ruiz',     'F', 'Pediatria',        '3102000005', 'camila.ruiz@citaya.com',     'Admincitaya0*', 1),
('CC', '2000000006', 'Diego',   'Salinas',  'M', 'Dermatologia',     '3102000006', 'diego.salinas@citaya.com',   'Admincitaya0*', 1),
('CC', '2000000007', 'Paola',   'Mendoza',  'F', 'Medicina General', '3102000007', 'paola.mendoza@citaya.com',   'Admincitaya0*', 0),
('CE', '2000000008', 'Felipe',  'Rojas',    'M', 'Ortopedia',        '3102000008', 'felipe.rojas@citaya.com',    'Admincitaya0*', 1),
('CC', '2000000009', 'Isabel',  'Navarro',  'F', 'Psicologia',       '3102000009', 'isabel.navarro@citaya.com',  'Admincitaya0*', 1),
('CC', '2000000010', 'Julian',  'Rios',     'M', 'Cardiologia',      '3102000010', 'julian.rios@citaya.com',     'Admincitaya0*', 1);

-- 3. PACIENTES
INSERT INTO citas_paciente (tipo_doc, numero_doc, nombre, apellido, genero, fecha_nacimiento, tipo_sangre, direccion, telefono, correo, contrasena, estado) VALUES
('CC', '3000000001', 'Ana',       'Lopez',     'F', '1990-03-15', 'O+',  'Cra 10 20-30 Bogota',       '3203000001', 'ana.lopez@gmail.com',       'Admincitaya0*', 1),
('CC', '3000000002', 'Juan',      'Martinez',  'M', '1985-07-22', 'A+',  'Cl 50 15-40 Medellin',      '3203000002', 'juan.martinez@gmail.com',   'Admincitaya0*', 1),
('TI', '3000000003', 'Valeria',   'Diaz',      'F', '2005-01-08', 'B-',  'Av 30 5-10 Cali',           '3203000003', 'valeria.diaz@gmail.com',    'Admincitaya0*', 1),
('CC', '3000000004', 'Pedro',     'Gutierrez', 'M', '1978-11-03', 'AB+', 'Cl 12 8-22 Barranquilla',   '3203000004', 'pedro.gutierrez@gmail.com', 'Admincitaya0*', 1),
('CC', '3000000005', 'Mariana',   'Herrera',   'F', '1995-05-19', 'O-',  'Cra 7 100-50 Bogota',       '3203000005', 'mariana.herrera@gmail.com', 'Admincitaya0*', 1),
('CE', '3000000006', 'Sebastian', 'Mora',      'M', '1988-09-30', 'A-',  'Cl 80 20-15 Bogota',        '3203000006', 'sebastian.mora@gmail.com',  'Admincitaya0*', 1),
('CC', '3000000007', 'Luciana',   'Vega',      'F', '2000-12-01', 'B+',  'Cra 15 30-60 Pereira',      '3203000007', 'luciana.vega@gmail.com',    'Admincitaya0*', 1),
('CC', '3000000008', 'Tomas',     'Pardo',     'M', '1970-04-25', 'AB-', 'Cl 45 10-5 Manizales',      '3203000008', 'tomas.pardo@gmail.com',     'Admincitaya0*', 0),
('TI', '3000000009', 'Isabela',   'Cano',      'F', '2008-06-14', 'O+',  'Av 68 50-30 Bogota',        '3203000009', 'isabela.cano@gmail.com',    'Admincitaya0*', 1),
('CC', '3000000010', 'Mateo',     'Salazar',   'M', '1993-08-07', 'A+',  'Cra 50 25-10 Bucaramanga',  '3203000010', 'mateo.salazar@gmail.com',   'Admincitaya0*', 1);

-- 4. AGENDAMIENTOS
INSERT INTO citas_agendamiento (cita, fecha, hora, id_paciente_id, id_medico_id) VALUES
('Medicina General', '2026-06-02', '08:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000001'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000001')),
('Cardiologia',      '2026-06-03', '09:30:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000002'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000004')),
('Pediatria',        '2026-06-04', '10:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000003'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000005')),
('Dermatologia',     '2026-06-05', '11:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000004'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000006')),
('Psicologia',       '2026-06-06', '14:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000005'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000003')),
('Ortopedia',        '2026-06-09', '08:30:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000006'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000002')),
('Medicina General', '2026-06-10', '15:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000007'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000007')),
('Psicologia',       '2026-06-11', '16:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000009'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000009')),
('Cardiologia',      '2026-06-12', '09:00:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000010'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000010')),
('Ortopedia',        '2026-06-13', '10:30:00', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000001'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000008'));

-- 5. HISTORIALES CLINICOS
INSERT INTO citas_historial_clinico (fecha_creacion, antecedentes, id_paciente_id, id_medico_id) VALUES
('2026-05-01', 'Paciente con hipertension arterial controlada. Se recetan betabloqueantes.',           (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000001'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000004')),
('2026-05-02', 'Nina con asma leve. Se indica salbutamol en aerosol y control en 3 meses.',           (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000003'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000005')),
('2026-05-05', 'Dermatitis atopica en miembros superiores. Se prescribe hidrocortisona topica.',       (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000004'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000006')),
('2026-05-07', 'Cefalea tensional cronica. Se ajusta tratamiento con ibuprofeno y se solicita TAC.',  (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000005'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000003')),
('2026-05-08', 'Control anual. Paciente sano, glucemia y presion arterial en rangos normales.',        (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000002'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000001')),
('2026-05-09', 'Fractura consolidada de radio distal. Alta de ortopedia, rehabilitacion completada.', (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000006'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000002')),
('2026-05-12', 'Miopia leve OD -1.25, OS -1.00. Se indica uso de lentes correctivos.',                (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000007'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000001')),
('2026-05-14', 'Trastorno de ansiedad generalizada. Se inicia terapia cognitivo-conductual.',         (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000009'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000009')),
('2026-05-15', 'Hipotiroidismo subclinico. Se solicita perfil tiroideo y se inicia levotiroxina.',    (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000010'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000010')),
('2026-05-16', 'Seguimiento post-consulta. Paciente refiere mejoria. Se mantiene tratamiento.',       (SELECT id_paciente FROM citas_paciente WHERE numero_doc='3000000001'), (SELECT id_medico FROM citas_medico WHERE numero_doc='2000000001'));