import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_password_reset_email(email: str, reset_token: str) -> None:
    """
    Send password reset email to user.

    Args:
        email: Recipient email address
        reset_token: JWT reset token
    """
    # Print token to stdout as requested
    print(f"Token de restablecimiento para {email}: {reset_token}")

    # Check if email is configured
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("Configuracion de correo no establecida. El correo no sera enviado.")
        return

    try:
        # Create reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM or settings.SMTP_USER
        msg['To'] = email
        msg['Subject'] = 'Restablece tu contraseña - Vehicle Check'

        # Email body in Spanish
        body = f"""Hola,

Recibimos una solicitud para restablecer tu contraseña en Vehicle Check.

Haz clic en el siguiente enlace para restablecer tu contraseña:
{reset_link}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

Saludos,
Equipo de Vehicle Check
"""

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Send email via SMTP
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Correo de restablecimiento enviado exitosamente a {email}")

    except smtplib.SMTPAuthenticationError:
        print(f"Error de autenticacion SMTP. Verifica SMTP_USER y SMTP_PASSWORD.")
    except smtplib.SMTPException as e:
        print(f"Error al enviar correo: {str(e)}")
    except Exception as e:
        print(f"Error inesperado al enviar correo: {str(e)}")
