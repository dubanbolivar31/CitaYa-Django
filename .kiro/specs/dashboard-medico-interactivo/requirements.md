# Requirements: Dashboard Médico Interactivo

## Overview

Ampliar el dashboard médico de CitaYa para que las 4 stat-cards sean interactivas:
al hacer clic cada tarjeta abre un modal con datos detallados servidos por una
nueva API JSON. También se agregan 3 nuevas vistas JSON en `views.py` y sus
rutas en `urls.py`.

---

## Requirement 1

**User Story:** Como médico, quiero hacer clic en la tarjeta "Total citas" y ver
la lista completa de mis citas, para revisar el historial sin salir del dashboard.

### Acceptance Criteria

1. WHEN el médico hace clic en la stat-card "Total citas"
   THEN el sistema SHALL abrir un modal con la lista paginada de todas sus citas
   (pasadas y futuras), mostrando fecha, hora, tipo y nombre del paciente.
2. WHEN la lista se carga THEN el sistema SHALL obtener los datos desde
   `GET /api/medico/stats/todas-citas/`.
3. WHEN no hay citas THEN el sistema SHALL mostrar un estado vacío dentro del modal.

---

## Requirement 2

**User Story:** Como médico, quiero hacer clic en "Citas hoy" y ver los pacientes
agendados para el día actual, para planificar mi jornada con detalle.

### Acceptance Criteria

1. WHEN el médico hace clic en la stat-card "Citas hoy"
   THEN el sistema SHALL abrir un modal con las citas del día ordenadas por hora.
2. WHEN la lista se carga THEN el sistema SHALL obtener los datos desde
   `GET /api/medico/stats/citas-hoy/`.
3. WHEN no hay citas hoy THEN el sistema SHALL mostrar un mensaje informativo.

---

## Requirement 3

**User Story:** Como médico, quiero hacer clic en "Historiales creados" y ver
todos los historiales que he registrado, para consultar notas clínicas anteriores.

### Acceptance Criteria

1. WHEN el médico hace clic en la stat-card "Historiales creados"
   THEN el sistema SHALL abrir un modal con la lista de historiales ordenada por
   fecha descendente, mostrando fecha, paciente y un preview de antecedentes.
2. WHEN la lista se carga THEN el sistema SHALL obtener los datos desde
   `GET /api/medico/stats/mis-historiales/`.
3. WHEN el médico hace clic en un historial THEN el sistema SHALL abrir el modal
   de detalle existente (modal-hist-detalle) reutilizando `verDetalleHistorial`.
4. WHEN no hay historiales THEN el sistema SHALL mostrar un estado vacío.

---

## Requirement 4

**User Story:** Como médico, quiero hacer clic en "Pacientes atendidos" y ver la
lista de pacientes únicos que he atendido, para acceder a sus datos con un clic.

### Acceptance Criteria

1. WHEN el médico hace clic en la stat-card "Pacientes atendidos"
   THEN el sistema SHALL abrir un modal con la lista de pacientes únicos.
2. WHEN el médico hace clic en un paciente de la lista
   THEN el sistema SHALL abrir el modal de ficha de paciente existente
   (modal-paciente) invocando `abrirPaciente(id, null, null, false)`.
3. WHEN no hay pacientes THEN el sistema SHALL mostrar un estado vacío.

---

## Requirement 5

**User Story:** Como médico, quiero que las nuevas APIs estén protegidas por
sesión, para que solo yo pueda acceder a mis propios datos.

### Acceptance Criteria

1. WHEN una petición a las nuevas APIs llega sin sesión de médico activa
   THEN el sistema SHALL retornar HTTP 403 con `{"error": "No autorizado"}`.
2. WHEN un médico accede a las APIs THEN el sistema SHALL filtrar los datos
   exclusivamente por su `usuario_id` de sesión.

---

## Requirement 6

**User Story:** Como médico, quiero que las stat-cards tengan un indicador visual
de que son clicables, para entender que ofrecen más información.

### Acceptance Criteria

1. WHEN el cursor pasa sobre una stat-card THEN el sistema SHALL mostrar un cursor
   `pointer` y una transición visual (elevación/brillo) que indique interactividad.
2. WHEN una stat-card está siendo cargada THEN el sistema SHALL deshabilitar el
   clic para evitar peticiones duplicadas.
