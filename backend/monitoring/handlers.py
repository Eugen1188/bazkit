import logging
import traceback

from django.core.exceptions import DisallowedHost


class OperationalIssueHandler(logging.Handler):
    @staticmethod
    def _is_rejected_host_probe(record):
        if record.name == "django.security.DisallowedHost":
            return True

        if not record.exc_info:
            return False

        exception_type = record.exc_info[0]
        try:
            return issubclass(exception_type, DisallowedHost)
        except TypeError:
            return False

    def emit(self, record):
        # Django correctly rejects requests with forged Host headers. Public
        # servers receive these automated probes constantly, so they are not
        # operational incidents and must not trigger alert e-mails.
        if (
            record.name.startswith("monitoring")
            or self._is_rejected_host_probe(record)
        ):
            return
        try:
            from .services import report_issue

            details = {
                "logger": record.name,
                "module": record.module,
                "line": record.lineno,
            }
            if record.exc_info:
                details["type"] = record.exc_info[0].__name__
                details["stack"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )[-4000:]
            report_issue(
                source=getattr(record, "monitoring_source", "backend"),
                level="critical" if record.levelno >= logging.CRITICAL else "error",
                message=record.getMessage(),
                details=details,
            )
        except Exception:
            self.handleError(record)
