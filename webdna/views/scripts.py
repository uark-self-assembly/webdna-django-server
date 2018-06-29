from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

import webdna.tasks as tasks
import webdna.util.server as server
from webdna.defaults import ProjectFile, AnalysisFile
from ..responses import *
from ..serializers import *


# URL: /api/scripts/upload
# Data: in request body
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


# URL: /api/scripts
# Data: None
class ScriptList(generics.CreateAPIView, generics.ListAPIView):
    queryset = Script.objects.all()
    serializer_class = ScriptSerializer

    def post(self, request, *args, **kwargs):
        pass

    def get(self, request, *args, **kwargs):
        response = generics.ListAPIView.get(self, request, args, kwargs)
        return ObjectResponse.make(response=response)


# URL: /api/scripts/userlog?project_id={project id}
# Data: in URL
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


# URL: /api/scripts/scriptchain/apply
# Data: in request body
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


# URL: /api/scripts/execute-analysis
# Data: in request body
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


# URL: /api/scripts/delete?script_id={script id}
# Data: in URL
@api_view(['DELETE'])
def delete_script(request):
    serialized_body = ScriptDeleteSerializer(data=request.query_params)
    if serialized_body.is_valid():
        serialized_body.fetched_script.delete()
        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/scripts/scriptchain/retrieve?project_id={project_id}
# Data: in URL
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