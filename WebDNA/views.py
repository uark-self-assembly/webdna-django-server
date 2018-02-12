from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import *
from .responses import *
from .messages import *
from .util.password_util import *
from django.http import HttpResponse, JsonResponse

# NOTE: It is best practice to keep all validation (field, class, etc.) in serializers.py
# A view should ideally call serializer validation and return responses based on the validation result
# Refer to .register for an example of a good view definition
# Refer to RegistrationSerializer in serializers.py and User in models.py
# for an example of how to implement custom and default field validation for objects


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
    if serialized_body.is_valid():
        user_serializer = UserSerializer(instance=serialized_body.fetched_user)
        return AuthenticationResponse.make(user_serializer.data)
    else:
        return Response(serialized_body.errors, status=status.HTTP_400_BAD_REQUEST)


# /api/register
@api_view(['POST'])
def register(request):
    serialized_body = RegistrationSerializer(data=request.data)
    if serialized_body.is_valid():
        user_serializer = UserSerializer(instance=serialized_body.save())
        return RegistrationResponse.make(user_serializer.data)
        # return JsonResponse(serialized_body.data, status=status.HTTP_201_CREATED)

    return Response(serialized_body.errors, status=status.HTTP_400_BAD_REQUEST)
