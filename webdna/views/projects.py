import shutil
from enum import Enum

from django.http import HttpResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

import webdna.tasks as tasks
import webdna.util.file as file_util
import webdna.util.project as project_util
from webdna.defaults import ProjectFile
from webdna_django_server.celery import app
from ..responses import *
from ..serializers import *


# URL: api/projects/<uuid:project_id>/files/upload/
class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def put(self, request, *args, **kwargs):
        project_existence_serializer = ProjectExistenceSerializer(data=kwargs)
        if project_existence_serializer.is_valid():
            project_id = kwargs['project_id']
            file_obj = request.data['file']
            file_type_string = request.data['type']  # Any kind of file in project to edit

            try:
                file_type = FileType[file_type_string].value
            except KeyError:
                return ErrorResponse.make(
                    status=status.HTTP_400_BAD_REQUEST,
                    message='Invalid FileType: {}'.format(file_type_string))

            new_file_path = server.get_project_file(project_id, file_type)

            if os.path.isfile(new_file_path):
                os.remove(new_file_path)

            new_file = open(file=new_file_path, mode='wb')
            for line in file_obj.readlines():
                new_file.write(line)
            new_file.close()

            return DefaultResponse.make(status=status.HTTP_204_NO_CONTENT)
        else:
            return ErrorResponse.make(status=status.HTTP_404_NOT_FOUND)


# URL: /api/projects/
class ProjectList(generics.CreateAPIView, generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        response = generics.ListAPIView.get(self, request, args, kwargs)
        return ObjectResponse.make(response=response)

    def post(self, request, *args, **kwargs):
        response = generics.CreateAPIView.post(self, request, args, kwargs)
        fetched_projects = Project.objects.all().filter(id=response.data['id'])
        project_id = fetched_projects[0].id

        project_folder_path = server.get_analysis_folder_path(project_id)
        os.makedirs(project_folder_path, exist_ok=True)
        return ObjectResponse.make(response=response)


# URL: /api/projects/<uuid:project_id>/
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


# /api/projects/<uuid:id>/settings/
class SettingsView(generics.RetrieveUpdateAPIView):

    def get(self, request, *args, **kwargs):
        serialized_body = ProjectExistenceSerializer(data=kwargs)
        if serialized_body.is_valid():
            project_id = serialized_body.validated_data['project_id']

            input_data = file_util.parse_input_file(project_id)
            if input_data == MISSING_PROJECT_FILES:
                return ErrorResponse.make(status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)

            return ObjectResponse.make(obj=input_data)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)

    def put(self, request, *args, **kwargs):
        request.data['project_id'] = kwargs['project_id']

        project_settings_serializer = ProjectSettingsSerializer(data=request.data)
        if project_settings_serializer.is_valid():
            settings_data = project_settings_serializer.validated_data
            project_id = settings_data['project_id']
            input_file_status = file_util.generate_input_file(project_id, settings_data)

            if input_file_status == MISSING_PROJECT_FILES:
                return ErrorResponse.make(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=MISSING_PROJECT_FILES)

            return DefaultResponse.make(status.HTTP_201_CREATED)
        else:
            return ErrorResponse.make(errors=project_settings_serializer.errors)


# /api/projects/<uuid:id>/simulation/execute/
@api_view(['GET'])
def execute(request, *args, **kwargs):
    execution_data = {
        'project_id': kwargs['project_id'],
        'regenerate': request.query_params['regenerate']
    }

    serialized_body = ExecutionSerializer(data=execution_data)
    if serialized_body.is_valid():
        job = serialized_body.fetched_job
        if job is None:
            job = serialized_body.create(serialized_body.validated_data)

        project_id = serialized_body.validated_data['project_id']
        regenerate = serialized_body.validated_data['regenerate']
        fetched_project = Project.objects.all().filter(id=project_id)
        user_id = fetched_project[0].user_id
        project_folder_path = server.get_project_folder_path(project_id)

        input_file = server.get_project_file(project_id, ProjectFile.INPUT)
        sequence_file = server.get_project_file(project_id, ProjectFile.SEQUENCE)
        generated_dat = server.get_project_file(project_id, ProjectFile.GENERATED_DAT)
        generated_top = server.get_project_file(project_id, ProjectFile.GENERATED_TOP)

        if os.path.isdir(project_folder_path):
            is_project_executable = False

            if regenerate and os.path.isfile(sequence_file):
                is_project_executable = True
            else:
                if os.path.isfile(generated_dat) and os.path.isfile(generated_top):
                    is_project_executable = True

            if not os.path.isfile(input_file):
                is_project_executable = False

            if is_project_executable:
                tasks.execute_sim.delay(job.id, job.project_id, user_id, regenerate)
                return ExecutionResponse.make()
            else:
                return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:id>/simulation/terminate/
@api_view(['GET'])
def terminate(request, *args, **kwargs):
    serialized_body = TerminateSerializer(data=kwargs)
    if serialized_body.is_valid():
        job = serialized_body.fetched_job
        app.control.revoke(job.process_name, terminate=True)
        job.delete()
        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:id>/running-status/
@api_view(['GET'])
def get_running_status(request, *args, **kwargs):
    serialized_body = CheckStatusSerializer(data=kwargs)
    if serialized_body.is_valid():
        running = serialized_body.fetched_job.finish_time is None
        response_data = {'running': running}
        return ObjectResponse.make(response_data)
    else:
        response_data = {'running': False}
        return ObjectResponse.make(response_data)


# URL: /api/projects/<uuid:id>/current-output/
@api_view(['GET'])
def get_current_output(request, *args, **kwargs):
    serialized_body = CheckStatusSerializer(data=kwargs)
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


# URL: api/projects/<uuid:project_id>/files/download/<string:file_type>/
@api_view(['GET'])
def download_project_file(request, *args, **kwargs):
    serialized_body = FileSerializer(data=kwargs)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        project_file = serialized_body.project_file
        project_file_path = server.get_project_file(project_id, project_file)
        return file_util.get_file_contents_as_string(project_file_path)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:project_id>/files/trajectory/
@api_view(['GET'])
def generate_visualization(request, *args, **kwargs):
    serialized_body = GetPDBSerializer(data=kwargs)
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


# URL: api/projects/<uuid:project_id>/files/zip/
@api_view(['GET'])
def project_zip(request, *args, **kwargs):
    serialized_body = ProjectExistenceSerializer(data=kwargs)
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
