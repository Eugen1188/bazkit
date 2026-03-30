from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserRegisterSerializer


class RegisterUserView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
        )

        return Response(status=status.HTTP_201_CREATED)