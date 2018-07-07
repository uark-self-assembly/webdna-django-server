"""webdna_django_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from webdna.views import projects, scripts, users
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

urlpatterns = [

    # Navigate here to get JSON token
    # /token-auth
    url(r'^api/token-auth/', obtain_jwt_token),
    url(r'^api/token-refresh', refresh_jwt_token),
    # /users
    path('api/users/', users.UserView.as_view()),
    path('api/users/login/', users.LoginView.as_view()),
    path('api/users/register/', users.RegistrationView.as_view()),
    path('api/users/<uuid:user_id>/scripts/', scripts.ScriptList.as_view()),
    path('api/users/<uuid:user_id>/scripts/<uuid:id>/', scripts.ScriptView.as_view()),

    # /projects
    path('api/projects/', projects.ProjectList.as_view()),
    path('api/projects/<uuid:id>/', projects.ProjectView.as_view()),

    # /projects/{id}
    path('api/projects/<uuid:project_id>/current-output/', projects.get_current_output),
    path('api/projects/<uuid:project_id>/settings/', projects.SettingsView.as_view()),
    path('api/projects/<uuid:project_id>/generate-visualization/', projects.generate_visualization),
    path('api/projects/<uuid:project_id>/duplicate/', projects.duplicate_project),
    path('api/projects/<uuid:project_id>/execute-analysis/', scripts.AnalysisExecutionView.as_view()),

    # /projects/{id}/simulation
    path('api/projects/<uuid:project_id>/simulation/execute/', projects.execute),
    path('api/projects/<uuid:project_id>/simulation/terminate/', projects.terminate),
    path('api/projects/<uuid:project_id>/userlog/', scripts.UserLogView.as_view()),
    path('api/projects/<uuid:project_id>/scriptchain/', scripts.ScriptChainView.as_view()),

    # /projects/{id}/files
    path('api/projects/<uuid:project_id>/files/upload/', projects.FileUploadView.as_view()),
    path('api/projects/<uuid:project_id>/files/download/<str:file_type>/', projects.download_project_file),
    path('api/projects/<uuid:project_id>/files/zip/', projects.project_zip)
]

url_patterns = format_suffix_patterns(urlpatterns)
