import logging
import traceback


class OperationalIssueHandler(logging.Handler):
    def emit(self, record):
        if record.name.startswith("monitoring"):
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
