import io
from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


# =========================================================================
# CORREO
# =========================================================================

def enviar_confirmacion_cita(paciente, cita):
    """
    Envía un correo de confirmación de cita al paciente usando
    la configuración definida en settings.py.
    """
    subject = f'Confirmación de Cita - {cita.cita}'
    to = [paciente.correo]
    from_email = settings.DEFAULT_FROM_EMAIL

    context = {'paciente': paciente, 'cita': cita}
    html_content = render_to_string('emails/confirmacion_cita.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        print(f"Correo enviado exitosamente a {paciente.correo}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


# =========================================================================
# PALETA DE COLORES PARA REPORTES
# =========================================================================

COLOR_HEADER_BG  = colors.HexColor('#0d1b2a')   # Azul muy oscuro
COLOR_HEADER_FG  = colors.white
COLOR_ROW_ODD    = colors.HexColor('#f0f4f8')   # Gris muy claro
COLOR_ROW_EVEN   = colors.white
COLOR_ACCENT     = colors.HexColor('#00a3c8')   # Cyan acento
COLOR_BORDER     = colors.HexColor('#ccd6e0')


# =========================================================================
# HELPERS INTERNOS
# =========================================================================

def _build_pdf_table(df: pd.DataFrame, title: str, page_size=A4) -> bytes:
    """
    Convierte un DataFrame en un PDF con diseño limpio usando ReportLab.
    Retorna bytes del PDF listo para servir.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=COLOR_HEADER_BG,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    sub_style = ParagraphStyle(
        'ReportSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#5a7184'),
        spaceAfter=14,
        alignment=TA_LEFT,
    )
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
    )

    elements = []

    # Encabezado del documento
    elements.append(Paragraph(f"CitaYa — {title}", title_style))
    elements.append(Paragraph(
        f"Generado el {date.today().strftime('%d/%m/%Y')}  ·  {len(df)} registro(s)",
        sub_style
    ))

    # Preparar datos de la tabla
    headers = list(df.columns)
    data_rows = [headers]

    for _, row in df.iterrows():
        data_rows.append([
            Paragraph(str(val) if val is not None else '', cell_style)
            for val in row.values
        ])

    # Calcular anchos de columna automáticamente
    page_width = page_size[0] - 3 * cm
    col_width = page_width / len(headers)
    col_widths = [col_width] * len(headers)

    table = Table(data_rows, colWidths=col_widths, repeatRows=1)

    row_count = len(data_rows)

    # Estilos base
    table_style_cmds = [
        # Encabezado
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_HEADER_BG),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOR_HEADER_FG),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  8),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('VALIGN',        (0, 0), (-1, 0),  'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  10),
        ('TOPPADDING',    (0, 0), (-1, 0),  10),

        # Celdas de datos
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('VALIGN',        (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),

        # Bordes
        ('LINEBELOW',     (0, 0), (-1, 0),  1.5, COLOR_ACCENT),
        ('LINEBELOW',     (0, 1), (-1, -1), 0.5, COLOR_BORDER),
        ('LINEBEFORE',    (0, 0), (0, -1),  0.5, COLOR_BORDER),
        ('LINEAFTER',     (-1, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]

    # Filas alternadas
    for i in range(1, row_count):
        bg = COLOR_ROW_ODD if i % 2 == 1 else COLOR_ROW_EVEN
        table_style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

    table.setStyle(TableStyle(table_style_cmds))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def _queryset_to_df(queryset, fields: list, rename: dict = None) -> pd.DataFrame:
    """
    Convierte un QuerySet en un DataFrame de Pandas.
    - fields: lista de strings con los nombres de campo (soporta doble guion bajo para FK)
    - rename: dict para renombrar columnas { 'campo_original': 'Nombre Bonito' }
    """
    records = list(queryset.values(*fields))
    df = pd.DataFrame(records) if records else pd.DataFrame(columns=fields)
    if rename:
        df = df.rename(columns=rename)
    return df


# =========================================================================
# GENERADORES PÚBLICOS — uno por entidad
# =========================================================================

# ── ADMINISTRADORES ───────────────────────────────────────────────────────

def generar_df_administradores(queryset) -> pd.DataFrame:
    fields = ['id_admin', 'tipo_doc', 'numero_doc', 'nombre', 'apellido',
              'genero', 'telefono', 'correo', 'estado']
    rename = {
        'id_admin':   'ID',
        'tipo_doc':   'Tipo Doc',
        'numero_doc': 'Núm. Doc',
        'nombre':     'Nombre',
        'apellido':   'Apellido',
        'genero':     'Género',
        'telefono':   'Teléfono',
        'correo':     'Correo',
        'estado':     'Estado',
    }
    df = _queryset_to_df(queryset, fields, rename)
    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].map({True: 'Activo', False: 'Inactivo'})
    return df


def generar_pdf_administradores(queryset) -> bytes:
    df = generar_df_administradores(queryset)
    return _build_pdf_table(df, "Reporte de Administradores")


def generar_excel_administradores(queryset) -> bytes:
    df = generar_df_administradores(queryset)
    return _df_to_excel(df, "Administradores")


# ── MÉDICOS ───────────────────────────────────────────────────────────────

def generar_df_medicos(queryset) -> pd.DataFrame:
    fields = ['id_medico', 'tipo_doc', 'numero_doc', 'nombre', 'apellido',
              'genero', 'especialidad', 'telefono', 'correo', 'estado']
    rename = {
        'id_medico':    'ID',
        'tipo_doc':     'Tipo Doc',
        'numero_doc':   'Núm. Doc',
        'nombre':       'Nombre',
        'apellido':     'Apellido',
        'genero':       'Género',
        'especialidad': 'Especialidad',
        'telefono':     'Teléfono',
        'correo':       'Correo',
        'estado':       'Estado',
    }
    df = _queryset_to_df(queryset, fields, rename)
    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].map({True: 'Activo', False: 'Inactivo'})
    return df


def generar_pdf_medicos(queryset) -> bytes:
    df = generar_df_medicos(queryset)
    return _build_pdf_table(df, "Reporte de Médicos", page_size=landscape(A4))


def generar_excel_medicos(queryset) -> bytes:
    df = generar_df_medicos(queryset)
    return _df_to_excel(df, "Médicos")


# ── PACIENTES ─────────────────────────────────────────────────────────────

def generar_df_pacientes(queryset) -> pd.DataFrame:
    fields = ['id_paciente', 'tipo_doc', 'numero_doc', 'nombre', 'apellido',
              'genero', 'fecha_nacimiento', 'tipo_sangre', 'direccion',
              'telefono', 'correo', 'estado']
    rename = {
        'id_paciente':      'ID',
        'tipo_doc':         'Tipo Doc',
        'numero_doc':       'Núm. Doc',
        'nombre':           'Nombre',
        'apellido':         'Apellido',
        'genero':           'Género',
        'fecha_nacimiento': 'Nacimiento',
        'tipo_sangre':      'Sangre',
        'direccion':        'Dirección',
        'telefono':         'Teléfono',
        'correo':           'Correo',
        'estado':           'Estado',
    }
    df = _queryset_to_df(queryset, fields, rename)
    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].map({True: 'Activo', False: 'Inactivo'})
    return df


def generar_pdf_pacientes(queryset) -> bytes:
    df = generar_df_pacientes(queryset)
    return _build_pdf_table(df, "Reporte de Pacientes", page_size=landscape(A4))


def generar_excel_pacientes(queryset) -> bytes:
    df = generar_df_pacientes(queryset)
    return _df_to_excel(df, "Pacientes")


# ── AGENDAMIENTOS ─────────────────────────────────────────────────────────

def generar_df_agendamientos(queryset) -> pd.DataFrame:
    """
    Usa anotaciones para traer los nombres reales en lugar de IDs de FK.
    """
    from django.db.models import F, Value
    from django.db.models.functions import Concat

    qs = queryset.annotate(
        nombre_paciente=Concat(
            F('id_paciente__nombre'), Value(' '), F('id_paciente__apellido')
        ),
        nombre_medico=Concat(
            F('id_medico__nombre'), Value(' '), F('id_medico__apellido')
        ),
    )

    fields = ['id_agendamiento', 'cita', 'fecha', 'hora',
              'nombre_paciente', 'nombre_medico']
    rename = {
        'id_agendamiento': 'ID',
        'cita':            'Tipo de Cita',
        'fecha':           'Fecha',
        'hora':            'Hora',
        'nombre_paciente': 'Paciente',
        'nombre_medico':   'Médico',
    }
    df = _queryset_to_df(qs, fields, rename)

    # Formatear hora
    if 'Hora' in df.columns:
        df['Hora'] = df['Hora'].apply(
            lambda h: h.strftime('%H:%M') if hasattr(h, 'strftime') else str(h)
        )

    return df


def generar_pdf_agendamientos(queryset) -> bytes:
    df = generar_df_agendamientos(queryset)
    return _build_pdf_table(df, "Reporte de Agendamientos")


def generar_excel_agendamientos(queryset) -> bytes:
    df = generar_df_agendamientos(queryset)
    return _df_to_excel(df, "Agendamientos")


# ── HISTORIAL CLÍNICO ─────────────────────────────────────────────────────

def generar_df_historial(queryset) -> pd.DataFrame:
    from django.db.models import F, Value
    from django.db.models.functions import Concat

    qs = queryset.annotate(
        nombre_paciente=Concat(
            F('id_paciente__nombre'), Value(' '), F('id_paciente__apellido')
        ),
        nombre_medico=Concat(
            F('id_medico__nombre'), Value(' '), F('id_medico__apellido')
        ),
    )

    fields = ['id_historial', 'fecha_creacion', 'nombre_paciente',
              'nombre_medico', 'antecedentes']
    rename = {
        'id_historial':   'ID',
        'fecha_creacion': 'Fecha',
        'nombre_paciente':'Paciente',
        'nombre_medico':  'Médico Tratante',
        'antecedentes':   'Antecedentes',
    }
    return _queryset_to_df(qs, fields, rename)


def generar_pdf_historial(queryset) -> bytes:
    df = generar_df_historial(queryset)
    return _build_pdf_table(df, "Reporte de Historial Clínico")


def generar_excel_historial(queryset) -> bytes:
    df = generar_df_historial(queryset)
    return _df_to_excel(df, "Historial Clínico")


# =========================================================================
# HELPER EXCEL
# =========================================================================

def _df_to_excel(df: pd.DataFrame, sheet_name: str = 'Reporte') -> bytes:
    """
    Convierte un DataFrame en un archivo Excel (.xlsx) con formato limpio.
    Retorna bytes listos para servir.
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        wb = writer.book
        ws = writer.sheets[sheet_name]

        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        header_fill   = PatternFill("solid", fgColor="0D1B2A")
        header_font   = Font(bold=True, color="FFFFFF", size=10)
        odd_fill      = PatternFill("solid", fgColor="F0F4F8")
        even_fill     = PatternFill("solid", fgColor="FFFFFF")
        thin_border   = Border(
            left=Side(style='thin', color='CCD6E0'),
            right=Side(style='thin', color='CCD6E0'),
            top=Side(style='thin', color='CCD6E0'),
            bottom=Side(style='thin', color='CCD6E0'),
        )
        center_align  = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left_align    = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # Encabezados
        for col_idx, cell in enumerate(ws[1], start=1):
            cell.fill      = header_fill
            cell.font      = header_font
            cell.alignment = center_align
            cell.border    = thin_border

        # Filas de datos
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            fill = odd_fill if row_idx % 2 == 1 else even_fill
            for cell in row:
                cell.fill      = fill
                cell.alignment = left_align
                cell.border    = thin_border
                cell.font      = Font(size=9)

        # Ancho automático de columnas
        for col_idx, col in enumerate(ws.columns, start=1):
            max_len = 0
            col_letter = get_column_letter(col_idx)
            for cell in col:
                try:
                    if cell.value:
                        max_len = max(max_len, len(str(cell.value)))
                except Exception:
                    pass
            ws.column_dimensions[col_letter].width = min(max_len + 4, 45)

        # Fijar fila de encabezado
        ws.freeze_panes = 'A2'

    buffer.seek(0)
    return buffer.read()