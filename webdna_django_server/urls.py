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
from webdna.views import projects, scripts, users

urlpatterns = [
    url(r'^api/users/login', users.login),
    url(r'^api/users/register', users.register),
    url(r'^api/users', users.UserView.as_view()),

    url(r'^api/projects/$', projects.ProjectList.as_view()),
    url(r'^api/projects/?(?P<id>[^/]+)/$', projects.ProjectView.as_view()),

    url(r'^api/projects/simulation/execute', projects.execute),
    url(r'^api/projects/simulation/terminate', projects.stop_execution),
    url(r'^api/projects/current-output', projects.check_output),
    url(r'^api/projects/running-status', projects.check_running),
    url(r'^api/projects/settings/apply', projects.set_project_settings),
    url(r'^api/projects/settings/retrieve', projects.get_project_settings),

    url(r'^api/projects/files/trajectory', projects.fetch_traj),
    url(r'^api/projects/files/upload', projects.FileUploadView.as_view()),
    url(r'^api/projects/files/retrieve', projects.get_project_file),
    url(r'^api/projects/files/zip', projects.project_zip),

    url(r'^api/scripts/$', scripts.ScriptList.as_view()),
    url(r'^api/scripts/upload', scripts.ScriptUploadView.as_view()),
    url(r'^api/scripts/userlog', scripts.get_user_log),
    url(r'^api/scripts/scriptchain/retrieve', scripts.fetch_script_chain),
    url(r'^api/scripts/scriptchain/apply', scripts.set_scriptchain),
    url(r'^api/scripts/execute-analysis', scripts.run_analysis_scripts),
    url(r'^api/scripts/delete', scripts.delete_script)
]

url_patterns = format_suffix_patterns(urlpatterns)