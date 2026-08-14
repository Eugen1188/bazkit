from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SavedList
from .serializers import (
    SavedListSerializer,
    SavedListDetailSerializer,
)


class SavedListListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved_lists = (
            SavedList.objects
            .filter(user=request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        serializer = SavedListSerializer(
            saved_lists,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = SavedListSerializer(
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        saved_list = serializer.save()

        return Response(
            SavedListSerializer(
                saved_list
            ).data,
            status=status.HTTP_201_CREATED
        )