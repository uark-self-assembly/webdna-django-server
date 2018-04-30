from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import *
from .responses import *
from .tasks import *
from rest_framework import status
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from WebDNA.util.oxDNA_util import *
import shutil
from webdna_server.celery import app

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
        return ObjectResponse.make(obj=serializer.data)


# /api/file/upload
class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def put(self, request):
        file_obj = request.data['file']
        project_id = request.data['id']
        file_name = request.data['type']  # Any kind of file in project to edit

        new_file_path = os.path.join('server-data', 'server-projects', str(project_id), str(file_name))

        if os.path.isfile(new_file_path):
            os.remove(new_file_path)

        new_file = open(file=new_file_path, mode='wb')
        for line in file_obj.readlines():
            new_file.write(line)
        new_file.close()

        return ErrorResponse.make(status=status.HTTP_204_NO_CONTENT)


# api/script/upload
class ScriptUploadView(APIView):
    parser_classes = (MultiPartParser,)

    # update to add script file to Script table
    def put(self, request):
        serialized_body = ScriptUploadSerializer(data=request.data)
        if serialized_body.is_valid():
            file_obj = serialized_body.validated_data['file']
            user_id = serialized_body.validated_data['user']
            script_name = serialized_body.validated_data['file_name']

            new_script_path = os.path.join('server-data', 'server-users', str(user_id), 'scripts', str(script_name))

            if os.path.isfile(new_script_path):
                os.remove(new_script_path)

            new_script = open(file=new_script_path, mode='wb')
            for line in file_obj.readlines():
                new_script.write(line)
            new_script.close()

            serialized_body.create(serialized_body.validated_data)
            return ErrorResponse.make(status=status.HTTP_204_NO_CONTENT)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)


class ProjectList(generics.CreateAPIView, generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def post(self, request, *args, **kwargs):
        response = generics.CreateAPIView.post(self, request, args, kwargs)
        return ObjectResponse.make(response=response)

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

        path = os.path.join('server-data', 'server-projects', kwargs['id'])
        jobs = Job.objects.filter(project_id=kwargs['id'])

        for j in jobs:
            if j.finish_time is None:
                app.control.revoke(j.process_name, terminate=True)
        shutil.rmtree(path)

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
        path = os.path.join('server-data', 'server-projects', str(project_id))

        input_file = os.path.join(path, 'input.txt')
        generated_dat = os.path.join(path, 'generated.dat')
        generated_top = os.path.join(path, 'generated.top')
        if os.path.isdir(path):
            if os.path.isfile(input_file) and os.path.isfile(generated_dat) and os.path.isfile(generated_top):
                execute_sim.delay(job.id, job.project_id, path)
                return ExecutionResponse.make()
        else:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/checkstatus
@api_view(['POST'])
def check_status(request):
    serialized_body = CheckStatusSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        path = os.path.join('server-data', 'server-projects', str(project_id))
        running = True

        if serialized_body.fetched_job.finish_time is not None:
            running = False

        stdout_file = os.path.join(path, 'stdout.log')
        if os.path.isfile(stdout_file):
            with open(stdout_file, 'r') as log:
                stdout_string = log.read()
        else:
            stdout_string = ''

        log_file = os.path.join(path, 'log.dat')
        if os.path.isfile(log_file):
            with open(log_file, 'r') as logdatfile:
                log_string = logdatfile.read()
        else:
            log_string = ''

        response_data = {'running': running, 'log': log_string, 'stdout': stdout_string}
        return ObjectResponse.make(response_data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/file/visual
@api_view(['GET'])
def get_visual(request):
    serialized_body = VisualizationSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        project_path = os.path.join('server-data', 'server-projects', str(project_id))

        trajectory_file = os.path.join(project_path, 'trajectory.dat')
        if os.path.isfile(trajectory_file):
            file_string = get_pdb_file.delay(project_id)
            response_data = {'file_string': file_string, 'project_id': project_id}
            return ObjectResponse.make(obj=response_data)
        else:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/applysettings
@api_view(['POST'])
def set_project_settings(request):
    serialized_body = ProjectSettingsSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        box_size = serialized_body.validated_data['box_size']

        generated_files_status = generate_dat_top(project_id, box_size)
        input_file_status = generate_input_file(project_id, serialized_body.validated_data)
        if input_file_status == MISSING_PROJECT_FILES or generated_files_status == MISSING_PROJECT_FILES:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)

        return DefaultResponse.make(status.HTTP_201_CREATED)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/getsettings
@api_view(['GET'])
def get_project_settings(request):
    serialized_body = ProjectSettingsSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']

        input_data = get_input_file_as_serializer_data(project_id)
        if input_data == MISSING_PROJECT_FILES:
            return ErrorResponse.make(status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)

        return ObjectResponse.make(obj=input_data)
    else:
        return ErrorResponse.make(serialized_body.errors)


# /api/file/getprojectfile
@api_view(['GET'])
def get_project_file(request):
    serialized_body = FileSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        file_name = serialized_body.validated_data['file_name']
        file_path = os.path.join('server-data', 'server-projects', str(project_id), str(file_name))
        return get_file_string(file_path)
    else:
        return ErrorResponse.make(serialized_body.errors)


# /api/trajectory
@api_view(['GET'])
def fetch_traj(request):
    serialized_body = GetPDBSerializer(data=request.query_params)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        path = os.path.join('server-data', 'server-projects', str(project_id))

        if serialized_body.fetched_job.finish_time is None:
            trajectory_file = os.path.join(path, 'trajectory.dat')
            topology_file = os.path.join(path, 'generated.top')
            if os.path.isfile(trajectory_file) and os.path.isfile(topology_file):
                generate_sim_files(path)
            else:
                return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with open(os.path.join(path, 'sim', 'simulation.zip'), 'rb') as archive_file:
            response = HttpResponse(archive_file, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="simulation.zip"'
            archive_file.close()
        return response

    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/file/download
@api_view(['GET'])
def download_project_file(request, path):
    # assumes path is a path in "server-data/server-projects/{project_id}"
    serialized_body = ProjectExistenceSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        file_path = os.path.join('server-data', 'server-projects', str(project_id), path)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type="application/file")
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                file.close()
            return response
        else:
            return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR, message=MISSING_PROJECT_FILES)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/script/getscriptlist
@api_view(['GET'])
def get_script_list(request):
    # gets all the usuable scripts
    path = os.path.join(os.getcwd(), 'oxDNA', 'UTILS')

    dir_list = os.listdir(path)
    for item in list(dir_list):
        if item[-3:] != '.py':
            dir_list.remove(item)

    response_data = {'scripts': dir_list}
    return ObjectResponse.make(obj=response_data)


# /api/script/getcustomlist
@api_view(['GET'])
def get_custom_script_list(request):
    # assumes "server-data/server-projects/{project_id}/analysis" is the CWD for script execution
    serialized_body = UserScriptSerializer(data=request.data)
    if serialized_body.is_valid():
        user_id = serialized_body.validated_data['user_id']
        path_to_scripts = os.path.join('server-users', str(user_id), 'scripts')
        path = os.path(os.getcwd(), 'server-data', path_to_scripts)
        dir_list = os.listdir(path)

        dir_list_len = len(dir_list)
        path_from_analysis = os.path.join('..', '..', '..', path_to_scripts)
        for i in range(0, dir_list_len):
            dir_list[i] = os.path.join(path_from_analysis, dir_list[i])

        response_data = {'custom_scripts': dir_list}
        return ObjectResponse.make(obj=response_data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/script/getinputlist
@api_view(['GET'])
def get_input_list(request):
    # assumes "server-data/server-projects/{project_id}/analysis" is the CWD for script execution
    # names input variable files as ../{path_in_project_id}/{file_name}
    serialized_body = ProjectExistenceSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        path = os.path(os.getcwd(), 'server-data', 'server-projects', str(project_id))
        dir_list = []
        for (dir_path, dir_names, file_names) in os.walk(path):
            if 'analysis' in dir_path:  # analysis output files folder
                continue
            # path_from_analysis = "../{path_in_project_id}" or simply ".."
            path_from_analysis = dir_path.replace(path, '')
            path_from_analysis = '..' + path_from_analysis
            # ../{path_in_project_id}/{file_name}
            file_names_len = len(file_names)
            for i in range(0, file_names_len):
                file_names[i] = os.path.join(path_from_analysis, file_names[i])
            # concat file_names
            dir_list.extend(file_names)

        response_data = {'inputs': dir_list}
        return ObjectResponse.make(obj=response_data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# /api/script/getoutputlist
@api_view(['GET'])
def get_output_list(request):
    # to download from project folder "analysis/{output_file}"
    serialized_body = ProjectExistenceSerializer(data=request.data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        path = os.path(os.getcwd(), 'server-data', 'server-projects', str(project_id), 'analysis')

        dir_list = os.listdir(path)
        dir_list_len = len(dir_list)
        for i in range(0, dir_list_len):
            dir_list[i] = os.path.join('analysis', dir_list[i])

        response_data = {'outputs': dir_list}
        return ObjectResponse.make(obj=response_data)
    else:
        return ErrorResponse.make(errors=serialized_body.errors)
