from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode


def verification_url(token):
    query = urlencode({"token": str(token)})
    return f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?{query}"


def send_verification_email(user, recipient, *, email_change=False):
    url = verification_url(user.email_verification_token)
    display_name = user.first_name.strip() or "dort"
    escaped_name = escape(display_name)
    if email_change:
        subject = "Neue E-Mail-Adresse für bazkit bestätigen"
        intro = "du möchtest diese Adresse künftig für dein bazkit-Konto verwenden."
        action = "Neue E-Mail-Adresse bestätigen"
    else:
        subject = "Dein bazkit-Konto bestätigen"
        intro = "bestätige bitte deine E-Mail-Adresse, um dein bazkit-Konto freizuschalten."
        action = "E-Mail-Adresse bestätigen"

    text = (
        f"Hallo {display_name},\n\n"
        f"{intro}\n\n"
        f"{url}\n\n"
        f"Der Link ist {settings.EMAIL_VERIFICATION_TIMEOUT_HOURS} Stunden gültig. "
        "Falls du diese Änderung nicht angefordert hast, kannst du diese Nachricht ignorieren.\n\n"
        "Viele Grüße\nDein bazkit-Team"
    )
    html = f"""
      <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2a37">
        <h1 style="font-size:24px">Hallo {escaped_name},</h1>
        <p style="line-height:1.6">{intro}</p>
        <p style="margin:28px 0">
          <a href="{url}" style="display:inline-block;padding:13px 20px;border-radius:10px;background:#587664;color:#fff;text-decoration:none;font-weight:700">
            {action}
          </a>
        </p>
        <p style="line-height:1.6;color:#646464">Der Link ist {settings.EMAIL_VERIFICATION_TIMEOUT_HOURS} Stunden gültig.</p>
        <p style="line-height:1.6;color:#646464">Falls du diese Änderung nicht angefordert hast, kannst du diese Nachricht ignorieren.</p>
      </div>
    """
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach_alternative(html, "text/html")
    message.send(fail_silently=False)


def password_reset_url(user):
    query = urlencode({
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
    })
    return f"{settings.FRONTEND_URL.rstrip('/')}/passwort-zuruecksetzen?{query}"


def send_password_reset_email(user):
    url = password_reset_url(user)
    display_name = user.first_name.strip()
    greeting = f"Hallo {display_name}," if display_name else "Hallo,"
    escaped_greeting = escape(greeting)
    escaped_url = escape(url)
    text = (
        f"{greeting}\n\n"
        "du hast angefordert, dein bazkit-Passwort zurückzusetzen.\n\n"
        f"{url}\n\n"
        f"Der Link ist {settings.PASSWORD_RESET_TIMEOUT // 3600} Stunden gültig. "
        "Falls du das nicht angefordert hast, kannst du diese Nachricht ignorieren.\n\n"
        "Viele Grüße\nDein bazkit-Team"
    )
    html = f"""
      <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2a37">
        <h1 style="font-size:24px">{escaped_greeting}</h1>
        <p style="line-height:1.6">Du hast angefordert, dein bazkit-Passwort zurückzusetzen.</p>
        <p style="margin:28px 0">
          <a href="{escaped_url}" style="display:inline-block;padding:13px 20px;border-radius:10px;background:#587664;color:#fff;text-decoration:none;font-weight:700">
            Neues Passwort festlegen
          </a>
        </p>
        <p style="line-height:1.6;color:#646464">Der Link ist {settings.PASSWORD_RESET_TIMEOUT // 3600} Stunden gültig.</p>
        <p style="line-height:1.6;color:#646464">Falls du das nicht angefordert hast, kannst du diese Nachricht ignorieren.</p>
      </div>
    """
    message = EmailMultiAlternatives(
        subject="Bazkit-Passwort zurücksetzen",
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html, "text/html")
    message.send(fail_silently=False)
