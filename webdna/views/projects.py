import shutil
import json
from distutils.dir_util import copy_tree

from django.http import HttpResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated

import webdna.tasks as tasks
import webdna.util.file as file_util
import webdna.util.project as project_util
from webdna.defaults import ProjectFile
from webdna_django_server.celery import app
from ..responses import *
from ..serializers import *
from ..util.jwt import *
from ..util.project import Generation, Payload, is_executable


# URL: api/projects/<uuid:project_id>/files/upload/
class FileUploadView(generics.GenericAPIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def put(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
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
    permission_classes = [IsAuthenticated, ]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(user_id=user.id)

    def create(self, request, *args, **kwargs):
        project_data = request.data
        project_data['user'] = request.user.id
        serializer = self.get_serializer(data=project_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        response = generics.ListAPIView.get(self, request, args, kwargs)
        for project in response.data:
            fetched_job = Job.objects.filter(project_id=project['id'])

            if fetched_job:
                job_serialized = JobSerializer(instance=fetched_job[0])
                project['job'] = job_serialized.data
            else:
                project['job'] = None
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
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    lookup_field = 'id'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        response = generics.RetrieveUpdateDestroyAPIView.get(self, request, args, kwargs)
        fetched_job = Job.objects.filter(project_id=response.data['id'])

        if fetched_job:
            job_serialized = JobSerializer(instance=fetched_job[0])
            response.data['job'] = job_serialized.data
        else:
            response.data['job'] = None

        return ObjectResponse.make(response=response)

    def put(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        response = generics.RetrieveUpdateDestroyAPIView.put(self, request, args, kwargs)
        return ObjectResponse.make(response=response)

    def delete(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        project = self.get_object()

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


# /api/projects/<uuid:project_id>/settings/
class SettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
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
        self.check_object_permissions(request, self.get_object())
        request.data['project_id'] = kwargs['project_id']

        project_settings_serializer = ProjectSettingsSerializer(data=request.data)
        if project_settings_serializer.is_valid():
            settings_data = project_settings_serializer.validated_data.copy()
            project_id = settings_data['project_id']
            settings_data.pop('generation_method', None)
            settings_data.pop('lattice_type', None)
            input_file_status = file_util.generate_input_file(project_id, settings_data)
            fetched_project = Project.objects.all().filter(id=project_id)[0]

            generation_info = project_util.Generation(
                method=project_settings_serializer.validated_data['generation_method'],
                arguments=project_settings_serializer.gen_args
            )

            json_settings = project_util.ProjectSettings(project_name=fetched_project.name, generation=generation_info)

            with open(server.get_project_file(project_id, ProjectFile.JSON), 'w') as json_file:
                json.dump(json_settings.serializable(), json_file)

            if input_file_status == MISSING_PROJECT_FILES:
                return ErrorResponse.make(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=MISSING_PROJECT_FILES)

            return DefaultResponse.make(status.HTTP_201_CREATED)
        else:
            return ErrorResponse.make(errors=project_settings_serializer.errors)


# /api/projects/<uuid:project_id>/simulation/execute/
class ExecutionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        regenerate = request.GET.get('regenerate', False)
        execution_data = {
            'project_id': kwargs['project_id'],
            'regenerate': regenerate
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

            with open(server.get_project_file(project_id, ProjectFile.JSON), 'r') as json_file:
                p = Payload(json_file)
                generation = Generation(dictionary=p.__dict__['gen'])

            if os.path.isdir(project_folder_path):
                if is_executable(project_id, regenerate, generation):
                    tasks.execute_sim.delay(job.id, project_id, user_id, regenerate, generation.__dict__)
                    return ExecutionResponse.make()
                else:
                    job.delete()
                    return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                              message='Unable to execute specified simulation')
            else:
                job.delete()
                return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                          message='Unable to execute specified simulation')
        else:
            return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:project_id>/simulation/terminate/
class TerminationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        serialized_body = TerminateSerializer(data=kwargs)
        if serialized_body.is_valid():
            job = serialized_body.fetched_job
            try:
                app.control.revoke(job.process_name, terminate=True)
            except ConnectionResetError as exception:
                print(exception)
            job.terminated = True
            job.finish_time = timezone.now()
            job.process_name = None
            job.save(update_fields=['process_name', 'terminated', 'finish_time'])
            return DefaultResponse.make()
        else:
            return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:project_id>/current-output/
class OutputView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
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
class DownloadProjectFileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        serialized_body = FileSerializer(data=kwargs)
        if serialized_body.is_valid():
            project_id = serialized_body.validated_data['project_id']
            project_file = serialized_body.project_file
            project_file_path = server.get_project_file(project_id, project_file)
            return file_util.get_file_contents_as_string(project_file_path)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:project_id>/files/trajectory/
class GenerateVisualizationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
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
class ProjectZipView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
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


# URL: api/projects/<uuid:project_id>/duplicate/
class DuplicateProjectView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner, ]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'project_id'

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        serialized_body = ProjectExistenceSerializer(data=kwargs)
        if serialized_body.is_valid():
            new_project = Project()
            new_project.name = 'Duplicate of ' + serialized_body.fetched_project.name
            new_project.user_id = serialized_body.fetched_project.user_id

            original_project_id = serialized_body.validated_data['project_id']
            original_project_folder_path = server.get_project_folder_path(original_project_id)
            duplicated_project_folder_path = server.get_project_folder_path(new_project.id)

            copy_tree(original_project_folder_path, duplicated_project_folder_path)

            new_project.save()

            project_serializer = ProjectSerializer(instance=new_project)
            return ObjectResponse.make(obj=project_serializer.data)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)
