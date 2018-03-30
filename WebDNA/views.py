from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import *
from .responses import *
from pprint import pprint

from rest_framework import mixins
from rest_framework import generics

# NOTE: It is best practice to keep all validation (field, class, etc.) in serializers.py
# A view should ideally call serializer validation and return responses based on the validation result
# Refer to .register for an example of a good view definition
# Refer to RegistrationSerializer in serializers.py and User in models.py
# for an example of how to implement custom and default field validation for objects


# /api/users
class UserView(APIView):

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class ProjectList(
        generics.CreateAPIView,
        generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


# /api/projects
class ProjectView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'id'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


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

    return Response(serialized_body.errors, status=status.HTTP_400_BAD_REQUEST)


# /api/execute
@api_view(['GET'])
def execute(request):
    return Response(status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def checkStatus(request):
    serialized_body = CheckStatusSerializer(data=request.data)
    if serialized_body.is_valid():
        pass
        # check_oxDNA()


# /api/update
@api_view(['GET'])
def output_console(request):
    return Response(template_name='output.html')
