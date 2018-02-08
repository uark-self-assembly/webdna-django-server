from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .models import *
from .serializers import *
from .responses import *
from .messages import *


# /api/users
class UserList(APIView):

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


# /api/projects
class ProjectList(APIView):

    def get(self, request):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


# /api/login
@api_view(['POST'])
def login(request):
    serialized_body = LoginSerializer(data=request.data)
    if not serialized_body.is_valid():
        return ErrorResponse.make(status=status.HTTP_400_BAD_REQUEST, message=INVALID_BODY)

    login_body = serialized_body.data

    # find user with supplied username
    found_user = User.objects.get(username=login_body['username'])
    print(found_user)

    serializer = UserSerializer(data=found_user)

    return ObjectResponse.make(serializer.data)
