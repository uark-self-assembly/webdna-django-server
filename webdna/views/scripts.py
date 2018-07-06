from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser

import webdna.tasks as tasks
from webdna.defaults import ProjectFile, AnalysisFile
from ..responses import *
from ..serializers import *


# URL: /api/users/<uuid:user_id>/scripts/<uuid:id>
class ScriptView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'id'
    queryset = Script.objects.all()
    serializer_class = ScriptSerializer

    def get(self, request, *args, **kwargs):
        response = generics.RetrieveUpdateDestroyAPIView.get(self, request, args, kwargs)
        return ObjectResponse.make(response=response)

    def delete(self, request, *args, **kwargs):
        delete_data = {
            'script_id': kwargs['id']
        }
        serialized_body = ScriptDeleteSerializer(data=delete_data)
        if serialized_body.is_valid():
            response = generics.RetrieveUpdateDestroyAPIView.delete(self, request, args, kwargs)
            os.remove(server.get_user_script(user_id=kwargs['user_id'],
                                             script_file_name=serialized_body.fetched_script.file_name))
            return ObjectResponse.make(response=response)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/users/<uuid:user_id>/scripts/
class ScriptList(generics.CreateAPIView, generics.ListAPIView):
    queryset = Script.objects.all()
    serializer_class = ScriptSerializer
    parser_classes = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        upload_data = {
            'file_name': request.data['file_name'],
            'user': str(kwargs['user_id']),
            'file': request.data['file'],
            'description': request.data['description']
        }

        serialized_body = ScriptUploadSerializer(data=upload_data)
        if serialized_body.is_valid():
            script = serialized_body.create(serialized_body.validated_data)
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

            serialized_script = ScriptSerializer(script)
            return ObjectResponse.make(serialized_script.data)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)

    def get(self, request, *args, **kwargs):
        response = generics.ListAPIView.get(self, request, args, kwargs)
        return ObjectResponse.make(response=response)


# URL: /api/projects/<uuid:project_id>/userlog
@api_view(['GET'])
def get_user_log(request, *args, **kwargs):
    log_data = {
        'project_id': kwargs['project_id']
    }

    serialized_body = UserOutputRequestSerializer(data=log_data)
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


# URL: /api/projects/<uuid:project_id>/execute-analysis
@api_view(['POST'])
def run_analysis_scripts(request, *args, **kwargs):
    analysis_data = {
        'project_id': kwargs['project_id']
    }
    serialized_body = RunAnalysisSerializer(data=analysis_data)
    if serialized_body.is_valid():
        project_id = serialized_body.validated_data['project_id']
        user_id = serialized_body.fetched_project.user_id

        tasks.execute_output_analysis.delay(project_id, user_id)
        return DefaultResponse.make()
    else:
        return ErrorResponse.make(errors=serialized_body.errors)


# URL: /api/projects/<uuid:project_id>/scriptchain/
class ScriptChainView(generics.RetrieveUpdateDestroyAPIView):

    def get(self, request, *args, **kwargs):
        request_data = {
            'project_id': kwargs['project_id']
        }
        serialized_body = ScriptChainRequestSerializer(data=request_data)
        if serialized_body.is_valid():
            project_id = str(serialized_body.project_id)
            script_chain_file_path = server.get_project_file(project_id, ProjectFile.SCRIPT_CHAIN)
            with open(script_chain_file_path, 'rb') as script_chain:
                response = script_chain.readlines()

            return ObjectResponse.make(obj=response)
        else:
            return ErrorResponse.make(errors=serialized_body.errors)

    def post(self, request, *args, **kwargs):
        request_data = {
             'project_id': kwargs['project_id']
        }
        serialized_body = ScriptChainSerializer(data=request_data)
        if serialized_body.is_valid():
            project_id = serialized_body.validated_data['project_id']
            script_chain_file_path = server.get_project_file(project_id, ProjectFile.SCRIPT_CHAIN)
            script_list = serialized_body.validated_data['script_list']

            with open(script_chain_file_path, 'w') as script_chain:
                script_chain.write(script_list)

            return DefaultResponse.make()
        else:
            return ErrorResponse.make(errors=serialized_body.errors)
