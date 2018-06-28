from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView

import webdna.util.server as server
from ..responses import *
from ..serializers import *


class UserView(APIView):
    def get(self):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return ObjectResponse.make(obj=serializer.data)


@api_view(['POST'])
def login(request):
    serialized_body = LoginSerializer(data=request.data)
    if serialized_body.is_valid():
        user_serializer = UserSerializer(instance=serialized_body.fetched_user)
        return AuthenticationResponse.make(user_serializer.data)
    else:
        return ErrorResponse.make(status=status.HTTP_400_BAD_REQUEST, errors=serialized_body.errors)


@api_view(['POST'])
def register(request):
    serialized_body = RegistrationSerializer(data=request.data)
    if serialized_body.is_valid():
        user_serializer = UserSerializer(instance=serialized_body.save())
        user_id = str(user_serializer.data['id'])
        scripts_folder_path = server.get_user_scripts_folder_path(user_id)
        os.makedirs(scripts_folder_path, exist_ok=True)
        return RegistrationResponse.make(user_serializer.data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)