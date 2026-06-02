# Implementation Plan: Dashboard Médico Interactivo

## Overview

Implementación incremental del dashboard médico interactivo de CitaYa. Se agregan
3 vistas JSON al backend, 3 rutas en `urls.py`, estilos de interactividad en el
CSS y 4 nuevos modales con su lógica de fetch en el template HTML. Las tareas
siguen el orden: backend → frontend → pruebas.

---

## Tasks

- [ ] 1. Agregar las 3 vistas JSON en `views.py`
  - [ ] 1.1 Implementar `todas_citas_medico_json`
    - Verificar sesión `rol == 'medico'`, retornar 403 si no.
    - Filtrar `Agendamiento` por `id_medico = session['usuario_id']` con `select_related('id_paciente')`.
    - Ordenar por `-fecha, -hora`.
    - Serializar los campos: `id_agendamiento`, `fecha`, `hora`, `tipo_cita` (campo `cita`), `paciente_nombre`, `paciente_doc`, `id_paciente`.
    - Retornar `JsonResponse({'citas': data})`.
    - _Requirements: 1.2, 5.1, 5.2_

  - [ ] 1.2 Implementar `citas_hoy_medico_json`
    - Verificar sesión `rol == 'medico'`, retornar 403 si no.
    - Filtrar `Agendamiento` por `id_medico` y `fecha = date.today()`.
    - Ordenar por `hora ASC`.
    - Campo `cumplida`: verificar si existe `Historial_Clinico` con `id_paciente` e `id_medico` creado hoy (misma lógica que `agenda_medico_json`).
    - Serializar: `id_agendamiento`, `hora`, `tipo_cita`, `paciente_nombre`, `paciente_doc`, `id_paciente`, `cumplida`.
    - Retornar `JsonResponse({'citas': data})`.
    - _Requirements: 2.1, 2.2, 5.1, 5.2_

  - [ ] 1.3 Implementar `mis_historiales_json`
    - Verificar sesión `rol == 'medico'`, retornar 403 si no.
    - Filtrar `Historial_Clinico` por `id_medico = session['usuario_id']` con `select_related('id_paciente')`.
    - Ordenar por `-fecha_creacion`.
    - Serializar: `id_historial`, `fecha_creacion` (formato `DD/MM/YYYY`), `antecedentes`, `paciente_nombre`, `paciente_doc`, `id_paciente`.
    - Retornar `JsonResponse({'historiales': data})`.
    - _Requirements: 3.1, 3.2, 5.1, 5.2_

  - [ ]* 1.4 Escribir pruebas unitarias para las 3 vistas — autorización
    - Crear `citas/tests/test_stats_views.py` con clase `TestStatsAutorizacion(TestCase)`.
    - Para cada una de las 3 vistas probar: sin sesión → 403, sesión `paciente` → 403, sesión `admin` → 403.
    - _Requirements: 5.1_

  - [ ]* 1.5 Escribir prueba de propiedad — Property 1: Aislamiento de datos por médico
    - **Property 1: Aislamiento de datos por médico**
    - Usar `hypothesis` con estrategia personalizada para generar citas de médico A y médico B.
    - Autenticar como médico A, llamar a las 3 vistas, verificar que ningún registro contiene `id_medico` del médico B.
    - `@settings(max_examples=100)`.
    - **Validates: Requirements 5.1, 5.2**

- [ ] 2. Registrar las 3 nuevas rutas en `urls.py`
  - [ ] 2.1 Añadir las rutas `api/medico/stats/` en `urls.py`
    - Agregar bajo el bloque `# API MÉDICO`:
      ```python
      path('api/medico/stats/todas-citas/',    views.todas_citas_medico_json, name='todas_citas_medico_json'),
      path('api/medico/stats/citas-hoy/',      views.citas_hoy_medico_json,   name='citas_hoy_medico_json'),
      path('api/medico/stats/mis-historiales/', views.mis_historiales_json,    name='mis_historiales_json'),
      ```
    - _Requirements: 1.2, 2.2, 3.2_

- [ ] 3. Checkpoint — Verificar backend
  - Asegurarse de que el servidor Django arranca sin errores (`python manage.py check`).
  - Verificar manualmente (o con el cliente de pruebas) que las 3 rutas responden 403 sin sesión.
  - Asegurarse de que todas las pruebas unitarias pasen.

- [ ] 4. Agregar estilos de interactividad en `dashboard_medico.css`
  - [ ] 4.1 Añadir clase `.stat-card-clickable` con variantes hover / active / loading
    - Insertar el siguiente bloque CSS después de `.stat-card:hover { … }`:
      ```css
      .stat-card-clickable {
        cursor: pointer;
      }
      .stat-card-clickable:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-md);
        border-color: color-mix(in srgb, var(--c, var(--blue-700)) 30%, white);
      }
      .stat-card-clickable:active {
        transform: translateY(-1px);
      }
      .stat-card-clickable.loading {
        pointer-events: none;
        opacity: 0.75;
      }
      ```
    - _Requirements: 6.1, 6.2_

- [ ] 5. Modificar `inicio_medico.html`: stat-cards clicables y objeto URLS
  - [ ] 5.1 Añadir clase `stat-card-clickable` y atributo `data-modal` a las 4 stat-cards
    - Stat-card "Total citas" → `data-modal="modal-stats-citas"`.
    - Stat-card "Citas hoy" → `data-modal="modal-stats-hoy"`.
    - Stat-card "Historiales creados" → `data-modal="modal-stats-historiales"`.
    - Stat-card "Pacientes atendidos" → `data-modal="modal-stats-pacientes"`.
    - Agregar `stat-card-clickable` a la clase `class` de cada `div.stat-card`.
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 6.1_

  - [ ] 5.2 Ampliar el objeto `URLS` con las 3 nuevas rutas
    - Añadir dentro del bloque `const URLS = { … }`:
      ```js
      todasCitas:     "{% url 'todas_citas_medico_json' %}",
      citasHoy:       "{% url 'citas_hoy_medico_json' %}",
      misHistoriales: "{% url 'mis_historiales_json' %}",
      ```
    - _Requirements: 1.2, 2.2, 3.2_

- [ ] 6. Implementar función `loadStatModal` y listeners de stat-cards
  - [ ] 6.1 Agregar función genérica `loadStatModal(modalId, url, renderFn)`
    - Abrir el modal con `openModal(modalId)`.
    - Poner `body.innerHTML = '<div class="m-loading">…</div>'` mientras carga.
    - Agregar / quitar clase `loading` en la stat-card durante el fetch.
    - Capturar errores con `try/catch` y mostrar `.msg-error` en el body del modal.
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 6.2_

  - [ ] 6.2 Agregar listener de clic en las stat-cards mediante `data-modal`
    - Al hacer `DOMContentLoaded`, iterar `document.querySelectorAll('.stat-card-clickable')`.
    - Leer `dataset.modal` y llamar a la función de carga correspondiente (`loadStatModal` con la `renderFn` adecuada).
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 6.1_

- [ ] 7. Implementar los 4 nuevos modales en `inicio_medico.html`
  - [ ] 7.1 Agregar HTML del modal `modal-stats-citas` (Total citas)
    - Estructura: `modal-overlay` > `modal-box modal-lg` con header, `modal-body id="body-modal-stats-citas"` y footer con botón Cerrar.
    - Título: "Todas mis citas" + icono `fa-calendar-check`.
    - _Requirements: 1.1, 1.3_

  - [ ] 7.2 Agregar HTML del modal `modal-stats-hoy` (Citas hoy)
    - Estructura similar; `modal-body id="body-modal-stats-hoy"`.
    - Título: "Citas de hoy" + icono `fa-calendar-day`.
    - _Requirements: 2.1, 2.3_

  - [ ] 7.3 Agregar HTML del modal `modal-stats-historiales` (Mis historiales)
    - Estructura similar; `modal-body id="body-modal-stats-historiales"`.
    - Título: "Mis historiales" + icono `fa-file-waveform`.
    - _Requirements: 3.1, 3.4_

  - [ ] 7.4 Agregar HTML del modal `modal-stats-pacientes` (Pacientes atendidos)
    - Estructura similar; `modal-body id="body-modal-stats-pacientes"`.
    - Título: "Pacientes atendidos" + icono `fa-users`.
    - _Requirements: 4.1, 4.3_

- [ ] 8. Implementar funciones `renderFn` para cada modal
  - [ ] 8.1 Implementar `renderTodasCitas(body, data)`
    - Si `data.citas` es vacío, mostrar `.empty-state` con mensaje "Sin citas registradas.".
    - Si hay citas, renderizar lista de filas con: fecha, hora, tipo de cita, nombre del paciente y documento.
    - Cada fila es clicable → llama `abrirPaciente(c.id_paciente, null, null, false)`.
    - _Requirements: 1.1, 1.3_

  - [ ] 8.2 Implementar `renderCitasHoy(body, data)`
    - Si `data.citas` es vacío, mostrar `.empty-state` con mensaje "Sin citas para hoy.".
    - Si hay citas, renderizar filas con: hora, tipo de cita, nombre del paciente y badge "Cumplida" o "Pendiente" según `cumplida`.
    - _Requirements: 2.1, 2.3_

  - [ ] 8.3 Implementar `renderMisHistoriales(body, data)`
    - Si `data.historiales` es vacío, mostrar `.empty-state`.
    - Si hay historiales, reutilizar el patrón `hist-row` existente con `data-idx` y `_historiales` en el body.
    - Al hacer clic en una fila, llamar `verDetalleHistorial(h.fecha_creacion, h.paciente_nombre, h.antecedentes)`.
    - _Requirements: 3.1, 3.3, 3.4_

  - [ ] 8.4 Implementar `renderPacientesAtendidos(body, data)`
    - Deduplicar `data.citas` por `id_paciente` (usando un `Map` o `Set`).
    - Si la lista deduplicada es vacía, mostrar `.empty-state`.
    - Si hay pacientes, renderizar filas con nombre, documento; al clic → `abrirPaciente(id, null, null, false)`.
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 8.5 Escribir prueba de propiedad — Property 4: Unicidad de pacientes en la lista de atendidos
    - **Property 4: Unicidad de pacientes en lista de atendidos**
    - Generar listas de citas con `id_paciente` repetidos usando `hypothesis`.
    - Llamar a `todas_citas_medico_json` y verificar que al deduplicar los `id_paciente` no existen repeticiones.
    - `@settings(max_examples=100)`.
    - **Validates: Requirements 4.1**

- [ ] 9. Checkpoint — Verificar integración frontend
  - Asegurarse de que todas las pruebas unitarias pasen (`python manage.py test citas`).
  - Verificar que no hay errores de template en la consola del navegador.
  - Verificar que las 4 stat-cards muestran cursor `pointer` al hover.

- [ ] 10. Pruebas unitarias de filtrado y datos
  - [ ] 10.1 Escribir pruebas de datos vacíos para las 3 vistas
    - Médico sin citas → `todas_citas_medico_json` retorna `{"citas": []}`.
    - Médico sin citas hoy → `citas_hoy_medico_json` retorna `{"citas": []}`.
    - Médico sin historiales → `mis_historiales_json` retorna `{"historiales": []}`.
    - _Requirements: 1.3, 2.3, 3.4_

  - [ ] 10.2 Escribir prueba de filtrado por médico (dos médicos con datos distintos)
    - Crear médico A y médico B con sus propias citas e historiales.
    - Autenticar como médico A; verificar que las 3 respuestas no contienen datos del médico B.
    - _Requirements: 5.1, 5.2_

  - [ ]* 10.3 Escribir prueba de propiedad — Property 2: Filtrado correcto de citas del día
    - **Property 2: Filtrado correcto de citas del día**
    - Generar citas con fechas distribuidas en pasado, hoy y futuro usando `hypothesis`.
    - Llamar a `citas_hoy_medico_json` y verificar que solo retorna citas con `fecha == date.today()`.
    - `@settings(max_examples=100)`.
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 10.4 Escribir prueba de propiedad — Property 3: Ordenamiento descendente de historiales
    - **Property 3: Ordenamiento descendente de historiales**
    - Generar N historiales con fechas aleatorias usando `hypothesis`.
    - Llamar a `mis_historiales_json` y verificar que para todo par consecutivo `(h_i, h_{i+1})`, `fecha_creacion[i] >= fecha_creacion[i+1]`.
    - `@settings(max_examples=100)`.
    - **Validates: Requirements 3.1**

- [ ] 11. Checkpoint final — Verificar cobertura completa
  - Ejecutar `python manage.py test citas` y asegurarse de que todas las pruebas pasen.
  - Verificar que los 4 modales abren y cierran correctamente (×, overlay y botón Cerrar).
  - Verificar el estado vacío en todos los modales con 0 registros.

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido.
- Cada tarea referencia los requisitos específicos para trazabilidad.
- Los checkpoints permiten validación incremental antes de avanzar.
- Las pruebas de propiedad requieren instalar `hypothesis`: `pip install hypothesis`.
- La 4ª stat-card (Pacientes atendidos) reutiliza `todas_citas_medico_json` para construir la lista de pacientes únicos — no se necesita una vista nueva.
- El campo `cita` del modelo `Agendamiento` se serializa como `tipo_cita` en la respuesta JSON.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "1.4"] },
    { "id": 2, "tasks": ["4.1", "5.1", "5.2", "1.5"] },
    { "id": 3, "tasks": ["6.1", "6.2", "7.1", "7.2", "7.3", "7.4"] },
    { "id": 4, "tasks": ["8.1", "8.2", "8.3", "8.4"] },
    { "id": 5, "tasks": ["8.5", "10.1", "10.2"] },
    { "id": 6, "tasks": ["10.3", "10.4"] }
  ]
}
```
