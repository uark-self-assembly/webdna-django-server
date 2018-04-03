from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import *
from .responses import *
from .tasks import *
import os
from pprint import pprint

from rest_framework import mixins
from rest_framework import generics
from rest_framework.parsers import MultiPartParser

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


class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def put(self, request, filename, format=None):
        file_obj = request.data['file']
        project_id = request.data['id']
        file_name = request.data['type']  # 'sequence.txt', 'seq_dep.txt', or 'external_forces.txt'
        views_file_path = os.path.dirname(os.path.realpath(__file__))
        new_file_path = views_file_path + r'/../server-data/server-projects/' + project_id + r'/' + file_name

        new_file = open(file=new_file_path, mode='w')
        for line in file_obj.readlines():
            new_file.write(line)
        new_file.close()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectList(generics.CreateAPIView, generics.ListAPIView):
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
@api_view(['POST'])
def execute(request):
    serialized_body = ExecutionSerializer(data=request.data)
    if serialized_body.is_valid():
        proj_path = "server-data/server-projects/" + serialized_body.validated_data['id']
        if os.path.isdir(proj_path) and os.path.isfile(proj_path+"/input.txt"):
            serialized_body.fetched_project.job_running = True
            serialized_body.fetched_project.save(update_fields=['job_running'])
            execute_sim.delay(serialized_body.validated_data['id'], proj_path)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serialized_body.errors, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(['GET'])
def celery_test(request):
    test.delay()
    return TestResponse.make()

