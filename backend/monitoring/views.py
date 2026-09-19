from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import report_issue
from .throttles import BrowserErrorThrottle


class BrowserErrorView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [BrowserErrorThrottle]

    def post(self, request):
        message = str(request.data.get("message", "")).strip()
        if not message:
            return Response(
                {"message": ["Eine Fehlermeldung ist erforderlich."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report_issue(
            source="browser",
            message=message,
            details={
                "type": str(request.data.get("type", "BrowserError"))[:100],
                "stack": str(request.data.get("stack", ""))[:4000],
                "path": str(request.data.get("path", ""))[:500],
                "release": str(request.data.get("release", ""))[:100],
                "user_agent": str(request.headers.get("User-Agent", ""))[:500],
            },
        )
        return Response(status=status.HTTP_202_ACCEPTED)
