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

        new_file_path = os.path.join('server-data', 'server-projects', project_id, file_name)

        if os.path.isfile(new_file_path):
            os.remove(new_file_path)

        new_file = open(file=new_file_path, mode='wb')
        for line in file_obj.readlines():
            new_file.write(line)

        new_file.close()
        return ErrorResponse.make(status=status.HTTP_204_NO_CONTENT)


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


# /api/getfile
@api_view(['GET'])
def get_energy(request):
    pass


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
                traj2pdb(path)
                traj2xtc(path)
                zip_traj(project_id, path)
            else:
                return ErrorResponse.make(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with open(os.path.join(path, str(project_id) + '.zip'), 'rb') as archive_file:
            response = HttpResponse(archive_file, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="'+str(project_id)+'.zip"'
            archive_file.close()
        return response

    else:
        return ErrorResponse.make(errors=serialized_body.errors)
