from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

import webdna.util.server as server
from ..responses import *
from ..serializers import *


# URL: /api/users/
# Data: None
class UserView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        if request.user.is_superuser:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return ObjectResponse.make(obj=serializer.data)
        else:
            return PermissionDeniedResponse.make()


# URL: /api/users/login
# Data: in request body
class LoginView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        serialized_body = LoginSerializer(data=request.data)
        if serialized_body.is_valid():
            user_serializer = UserSerializer(serialized_body.fetched_user)
            return AuthenticationResponse.make(user_serializer.data)
        else:
            return ErrorResponse.make(status=status.HTTP_400_BAD_REQUEST, errors=serialized_body.errors)


# URL: /api/users/register
# Data: in request body
class RegistrationView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        serialized_body = RegistrationSerializer(data=request.data)
        if serialized_body.is_valid():
            created_user = serialized_body.save()
            serialized_user = UserSerializer(created_user)
            user_id = str(created_user.id)
            scripts_folder_path = server.get_user_scripts_folder_path(user_id)
            os.makedirs(scripts_folder_path, exist_ok=True)
            return RegistrationResponse.make(serialized_user.data)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)
