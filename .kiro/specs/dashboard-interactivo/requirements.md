# Requirements Document

## Introduction

CitaYa es un sistema de citas médicas Django con tres roles: Administrador, Médico y Paciente. Actualmente los dashboards existen pero no son suficientemente interactivos: el dashboard del Administrador está completamente vacío (solo hereda base.html), y las tarjetas de estadísticas de los dashboards del Médico y del Paciente no responden al hacer clic.

Esta feature construye desde cero el dashboard del Administrador con estadísticas clickeables, topbar, reloj en vivo y acciones rápidas; añade modales de detalle a las tarjetas del dashboard del Médico; y conecta las tarjetas del dashboard del Paciente a los modales y secciones ya existentes.

## Glossary

- **Dashboard_Admin**: La vista en `inicio_admin.html` que renderiza la vista `dashboard_admin` para usuarios con `rol == 'admin'`.
- **Dashboard_Medico**: La vista en `inicio_medico.html` para usuarios con `rol == 'medico'`.
- **Dashboard_Paciente**: La vista en `inicio_paciente.html` para usuarios con `rol == 'paciente'`.
- **Stat_Card**: Tarjeta de estadística visual que muestra un número (total_medicos, total_pacientes, etc.) en el grid de estadísticas de un dashboard.
- **Modal_Detalle**: Panel superpuesto (overlay) que aparece sobre el dashboard al hacer clic en una Stat_Card y muestra una lista de registros relacionados cargados via AJAX.
- **API_Admin**: Endpoint Django que devuelve datos JSON, protegido por `rol == 'admin'`, destinado a poblar los Modal_Detalle del Dashboard_Admin.
- **Topbar**: Barra superior del dashboard que muestra el logo, nombre del usuario, reloj en vivo y menú de perfil.
- **Live_Clock**: Componente de reloj digital en el Topbar que actualiza la hora cada segundo.
- **Quick_Action**: Botón o enlace en la sección de acciones rápidas del Dashboard_Admin que navega a un módulo CRUD existente.
- **CSRF_Token**: Token de seguridad Django requerido en peticiones POST para prevenir ataques CSRF.

---

## Requirements

### Requirement 1: Dashboard del Administrador — Topbar

**User Story:** Como administrador, quiero ver mi nombre, la hora en vivo y acceder a mi perfil desde la barra superior, para tener contexto de sesión sin necesidad de navegar a otra página.

#### Acceptance Criteria

1. THE Dashboard_Admin SHALL renderizar un Topbar con el logo de CitaYa, el nombre del administrador proveniente del contexto de sesión `nombre`, y un botón de perfil (avatar).
2. WHEN la página del Dashboard_Admin carga, THE Live_Clock SHALL comenzar a mostrar la hora actual en formato `HH:MM:SS`.
3. WHILE el Dashboard_Admin esté visible, THE Live_Clock SHALL actualizarse cada 1000 milisegundos con la hora del sistema del cliente.
4. WHEN el botón de avatar es presionado, THE Dashboard_Admin SHALL mostrar un dropdown con las opciones "Mi Perfil" y "Cerrar sesión".
5. WHEN la opción "Cerrar sesión" es seleccionada, THE Dashboard_Admin SHALL redirigir al usuario a la URL `logout_admin`.
6. WHEN la opción "Mi Perfil" es seleccionada, THE Dashboard_Admin SHALL abrir el modal de perfil del administrador, cargando los datos via la API existente `perfil_admin_json`.

---

### Requirement 2: Dashboard del Administrador — Tarjetas de estadísticas clickeables

**User Story:** Como administrador, quiero hacer clic en cada tarjeta de estadística para ver la lista completa de registros correspondientes, para tener acceso rápido a la información sin salir del dashboard.

#### Acceptance Criteria

1. THE Dashboard_Admin SHALL mostrar cuatro Stat_Cards con los valores `total_medicos`, `total_pacientes`, `total_citas` y `total_historiales` ya disponibles en el contexto de la vista `dashboard_admin`.
2. WHEN el usuario hace clic en la Stat_Card de "Total médicos", THE Dashboard_Admin SHALL abrir un Modal_Detalle con una tabla de todos los médicos registrados, cargados via API_Admin.
3. WHEN el usuario hace clic en la Stat_Card de "Total pacientes", THE Dashboard_Admin SHALL abrir un Modal_Detalle con una tabla de todos los pacientes registrados, cargados via API_Admin.
4. WHEN el usuario hace clic en la Stat_Card de "Total citas", THE Dashboard_Admin SHALL abrir un Modal_Detalle con una tabla de todos los agendamientos registrados, cargados via API_Admin.
5. WHEN el usuario hace clic en la Stat_Card de "Total historiales", THE Dashboard_Admin SHALL abrir un Modal_Detalle con una tabla de todos los historiales clínicos registrados, cargados via API_Admin.
6. THE Dashboard_Admin SHALL aplicar a cada Stat_Card el estilo CSS `cursor: pointer` y una animación de elevación (translateY) en el estado `:hover` para indicar interactividad.
7. WHEN un Modal_Detalle está abierto y el usuario hace clic fuera del cuadro del modal o en el botón de cierre, THE Dashboard_Admin SHALL ocultar el modal.

---

### Requirement 3: APIs JSON del Administrador

**User Story:** Como desarrollador, quiero APIs JSON dedicadas para el administrador, para que los Modal_Detalle del Dashboard_Admin puedan cargarse via AJAX sin recargar la página.

#### Acceptance Criteria

1. THE API_Admin `api/admin/medicos/` SHALL retornar una lista JSON de todos los médicos con los campos: `id_medico`, `nombre`, `apellido`, `especialidad`, `telefono`, `correo`, `estado`.
2. THE API_Admin `api/admin/pacientes/` SHALL retornar una lista JSON de todos los pacientes con los campos: `id_paciente`, `nombre`, `apellido`, `tipo_doc`, `numero_doc`, `telefono`, `correo`, `estado`.
3. THE API_Admin `api/admin/citas/` SHALL retornar una lista JSON de todos los agendamientos con los campos: `id_agendamiento`, `cita`, `fecha`, `hora`, `paciente_nombre`, `medico_nombre`, `especialidad`.
4. THE API_Admin `api/admin/historiales/` SHALL retornar una lista JSON de todos los historiales clínicos con los campos: `id_historial`, `fecha_creacion`, `paciente_nombre`, `medico_nombre`, `especialidad`, `preview_antecedentes` (primeros 80 caracteres de antecedentes).
5. IF una solicitud a cualquier API_Admin llega con `request.session['rol'] != 'admin'`, THEN THE API_Admin SHALL retornar una respuesta JSON con código HTTP 403 y el campo `{'error': 'No autorizado'}`.
6. WHERE los datos a serializar incluyan campos de relaciones ForeignKey (médico, paciente), THE API_Admin SHALL resolver esos campos con `select_related` para evitar consultas N+1.

---

### Requirement 4: Dashboard del Administrador — Acciones rápidas

**User Story:** Como administrador, quiero tener accesos directos visibles a todos los módulos de gestión, para navegar rápidamente sin memorizar URLs.

#### Acceptance Criteria

1. THE Dashboard_Admin SHALL mostrar una sección "Acciones rápidas" con Quick_Actions que enlazan a las cinco vistas de lista existentes: `ver_medicos`, `ver_pacientes`, `ver_agendamientos`, `ver_historiales` y `ver_administrador`.
2. THE Dashboard_Admin SHALL mostrar en cada Quick_Action un ícono FontAwesome representativo y una etiqueta de texto descriptiva.
3. WHEN el usuario hace clic en un Quick_Action, THE Dashboard_Admin SHALL navegar a la URL correspondiente del módulo CRUD.

---

### Requirement 5: Dashboard del Médico — Tarjetas clickeables

**User Story:** Como médico, quiero hacer clic en mis tarjetas de estadísticas para ver detalles de mis citas, historiales y pacientes, para tener acceso rápido a la información desde el panel principal.

#### Acceptance Criteria

1. WHEN el usuario hace clic en la Stat_Card "Total citas" del Dashboard_Medico, THE Dashboard_Medico SHALL abrir un Modal_Detalle con todas las citas del médico, cargadas via una nueva API `api/medico/mis-citas/`.
2. WHEN el usuario hace clic en la Stat_Card "Citas hoy" del Dashboard_Medico, THE Dashboard_Medico SHALL abrir un Modal_Detalle con solo las citas del médico cuya fecha sea igual a la fecha actual del servidor.
3. WHEN el usuario hace clic en la Stat_Card "Historiales creados" del Dashboard_Medico, THE Dashboard_Medico SHALL abrir un Modal_Detalle con todos los historiales clínicos creados por el médico, cargados via una nueva API `api/medico/mis-historiales/`.
4. WHEN el usuario hace clic en la Stat_Card "Pacientes atendidos" del Dashboard_Medico, THE Dashboard_Medico SHALL abrir un Modal_Detalle con la lista de pacientes únicos que tienen al menos una cita con el médico, cargados via una nueva API `api/medico/mis-pacientes/`.
5. IF la API correspondiente devuelve una lista vacía, THEN THE Dashboard_Medico SHALL mostrar en el Modal_Detalle un estado vacío con ícono y mensaje descriptivo en lugar de una tabla.
6. THE Dashboard_Medico SHALL aplicar a cada Stat_Card el estilo CSS `cursor: pointer` para indicar interactividad.

---

### Requirement 6: APIs JSON del Médico — Mis Citas, Historiales y Pacientes

**User Story:** Como desarrollador, quiero APIs dedicadas para el médico, para que los nuevos Modal_Detalle del Dashboard_Medico puedan cargarse via AJAX.

#### Acceptance Criteria

1. THE API `api/medico/mis-citas/` SHALL retornar todas las citas del médico logueado con los campos: `id_agendamiento`, `cita`, `fecha`, `hora`, `paciente_nombre`, `paciente_doc`.
2. THE API `api/medico/mis-citas/` SHALL aceptar un parámetro de query `?solo_hoy=1` que filtre las citas a solo aquellas con `fecha == date.today()`.
3. THE API `api/medico/mis-historiales/` SHALL retornar todos los historiales clínicos creados por el médico logueado, ordenados por `fecha_creacion` descendente, con los campos: `id_historial`, `fecha_creacion`, `paciente_nombre`, `preview_antecedentes`.
4. THE API `api/medico/mis-pacientes/` SHALL retornar la lista de pacientes únicos que tienen al menos una cita con el médico logueado, con los campos: `id_paciente`, `nombre`, `apellido`, `tipo_doc`, `numero_doc`, `total_citas` (conteo de citas del médico con ese paciente).
5. IF una solicitud a cualquier API del médico llega con `request.session['rol'] != 'medico'`, THEN THE API SHALL retornar una respuesta JSON con código HTTP 403 y el campo `{'error': 'No autorizado'}`.

---

### Requirement 7: Dashboard del Paciente — Tarjetas conectadas

**User Story:** Como paciente, quiero que las tarjetas de estadísticas respondan al hacer clic, para acceder rápidamente a mis citas e historial desde el panel principal.

#### Acceptance Criteria

1. WHEN el usuario hace clic en la Stat_Card "Total citas" del Dashboard_Paciente, THE Dashboard_Paciente SHALL abrir el modal existente con id `modal-mis-citas` y cargar las citas del paciente.
2. WHEN el usuario hace clic en la Stat_Card "Próximas citas" del Dashboard_Paciente, THE Dashboard_Paciente SHALL realizar un scroll suave hasta la sección "Próximas citas" identificada por el título de sección correspondiente.
3. WHEN el usuario hace clic en la Stat_Card "Historiales" del Dashboard_Paciente, THE Dashboard_Paciente SHALL abrir el modal existente con id `modal-historial` y cargar el historial del paciente.
4. WHEN el usuario hace clic en la Stat_Card "Médicos tratantes" del Dashboard_Paciente, THE Dashboard_Paciente SHALL realizar un scroll suave hasta la sección "Médicos tratantes" identificada por el id `medicos-tratantes-grid`.
5. THE Dashboard_Paciente SHALL aplicar a cada Stat_Card el estilo CSS `cursor: pointer` para indicar interactividad.
6. IF la Stat_Card "Total citas" tiene valor 0, THEN THE Dashboard_Paciente SHALL abrir igualmente el modal `modal-mis-citas` mostrando el estado vacío ya implementado en la función `loadCitas`.
