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
from rest_framework.urlpatterns import format_suffix_patterns
from webdna import views

urlpatterns = [
    url(r'^api/users/login/', views.login),
    url(r'^api/users/register', views.register),
    url(r'^api/users/', views.UserView.as_view()),

    url(r'^api/projects/$', views.ProjectList.as_view()),
    url(r'^api/projects/?(?P<id>[^/]+)/$', views.ProjectView.as_view()),

    url(r'^api/projects/simulation/execute', views.execute),
    url(r'^api/projects/simulation/terminate', views.stop_execution),
    url(r'^api/projects/current-output', views.check_output),
    url(r'^api/projects/running-status', views.check_running),
    url(r'^api/projects/settings/apply', views.set_project_settings),
    url(r'^api/projects/settings/retrieve', views.get_project_settings),
    url(r'^api/projects/trajectory', views.fetch_traj),

    url(r'^api/projects/files/upload', views.FileUploadView.as_view()),
    url(r'^api/projects/files/retrieve', views.get_project_file),
    url(r'^api/projects/files/zip', views.project_zip),

    url(r'^api/scripts/$', views.ScriptList.as_view()),
    url(r'^api/scripts/upload', views.ScriptUploadView.as_view()),
    url(r'^api/scripts/userlog', views.get_user_log),
    url(r'^api/scripts/scriptchain/retrieve', views.fetch_script_chain),
    url(r'^api/scripts/scriptchain/apply', views.set_scriptchain),
    url(r'^api/scripts/execute-analysis', views.run_analysis_scripts),
    url(r'^api/scripts/delete', views.delete_script)
]

url_patterns = format_suffix_patterns(urlpatterns)