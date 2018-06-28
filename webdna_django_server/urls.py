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
    url(r'^api/login/', views.login),
    url(r'^api/register', views.register),
    url(r'^api/users/', views.UserView.as_view()),

    url(r'^api/projects/$', views.ProjectList.as_view()),
    url(r'^api/projects/?(?P<id>[^/]+)/$', views.ProjectView.as_view()),
    url(r'^api/projects/zipdownload', views.project_zip),

    url(r'^api/execute', views.execute),
    url(r'^api/terminate', views.stop_execution),
    url(r'^api/checkstatus', views.check_status),
    url(r'^api/checkrunning', views.check_running),
    url(r'^api/applysettings', views.set_project_settings),
    url(r'^api/getsettings', views.get_project_settings),
    url(r'^api/trajectory', views.fetch_traj),

    url(r'^api/file/upload', views.FileUploadView.as_view()),
    url(r'^api/file/getprojectfile', views.get_project_file),

    url(r'^api/scripts/$', views.ScriptList.as_view()),
    url(r'^api/scripts/upload', views.ScriptUploadView.as_view()),
    url(r'^api/scripts/userlog', views.get_user_log),
    url(r'^api/scripts/getscriptchain', views.fetch_script_chain),
    url(r'^api/scripts/setscriptchain', views.set_scriptchain),
    url(r'^api/scripts/runanalysis', views.run_analysis_scripts),
    url(r'^api/scripts/delete', views.delete_script),
]

url_patterns = format_suffix_patterns(urlpatterns)