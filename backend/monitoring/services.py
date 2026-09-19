import hashlib
import json
import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import OperationalIssue


_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization|token|password|secret|cookie)(\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/-]+=*"),
)


def _clean_text(value, limit):
    text = str(value or "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}[entfernt]" if match.lastindex == 2 else "Bearer [entfernt]", text)
    return text[:limit]


def _clean_details(details):
    try:
        serializable = json.loads(json.dumps(details or {}, default=str))
    except (TypeError, ValueError):
        serializable = {"context": _clean_text(details, 4000)}
    cleaned = {}
    for key, value in serializable.items():
        safe_key = _clean_text(key, 100)
        cleaned[safe_key] = _clean_text(value, 4000) if isinstance(value, str) else value
    return cleaned


def report_issue(*, source, message, level="error", details=None):
    """Persist and optionally alert for an operational issue without breaking a request."""
    if not getattr(settings, "ERROR_MONITORING_ENABLED", True):
        return None

    allowed_sources = {choice for choice, _label in OperationalIssue.Source.choices}
    safe_source = source if source in allowed_sources else OperationalIssue.Source.BACKEND
    safe_level = level if level in {"error", "critical"} else "error"
    safe_message = _clean_text(message, 500) or "Unbekannter Fehler"
    safe_details = _clean_details(details)
    identity = json.dumps(
        {
            "source": safe_source,
            "message": safe_message,
            "type": safe_details.get("type", ""),
            "path": safe_details.get("path", ""),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    fingerprint = hashlib.sha256(identity.encode("utf-8")).hexdigest()

    try:
        now = timezone.now()
        with transaction.atomic():
            issue, created = OperationalIssue.objects.select_for_update().get_or_create(
                fingerprint=fingerprint,
                defaults={
                    "source": safe_source,
                    "level": safe_level,
                    "message": safe_message,
                    "details": safe_details,
                },
            )
            if not created:
                issue.source = safe_source
                issue.level = safe_level
                issue.message = safe_message
                issue.details = safe_details
                issue.occurrences += 1
                issue.resolved_at = None

            cooldown = timedelta(
                minutes=max(1, getattr(settings, "ERROR_ALERT_COOLDOWN_MINUTES", 30))
            )
            source_alert_is_cooling_down = OperationalIssue.objects.filter(
                source=safe_source,
                last_alerted_at__gte=now - cooldown,
            ).exclude(pk=issue.pk).exists()
            should_alert = (
                bool(getattr(settings, "ERROR_ALERT_EMAIL", ""))
                and not source_alert_is_cooling_down
                and (issue.last_alerted_at is None or now - issue.last_alerted_at >= cooldown)
            )
            if should_alert:
                issue.last_alerted_at = now
            issue.save()

        if should_alert:
            try:
                send_mail(
                    subject=f"[Bazkit] {issue.get_source_display()}-Fehler",
                    message=(
                        f"Quelle: {issue.get_source_display()}\n"
                        f"Stufe: {issue.get_level_display()}\n"
                        f"Meldung: {issue.message}\n"
                        f"Vorkommen: {issue.occurrences}\n"
                        f"Details: {json.dumps(issue.details, ensure_ascii=False, indent=2)}"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[settings.ERROR_ALERT_EMAIL],
                    fail_silently=False,
                )
            except Exception as error:
                issue.details = {
                    **issue.details,
                    "alert_delivery_error": _clean_text(error, 500),
                }
                issue.save(update_fields=["details"])
        return issue
    except Exception:
        # Monitoring must also be safe during migrations or database outages.
        return None
