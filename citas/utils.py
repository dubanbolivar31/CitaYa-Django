from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def enviar_confirmacion_cita(paciente, cita):
    """
    Envía un correo de confirmación de cita al paciente usando 
    la configuración definida en settings.py.
    """
    
    subject = f'Confirmación de Cita - {cita.cita}'
    to = [paciente.correo]
    
    from_email = settings.DEFAULT_FROM_EMAIL 

    context = {
        'paciente': paciente,
        'cita': cita,
    }

    html_content = render_to_string('emails/confirmacion_cita.html', context)
    
    text_content = strip_tags(html_content) 

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        print(f"Correo enviado exitosamente a {paciente.correo}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")