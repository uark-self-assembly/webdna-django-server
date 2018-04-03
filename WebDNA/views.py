from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import *
from .responses import *
from .tasks import *
import os
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
        job = serialized_body.fetched_job
        if job is None:
            job = serialized_body.create(serialized_body.validated_data)

        proj_path = "server-data/server-projects/" + serialized_body.validated_data['project_id']

        if os.path.isdir(proj_path) and os.path.isfile(proj_path+"/input.txt"):
            execute_sim.delay(job.id, job.project_id, proj_path)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serialized_body.errors, status=status.HTTP_400_BAD_REQUEST)


# /api/checkstatus
@api_view(['POST'])
def check_status(request):
    serialized_body = CheckStatusSerializer(data=request.data)
    if serialized_body.is_valid():
        path = "server-data/server-projects/" + str(serialized_body.validated_data['project_id'])
        running = True

        if serialized_body.fetched_job.finish_time is not None:
            running = False

        if os.path.isfile(path + '/stdout.log'):
            with open(path + '/stdout.log', 'r') as log:
                log_string = log.read()
        else:
            log_string = ''

        response_data = {'running': running, 'log': log_string}
        return JsonResponse(data=response_data, status=status.HTTP_200_OK)
    else:
        return Response(serialized_body.errors, status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def celery_test(request):
    test.delay()
    return TestResponse.make()

