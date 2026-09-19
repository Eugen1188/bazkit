import logging

from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import OperationalIssue


@override_settings(
    ERROR_MONITORING_ENABLED=True,
    ERROR_ALERT_EMAIL="betrieb@example.com",
    ERROR_ALERT_COOLDOWN_MINUTES=30,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class MonitoringTests(APITestCase):
    def test_browser_errors_are_sanitized_deduplicated_and_alerted_once(self):
        payload = {
            "message": "TypeError: kaputt token=geheim",
            "type": "TypeError",
            "stack": "password:offen\nbei app.js:10",
            "path": "/community/1",
        }

        first = self.client.post("/monitoring/browser-errors/", payload, format="json")
        second = self.client.post("/monitoring/browser-errors/", payload, format="json")
        third = self.client.post(
            "/monitoring/browser-errors/",
            {**payload, "message": "Ein weiterer Fehler"},
            format="json",
        )

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(third.status_code, 202)
        issue = OperationalIssue.objects.get(message__startswith="TypeError")
        self.assertEqual(issue.source, "browser")
        self.assertEqual(issue.occurrences, 2)
        self.assertNotIn("geheim", issue.message)
        self.assertNotIn("offen", issue.details["stack"])
        self.assertEqual(OperationalIssue.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 1)

    def test_error_log_is_recorded_with_email_source(self):
        handler = logging.getHandlerByName("operational_issues")
        record = logging.LogRecord(
            "users.views", logging.ERROR, __file__, 1,
            "E-Mail konnte nicht gesendet werden", (), None,
        )
        record.monitoring_source = "email"

        handler.emit(record)

        issue = OperationalIssue.objects.get()
        self.assertEqual(issue.source, "email")
        self.assertEqual(issue.message, "E-Mail konnte nicht gesendet werden")
