# Design: Dashboard Médico Interactivo

## Overview

El dashboard médico de CitaYa ya muestra 4 stat-cards con contadores estáticos
(total citas, citas hoy, historiales creados, pacientes atendidos). Esta feature
convierte esas tarjetas en puntos de entrada interactivos: cada clic abre un
modal con datos detallados obtenidos vía fetch a una nueva API JSON.

**Alcance del cambio:**

| Capa | Cambios |
|---|---|
| `views.py` | 3 nuevas vistas JSON para el médico |
| `urls.py` | 3 nuevas rutas bajo `/api/medico/stats/` |
| `inicio_medico.html` | Stat-cards clicables + 4 nuevos modales + JS de fetch |
| `dashboard_medico.css` | Estilos de interactividad en stat-cards |

La 4ª stat-card (Pacientes atendidos) reutiliza la API ya existente
`paciente_medico_json` y no requiere vista nueva.

---

## Architecture

El sistema sigue la arquitectura actual del proyecto: Django como backend
monolítico con templates HTML + JavaScript vanilla. No se introduce ninguna
dependencia nueva.

```
┌─────────────────────────────────────────────────────┐
│  Browser                                            │
│                                                     │
│  inicio_medico.html                                 │
│  ├── stat-card click listener                       │
│  │     └── fetch(API_URL)                           │
│  │           └── renderiza modal                    │
│  └── modal reutilizado (paciente / hist-detalle)    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP GET (JSON)
┌────────────────────▼────────────────────────────────┐
│  Django / citas/views.py                            │
│  ├── todas_citas_medico_json   (nueva)              │
│  ├── citas_hoy_medico_json     (nueva)              │
│  ├── mis_historiales_json      (nueva)              │
│  └── paciente_medico_json      (ya existe)          │
└────────────────────┬────────────────────────────────┘
                     │ ORM queries
┌────────────────────▼────────────────────────────────┐
│  SQLite / PostgreSQL                                │
│  Agendamiento · Historial_Clinico · Paciente        │
└─────────────────────────────────────────────────────┘
```

**Flujo de autenticación:** Todas las nuevas vistas verifican
`request.session.get('rol') == 'medico'` y retornan 403 si la sesión es inválida,
igual que las vistas existentes.

---

## Components and Interfaces

### 1. Nuevas vistas JSON en `views.py`

#### `todas_citas_medico_json(request)`

```
GET /api/medico/stats/todas-citas/
Sesión: rol=medico
Respuesta 200:
{
  "citas": [
    {
      "id_agendamiento": int,
      "fecha": "YYYY-MM-DD",
      "hora": "HH:MM",
      "tipo_cita": str,
      "paciente_nombre": str,
      "paciente_doc": str,
      "id_paciente": int
    },
    ...
  ]
}
Respuesta 403: { "error": "No autorizado" }
```

- Filtra `Agendamiento` por `id_medico = session['usuario_id']`.
- Ordena por `fecha DESC, hora DESC` (más recientes primero).
- Sin paginación en backend; el frontend muestra todos en lista scrollable.

#### `citas_hoy_medico_json(request)`

```
GET /api/medico/stats/citas-hoy/
Sesión: rol=medico
Respuesta 200:
{
  "citas": [
    {
      "id_agendamiento": int,
      "hora": "HH:MM",
      "tipo_cita": str,
      "paciente_nombre": str,
      "paciente_doc": str,
      "id_paciente": int,
      "cumplida": bool
    },
    ...
  ]
}
```

- Filtra por `id_medico` y `fecha = date.today()`.
- Ordena por `hora ASC`.
- El campo `cumplida` reutiliza la lógica de `agenda_medico_json`
  (verifica si existe historial creado hoy para ese paciente).

#### `mis_historiales_json(request)`

```
GET /api/medico/stats/mis-historiales/
Sesión: rol=medico
Respuesta 200:
{
  "historiales": [
    {
      "id_historial": int,
      "fecha_creacion": "DD/MM/YYYY",
      "antecedentes": str,
      "paciente_nombre": str,
      "paciente_doc": str,
      "id_paciente": int
    },
    ...
  ]
}
```

- Filtra `Historial_Clinico` por `id_medico = session['usuario_id']`.
- Ordena por `fecha_creacion DESC`.

### 2. Nuevas rutas en `urls.py`

```python
# bajo API MÉDICO
path('api/medico/stats/todas-citas/',   views.todas_citas_medico_json,  name='todas_citas_medico_json'),
path('api/medico/stats/citas-hoy/',     views.citas_hoy_medico_json,    name='citas_hoy_medico_json'),
path('api/medico/stats/mis-historiales/', views.mis_historiales_json,   name='mis_historiales_json'),
```

### 3. Modificaciones en `inicio_medico.html`

#### Stat-cards: atributo `data-modal`

Cada `.stat-card` recibe un atributo `data-modal` que identifica qué modal abrir:

```html
<div class="stat-card stat-card-clickable" data-modal="modal-stats-citas"
     style="--c:#0F4C75">
  ...
</div>
```

El atributo `stat-card-clickable` añade el cursor pointer y el indicador visual
sin tocar la lógica de estilos existente.

#### 4 nuevos modales

| ID modal | Contenido | API |
|---|---|---|
| `modal-stats-citas` | Lista completa de citas | `todas_citas_medico_json` |
| `modal-stats-hoy` | Citas del día de hoy | `citas_hoy_medico_json` |
| `modal-stats-historiales` | Mis historiales | `mis_historiales_json` |
| `modal-stats-pacientes` | Pacientes únicos atendidos | `paciente_medico_json` (existente) |

El modal de pacientes construye la lista a partir de los IDs únicos obtenidos
con `todas_citas_medico_json` (sin llamada extra).

#### Objeto `URLS` ampliado

```js
const URLS = {
  // ... URLs existentes ...
  todasCitas:    "{% url 'todas_citas_medico_json' %}",
  citasHoy:      "{% url 'citas_hoy_medico_json' %}",
  misHistoriales:"{% url 'mis_historiales_json' %}",
};
```

#### Función genérica `loadStatModal(modalId, url, renderFn)`

Para evitar duplicación, se introduce una función reutilizable:

```js
async function loadStatModal(modalId, url, renderFn) {
  openModal(modalId);
  const body = document.getElementById('body-' + modalId);
  body.innerHTML = '<div class="m-loading">…</div>';
  try {
    const data = await (await fetch(url)).json();
    renderFn(body, data);
  } catch (e) {
    body.innerHTML = '<div class="msg-error">Error al cargar datos.</div>';
  }
}
```

### 4. Modificaciones en `dashboard_medico.css`

Añadir al bloque de `.stat-card`:

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

---

## Data Models

No se modifica ningún modelo. Las consultas usan los modelos existentes:

| Modelo | Campos usados |
|---|---|
| `Agendamiento` | `id_agendamiento`, `fecha`, `hora`, `cita`, `id_paciente`, `id_medico` |
| `Historial_Clinico` | `id_historial`, `fecha_creacion`, `antecedentes`, `id_paciente`, `id_medico` |
| `Paciente` | `id_paciente`, `nombre`, `apellido`, `numero_doc` |
| `Medico` | `id_medico` (solo para filtrar por médico de sesión) |

**Consultas ORM nuevas:**

```python
# todas_citas_medico_json
Agendamiento.objects
    .filter(id_medico=medico_id)
    .select_related('id_paciente')
    .order_by('-fecha', '-hora')

# citas_hoy_medico_json
Agendamiento.objects
    .filter(id_medico=medico_id, fecha=date.today())
    .select_related('id_paciente')
    .order_by('hora')

# mis_historiales_json
Historial_Clinico.objects
    .filter(id_medico=medico_id)
    .select_related('id_paciente')
    .order_by('-fecha_creacion')
```

---

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse en
todas las ejecuciones válidas del sistema — una declaración formal de lo que el
sistema debe hacer. Las propiedades sirven como puente entre especificaciones
legibles por humanos y garantías de corrección verificables automáticamente.*

### Property 1: Aislamiento de datos por médico

*Para cualquier* médico A y médico B (A ≠ B), los datos retornados por las tres
nuevas APIs autenticadas como médico A no deben contener ningún registro cuyo
`id_medico` sea el del médico B.

**Validates: Requirements 5.1, 5.2**

### Property 2: Filtrado correcto de citas del día

*Para cualquier* conjunto de citas de un médico distribuidas en distintas fechas,
el endpoint `citas-hoy` debe retornar exactamente las citas cuya `fecha`
coincide con `date.today()`, sin incluir citas de otros días.

**Validates: Requirements 2.1, 2.2**

### Property 3: Ordenamiento descendente de historiales

*Para cualquier* médico con N historiales clínicos (N ≥ 1), los historiales
retornados por `mis-historiales` deben estar ordenados de forma que para todo
par consecutivo (h_i, h_{i+1}), `h_i.fecha_creacion >= h_{i+1}.fecha_creacion`.

**Validates: Requirements 3.1**

### Property 4: Unicidad de pacientes en la lista de atendidos

*Para cualquier* médico con M citas que referencien P pacientes distintos
(incluyendo múltiples citas del mismo paciente), la lista construida en el
frontend a partir de `todas-citas` no debe contener el mismo `id_paciente` más
de una vez.

**Validates: Requirements 4.1**

### Property 5: Totales consistentes entre stat-card y modal

*Para cualquier* médico, el número `total_citas` pasado al template por
`dashboard_medico` debe ser igual a la longitud de la lista retornada por
`todas-citas` en el mismo instante (sin citas creadas entre ambas llamadas).

**Validates: Requirements 1.1, 1.2**

---

## Error Handling

| Situación | Comportamiento esperado |
|---|---|
| Sesión no iniciada o rol incorrecto | 403 JSON `{"error": "No autorizado"}` |
| Error de DB / excepción en vista | 500 implícito de Django; el frontend muestra `msg-error` |
| Fetch falla por red | `loadStatModal` captura el error y muestra mensaje en el body del modal |
| Modal abierto mientras carga | La card recibe clase `loading` con `pointer-events:none` hasta que el fetch completa |
| Clic repetido en card | Bloqueado por la clase `loading`; evita peticiones duplicadas |

Las vistas nuevas siguen el patrón de las existentes: bloque `try/except`
devuelve 400 con mensaje de error descriptivo.

---

## Testing Strategy

### Pruebas de unidad (Django TestCase)

Se utilizará `django.test.TestCase` con `Client` de Django para las vistas:

1. **Test de autorización (3 vistas × 3 roles):** Verificar que cada vista
   retorna 403 para sesiones de `paciente`, `admin` y sin sesión.
2. **Test de datos vacíos:** Médico sin citas/historiales retorna listas vacías.
3. **Test de filtrado por médico:** Dos médicos con datos distintos; autenticado
   como médico A, verificar que la respuesta no incluye datos del médico B
   (**Property 1**).
4. **Test de citas-hoy:** Citas en fechas pasadas, hoy y futuras; verificar que
   solo devuelve las de hoy (**Property 2**).

### Pruebas de propiedad (pytest + Hypothesis)

PBT es aplicable porque las nuevas vistas son funciones con lógica de filtrado
y ordenamiento que varía con los datos de entrada (conjuntos de citas e
historiales), y 100+ iteraciones revelan edge cases de fechas, IDs duplicados y
ordenamientos.

**Librería:** `hypothesis` con `hypothesis-django`.  
**Iteraciones mínimas:** 100 por propiedad (`settings(max_examples=100)`).

#### Property Test 1 — Aislamiento de datos

```python
# Feature: dashboard-medico-interactivo, Property 1: Aislamiento de datos por médico
@given(
    medico_a_citas=st.lists(cita_strategy(), min_size=0, max_size=20),
    medico_b_citas=st.lists(cita_strategy(), min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_data_isolation(medico_a_citas, medico_b_citas):
    # Crear médico A y B con sus citas, autenticar como A,
    # verificar que la respuesta no contiene id_medico de B
    ...
```

#### Property Test 2 — Filtrado de citas del día

```python
# Feature: dashboard-medico-interactivo, Property 2: Filtrado correcto de citas del día
@given(fechas=st.lists(fecha_strategy(), min_size=1, max_size=30))
@settings(max_examples=100)
def test_citas_hoy_only_today(fechas):
    # Crear citas con las fechas generadas, verificar que solo
    # retorna las que coinciden con date.today()
    ...
```

#### Property Test 3 — Ordenamiento descendente de historiales

```python
# Feature: dashboard-medico-interactivo, Property 3: Ordenamiento descendente
@given(n_historiales=st.integers(min_value=1, max_value=50))
@settings(max_examples=100)
def test_historiales_ordenados_desc(n_historiales):
    # Crear N historiales con fechas aleatorias, verificar que
    # fecha[i] >= fecha[i+1] para todo i en la respuesta
    ...
```

#### Property Test 4 — Unicidad de pacientes

```python
# Feature: dashboard-medico-interactivo, Property 4: Unicidad de pacientes
@given(
    pacientes=st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=30)
)
@settings(max_examples=100)
def test_pacientes_unicos(pacientes):
    # Crear citas referenciando la lista de pacientes (con duplicados),
    # verificar que la lista construida en JS/endpoint no repite IDs
    ...
```

### Pruebas de integración (Selenium / Playwright — opcional)

- Verificar que al hacer clic en cada stat-card el modal correcto tiene clase
  `show`.
- Verificar que el modal muestra `m-loading` durante la carga y luego el
  contenido.
- Verificar que doble clic no genera peticiones duplicadas.

### Checklist de revisión manual

- [ ] Las 4 stat-cards muestran cursor `pointer` al hover.
- [ ] Los modales abren y cierran con `×`, clic en overlay y botón Cerrar.
- [ ] El modal de Pacientes Atendidos reutiliza `abrirPaciente` sin romper el
  flujo de consulta.
- [ ] El modal de Mis Historiales reutiliza `verDetalleHistorial`.
- [ ] Con 0 registros se muestra el estado vacío en todos los modales.
- [ ] En móvil (< 640px) los modales son scrollables.
