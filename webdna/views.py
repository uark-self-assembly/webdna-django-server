import shutil

from django.http import HttpResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

import webdna.tasks as tasks
import webdna.util.file as file_util
import webdna.util.project as project_util
import webdna.util.server as server
from webdna.defaults import ProjectFile, AnalysisFile
from webdna_django_server.celery import app
from .responses import *
from .serializers import *


# /api/users
class UserView(APIView):

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return ObjectResponse.make(obj=serializer.data)


# /api/file/upload
class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def put(self, request):
        file_obj = request.data['file']
        project_id = request.data['id']
        file_name = request.data['type']  # Any kind of file in project to edit

        new_file_path = server.get_project_file(project_id, file_name)

        if os.path.isfile(new_file_path):
            os.remove(new_file_path)

        new_file = open(file=new_file_path, mode='wb')
        for line in file_obj.readlines():
            new_file.write(line)
        new_file.close()

        return ErrorResponse.make(status=status.HTTP_204_NO_CONTENT)


# api/scripts/upload
class ScriptUploadView(APIView):
    parser_classes = (MultiPartParser,)

    # update to add script file to Script table
    def put(self, request):
        serialized_body = ScriptUploadSerializer(data=request.data)
        if serialized_body.is_valid():
            file_obj = serialized_body.validated_data['file']
            user_id = serialized_body.validated_data['user']
            script_name = serialized_body.validated_data['file_name']

            new_script_file_path = server.get_user_script(user_id, script_name)

            if os.path.isfile(new_script_file_path):
                os.remove(new_script_file_path)

            new_script_file = open(file=new_script_file_path, mode='wb')
            for line in file_obj.readlines():
                new_script_file.write(line)
            new_script_file.close()

            serialized_body.create(serialized_body.validated_data)
            return ErrorResponse.make(status=status.HTTP_204_NO_CONTENT)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)


class ProjectList(generics.CreateAPIView, generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def post(self, request, *args, **kwargs):
        response = generics.CreateAPIView.post(self, request, args, kwargs)
        fetched_projects = Project.objects.all().filter(id=response.data['id'])
        project_id = fetched_projects[0].id

        project_folder_path = server.get_analysis_folder_path(project_id)
        os.makedirs(project_folder_path, exist_ok=True)
        return ObjectResponse.make(response=response)

    def get(self, request, *args, **kwargs):
        response = generics.ListAPIView.get(self, request, args, kwargs)
        return ObjectResponse.make(response=response)


class ScriptList(generics.CreateAPIView, generics.ListAPIView):
        queryset = Script.objects.all()
        serializer_class = ScriptSerializer

        def post(self, request, *args, **kwargs):
            pass

        def get(self, request, *args, **kwargs):
            response = generics.ListAPIView.get(self, request, args, kwargs)
            return ObjectResponse.make(response=response)


# /api/projects
class ProjectView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'id'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        response = generics.RetrieveUpdateDestroyAPIView.get(self, request, args, kwargs)
        return ObjectResponse.make(response=response)

    def put(self, request, *args, **kwargs):
        response = generics.RetrieveUpdateDestroyAPIView.put(self, request, args, kwargs)
        return ObjectResponse.make(response=response)

    def delete(self, request, *args, **kwargs):
        project = self.queryset.filter(id=kwargs['id'])

        if not project:
            return ErrorResponse.make(message=PROJECT_NOT_FOUND)

        project_id = kwargs['id']
        project_folder_path = server.get_project_folder_path(project_id)
        jobs = Job.objects.filter(project_id=project_id)

        for j in jobs:
            if j.finish_time is None:
                app.control.revoke(j.process_name, terminate=True)

        shutil.rmtree(project_folder_path, ignore_errors=True)

        response = generics.RetrieveUpdateDestroyAPIView.delete(self, request, args, kwargs)
        return ObjectResponse.make(response=response)


# /api/login
@api_view(['POST'])
def login(request):
    serialized_body = LoginSerializer(data=request.data)
    if serialized_body.is_valid():
        user_serializer = UserSerializer(instance=serialized_body.fetched_user)
        return AuthenticationResponse.make(user_serializer.data)
    else:
        return ErrorResponse.make(status=status.HTTP_400_BAD_REQUEST, errors=serialized_body.errors)


# /api/register
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


# /api/execute
@api_view(['POST'])
def execute(request):
    serialized_body = ExecutionSerializer(data=request.data)
    if serialized_body.is_valid():
        job = serialized_body.fetched_job
        if job is None:
            job = serialized_body.create(serialized_body.validated_data)

        project_id = serialized_body.validated_data['project_id']
        should_regenerate = serialized_body.validated_data['should_regenerate']
        fetched_project = Project.objects.all().filter(id=project_id)
        user_id = fetched_project[0].user_id
        project_folder_path = server.get_project_folder_path(project_id)

        input_file = server.get_project_file(project_id, ProjectFile.INPUT)
        sequence_file = server.get_project_file(project_id, ProjectFile.SEQUENCE)
        generated_dat = server.get_project_file(project_id, ProjectFile.GENERATED_DAT)
        generated_top = server.get_project_file(project_id, ProjectFile.GENERATED_TOP)

        if os.path.isdir(project_folder_path):
            is_project_executable = False

            if should_regenerate and os.path.isfile(sequence_file):
                is_project_executable = True
            else:
                if os.path.isfile(generated_dat) and os.path.isfile(generated_top):
                    is_project_executable = True

            if not os.path.isfile(input_file):
                is_project_executable = False

            if is_project_executable:
                tasks.execute_sim.delay(job.id, job.project_id, user_id, should_regenerate)
                return ExecutionResponse.make()
            else:
                return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


@api_view(['GET'])
def check_running(request):
    serialized_body = CheckStatusSerializer(data=request.query_params)
    if serialized_body.is_valid():
        running = serialized_body.fetched_job.finish_time is None
        response_data = {'running': running}
        return ObjectResponse.make(response_data)
    else:
        response_data = {'running': False}
        return ObjectResponse.make(response_data)


# /api/checkstatus
@api_view(['POST'])
def check_output(request):
    serialized_body = CheckStatusSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        running = serialized_body.fetched_job.finish_time is None

        stdout_file = server.get_project_file(project_id, ProjectFile.STDOUT)
        if os.path.isfile(stdout_file):
            stdout_string = file_util.get_file_contents_as_string(stdout_file)
        else:
            stdout_string = ''

        log_file = server.get_project_file(project_id, ProjectFile.LOG_DAT)
        if os.path.isfile(log_file):
            log_string = file_util.get_file_contents_as_string(log_file)
        else:
            log_string = ''

        response_data = {'running': running, 'log': log_string, 'stdout': stdout_string}
        return ObjectResponse.make(response_data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/applysettings
@api_view(['POST'])
def set_project_settings(request):
    serialized_body = ProjectSettingsSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']

        input_file_status = file_util.generate_input_file(project_id, serialized_body.validated_data)
        if input_file_status == MISSING_PROJECT_FILES:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)

        return DefaultResponse.make(status.HTTP_201_CREATED)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/getsettings
@api_view(['POST'])
def get_project_settings(request):
    serialized_body = ProjectExistenceSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']

        input_data = file_util.parse_input_file(project_id)
        if input_data == MISSING_PROJECT_FILES:
            return ErrorResponse.make(status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)

        return ObjectResponse.make(obj=input_data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/file/getprojectfile
@api_view(['GET'])
def get_project_file(request):
    serialized_body = FileSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        file_name = serialized_body.validated_data['file_name']
        file_path = server.get_project_file(project_id, file_name)
        return file_util.get_file_contents_as_string(file_path)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/trajectory
@api_view(['GET'])
def fetch_traj(request):
    serialized_body = GetPDBSerializer(data=request.query_params)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']

        if serialized_body.fetched_job.finish_time is None:
            trajectory_file = server.get_project_file(project_id, ProjectFile.TRAJECTORY_DAT)
            top_file = server.get_project_file(project_id, ProjectFile.GENERATED_TOP)
            if os.path.isfile(trajectory_file) and os.path.isfile(top_file):
                project_util.generate_sim_files(project_id)
            else:
                return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/projects/zipdownload
@api_view(['GET'])
def project_zip(request):
    serialized_body = ProjectExistenceSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']

        project_util.zip_project(project_id)
        project_zip_file_path = server.get_project_file(project_id, ProjectFile.PROJECT_ZIP)
        with open(project_zip_file_path, 'rb') as archive_file:
            response = HttpResponse(archive_file, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="project.zip"'
            archive_file.close()
        return response
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


@api_view(['GET'])
def get_user_log(request):
    serialized_body = UserOutputRequestSerializer(data=request.query_params)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        file_path = server.get_analysis_file_path(project_id, AnalysisFile.LOG)

        if os.path.isfile(file_path):
            with open(file_path, 'rb') as output_file:
                response = output_file.readlines()

            return ObjectResponse.make(obj=response)
        else:
            return ErrorResponse.make(status=status.HTTP_404_NOT_FOUND,
                                      message='analysis.log does not exist for given project')
    else:
        return ErrorResponse.make(status=status.HTTP_400_BAD_REQUEST, message=PROJECT_NOT_FOUND)


@api_view(['POST'])
def stop_execution(request):
    serialized_body = TerminateSerializer(data=request.data)
    if serialized_body.is_valid():
        job = serialized_body.fetched_job
        app.control.revoke(job.process_name, terminate=True)
        job.delete()
        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


@api_view(['POST'])
def set_scriptchain(request):
    serialized_body = ScriptChainSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        script_chain_file_path = server.get_project_file(project_id, ProjectFile.SCRIPT_CHAIN)
        script_list = serialized_body.validated_data['script_list']

        with open(script_chain_file_path, 'w') as script_chain:
            script_chain.write(script_list)

        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


@api_view(['POST'])
def run_analysis_scripts(request):
    serialized_body = RunAnalysisSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        user_id = serialized_body.fetched_project.user_id

        tasks.execute_output_analysis.delay(project_id, user_id)
        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


@api_view(['DELETE'])
def delete_script(request):
    serialized_body = ScriptDeleteSerializer(data=request.query_params)
    if serialized_body.is_valid():
        serialized_body.fetched_script.delete()
        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


@api_view(['GET'])
def fetch_script_chain(request):
    serialized_body = ScriptChainRequestSerializer(data=request.query_params)
    if serialized_body.is_valid():
        project_id = str(serialized_body.project_id)
        script_chain_file_path = server.get_project_file(project_id, ProjectFile.SCRIPT_CHAIN)
        with open(script_chain_file_path, 'rb') as script_chain:
            response = script_chain.readlines()

        return ObjectResponse.make(obj=response)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)
