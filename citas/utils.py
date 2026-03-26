from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def enviar_confirmacion_cita(paciente, cita):
    subject = f'Confirmación de Cita - {cita.cita}'
    from_email = 'tu_correo@gmail.com'
    to = [paciente.correo]

    # Pasamos los datos a la plantilla
    context = {
        'paciente': paciente,
        'cita': cita,
    }

    # Renderizamos el HTML
    html_content = render_to_string('emails/confirmacion_cita.html', context)
    text_content = strip_tags(html_content) # Versión en texto plano por si el gestor de correo no soporta HTML

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()