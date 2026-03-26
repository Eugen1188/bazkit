from rest_framework import generics
from .serializers import SavedListSerializer
from rest_framework.permissions import IsAuthenticated
from .models import SavedList

class CreateList(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SavedListSerializer
    def get_queryset(self):
        return SavedList.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)