from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SavedList, SavedListItem
from .serializers import (
    SavedListSerializer,
    SavedListDetailSerializer,
    SavedListItemSerializer
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
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)

        saved_list = serializer.save()

        return Response(
            SavedListSerializer(saved_list).data,
            status=status.HTTP_201_CREATED
        )


class SavedListDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return (
            SavedList.objects
            .filter(
                id=pk,
                user=request.user
            )
            .prefetch_related("items")
            .first()
        )

    def get(self, request, pk):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail": "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SavedListDetailSerializer(
            saved_list
        )

        return Response(
            serializer.data
        )

    def put(self, request, pk):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail": "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SavedListSerializer(
            saved_list,
            data=request.data,
            context={
                "request": request
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_list = serializer.save()

        return Response(
            SavedListSerializer(
                updated_list
            ).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        saved_list = self.get_object(
            request,
            pk
        )

        if not saved_list:
            return Response(
                {
                    "detail": "Liste nicht gefunden."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        saved_list.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class SavedListItemDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, list_id, item_id):
        return SavedListItem.objects.filter(
            id=item_id,
            saved_list_id=list_id,
            saved_list__user=request.user
        ).first()

    def put(self, request, list_id, item_id):
        item = self.get_object(
            request,
            list_id,
            item_id
        )

        if not item:
            return Response(
                {"detail": "Produkt nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SavedListItemSerializer(
            item,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, list_id, item_id):
        item = self.get_object(
            request,
            list_id,
            item_id
        )

        if not item:
            return Response(
                {"detail": "Produkt nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )