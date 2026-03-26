from rest_framework import generics
from .serializers import SavedListSerializer
from rest_framework.permissions import IsAuthenticated
from .models import SavedList

class SavedListListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedList.objects.filter(user=self.request.user).prefetch_related('items')

    def perform_create(self, serializer):
        serializer.save()


class SavedListDetailView(generics.RetrieveAPIView):
    serializer_class = SavedListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedList.objects.filter(user=self.request.user).prefetch_related('items')
    
